# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
import logging

from django.conf import settings  # noqa
from django.template.defaultfilters import filesizeformat  # noqa
from django.utils.text import normalize_newlines  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa
from django.utils.translation import ungettext_lazy  # noqa
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon.utils import fields
from horizon.utils import functions
from horizon.utils import validators
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.project.images_and_snapshots import utils


LOG = logging.getLogger(__name__)


class SelectProjectUserAction(workflows.Action):
    project_id = forms.ChoiceField(label=_("Project"))
    user_id = forms.ChoiceField(label=_("User"))

    def __init__(self, request, *args, **kwargs):
        super(SelectProjectUserAction, self).__init__(request, *args, **kwargs)
        # Set our project choices
        projects = [(tenant.id, tenant.name)
                    for tenant in request.user.authorized_tenants]
        self.fields['project_id'].choices = projects

        # Set our user options
        users = [(request.user.id, request.user.username)]
        self.fields['user_id'].choices = users

    class Meta:
        name = _("Project & User")
        # Unusable permission so this is always hidden. However, we
        # keep this step in the workflow for validation/verification purposes.
        permissions = ("!",)


class SelectProjectUser(workflows.Step):
    action_class = SelectProjectUserAction
    contributes = ("project_id", "user_id")


class SetInstanceDetailsAction(workflows.Action):
    SOURCE_TYPE_CHOICES = (
        ('', _("--- Select source ---")),
        ("image_id", _("Boot from image.")),
        ("instance_snapshot_id", _("Boot from snapshot.")),
        ("volume_id", _("Boot from volume.")),
        ("volume_image_id", _("Boot from image "
                                  "(creates a new volume).")),
        ("volume_snapshot_id", _("Boot from volume snapshot "
                                 "(creates a new volume).")),
    )

    availability_zone = forms.ChoiceField(label=_("Availability Zone"),
                                          required=False)

    name = forms.CharField(max_length=80, label=_("Instance Name"))

    flavor = forms.ChoiceField(label=_("Flavor"),
                               help_text=_("Size of image to launch."))

    count = forms.IntegerField(label=_("Instance Count"),
                               min_value=1,
                               initial=1,
                               help_text=_("Number of instances to launch."))

    source_type = forms.ChoiceField(label=_("Instance Boot Source"),
                                    required=True,
                                    choices=SOURCE_TYPE_CHOICES,
                                    help_text=_("Choose Your Boot Source "
                                                "Type."))

    instance_snapshot_id = forms.ChoiceField(label=_("Instance Snapshot"),
                                             required=False)

    volume_id = forms.ChoiceField(label=_("Volume"), required=False)

    volume_snapshot_id = forms.ChoiceField(label=_("Volume Snapshot"),
                                               required=False)

    image_id = forms.ChoiceField(
        label=_("Image Name"),
        required=False,
        widget=fields.SelectWidget(
            data_attrs=('volume_size',),
            transform=lambda x: ("%s (%s)" % (x.name,
                                              filesizeformat(x.bytes)))))

    volume_size = forms.CharField(label=_("Device size (GB)"),
                                  required=False,
                                  help_text=_("Volume size in gigabytes "
                                              "(integer value)."))

    device_name = forms.CharField(label=_("Device Name"),
                                  required=False,
                                  initial="vda",
                                  help_text=_("Volume mount point (e.g. 'vda' "
                                              "mounts at '/dev/vda')."))

    delete_on_terminate = forms.BooleanField(label=_("Delete on Terminate"),
                                             initial=False,
                                             required=False,
                                             help_text=_("Delete volume on "
                                                         "instance terminate"))

    class Meta:
        name = _("Details")
        help_text_template = ("project/instances/"
                              "_launch_details_help.html")

    def __init__(self, request, context, *args, **kwargs):
        self._init_images_cache()
        super(SetInstanceDetailsAction, self).__init__(
            request, context, *args, **kwargs)

    def clean(self):
        cleaned_data = super(SetInstanceDetailsAction, self).clean()

        count = cleaned_data.get('count', 1)
        # Prevent launching more instances than the quota allows
        usages = quotas.tenant_quota_usages(self.request)
        available_count = usages['instances']['available']
        if available_count < count:
            error_message = ungettext_lazy('The requested instance '
                                           'cannot be launched as you only '
                                           'have %(avail)i of your quota '
                                           'available. ',
                                           'The requested %(req)i instances '
                                           'cannot be launched as you only '
                                           'have %(avail)i of your quota '
                                           'available.',
                                           count)
            params = {'req': count,
                      'avail': available_count}
            raise forms.ValidationError(error_message % params)

        # Validate our instance source.
        source_type = self.data.get('source_type', None)

        if source_type == 'image_id':
            if not cleaned_data.get('image_id'):
                msg = _("You must select an image.")
                self._errors['image_id'] = self.error_class([msg])

        elif source_type == 'instance_snapshot_id':
            if not cleaned_data['instance_snapshot_id']:
                msg = _("You must select a snapshot.")
                self._errors['instance_snapshot_id'] = self.error_class([msg])

        elif source_type == 'volume_id':
            if not cleaned_data.get('volume_id'):
                msg = _("You must select a volume.")
                self._errors['volume_id'] = self.error_class([msg])
            # Prevent launching multiple instances with the same volume.
            # TODO(gabriel): is it safe to launch multiple instances with
            # a snapshot since it should be cloned to new volumes?
            if count > 1:
                msg = _('Launching multiple instances is only supported for '
                        'images and instance snapshots.')
                raise forms.ValidationError(msg)

        elif source_type == 'volume_image_id':
            if not cleaned_data['image_id']:
                msg = _("You must select an image.")
                self._errors['image_id'] = self.error_class([msg])
            if not self.data.get('volume_size', None):
                msg = _("You must set volume size")
                self._errors['volume_size'] = self.error_class([msg])
            if not cleaned_data.get('device_name'):
                msg = _("You must set device name")
                self._errors['device_name'] = self.error_class([msg])

        elif source_type == 'volume_snapshot_id':
            if not cleaned_data.get('volume_snapshot_id'):
                msg = _("You must select a snapshot.")
                self._errors['volume_snapshot_id'] = self.error_class([msg])
            if not cleaned_data.get('device_name'):
                msg = _("You must set device name")
                self._errors['device_name'] = self.error_class([msg])

        return cleaned_data

    def populate_flavor_choices(self, request, context):
        """By default, returns the available flavors, sorted by RAM
        usage (ascending).
        Override these behaviours with a CREATE_INSTANCE_FLAVOR_SORT dict
        in local_settings.py."""
        try:
            flavors = api.nova.flavor_list(request)
            flavor_sort = getattr(settings, 'CREATE_INSTANCE_FLAVOR_SORT', {})
            rev = flavor_sort.get('reverse', False)
            key = flavor_sort.get('key', lambda flavor: flavor.ram)

            flavor_list = [(flavor.id, "%s" % flavor.name)
                           for flavor in sorted(flavors, key=key, reverse=rev)]
        except Exception:
            flavor_list = []
            exceptions.handle(request,
                              _('Unable to retrieve instance flavors.'))
        return flavor_list

    def populate_availability_zone_choices(self, request, context):
        try:
            zones = api.nova.availability_zone_list(request)
        except Exception:
            zones = []
            exceptions.handle(request,
                              _('Unable to retrieve availability zones.'))

        zone_list = [(zone.zoneName, zone.zoneName)
                      for zone in zones if zone.zoneState['available']]
        zone_list.sort()
        if not zone_list:
            zone_list.insert(0, ("", _("No availability zones found.")))
        elif len(zone_list) > 1:
            zone_list.insert(0, ("", _("Any Availability Zone")))
        return zone_list

    def get_help_text(self):
        extra = {}
        try:
            extra['usages'] = api.nova.tenant_absolute_limits(self.request)
            extra['usages_json'] = json.dumps(extra['usages'])
            flavors = json.dumps([f._info for f in
                                  api.nova.flavor_list(self.request)])
            extra['flavors'] = flavors
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve quota information."))
        return super(SetInstanceDetailsAction, self).get_help_text(extra)

    def _init_images_cache(self):
        if not hasattr(self, '_images_cache'):
            self._images_cache = {}

    def _get_volume_display_name(self, volume):
        if hasattr(volume, "volume_id"):
            vol_type = "snap"
            visible_label = _("Snapshot")
        else:
            vol_type = "vol"
            visible_label = _("Volume")
        return (("%s:%s" % (volume.id, vol_type)),
                (_("%(name)s - %(size)s GB (%(label)s)") %
                 {'name': volume.display_name or volume.id,
                  'size': volume.size,
                  'label': visible_label}))

    def populate_image_id_choices(self, request, context):
        choices = []
        images = utils.get_available_images(request,
                                            context.get('project_id'),
                                            self._images_cache)
        for image in images:
            image.bytes = image.size
            image.volume_size = functions.bytes_to_gigabytes(image.bytes)
            choices.append((image.id, image))
        if choices:
            choices.insert(0, ("", _("Select Image")))
        else:
            choices.insert(0, ("", _("No images available")))
        return choices

    def populate_instance_snapshot_id_choices(self, request, context):
        images = utils.get_available_images(request,
                                            context.get('project_id'),
                                            self._images_cache)
        choices = [(image.id, image.name)
                   for image in images
                   if image.properties.get("image_type", '') == "snapshot"]
        if choices:
            choices.insert(0, ("", _("Select Instance Snapshot")))
        else:
            choices.insert(0, ("", _("No snapshots available.")))
        return choices

    def populate_volume_id_choices(self, request, context):
        try:
            volumes = [self._get_volume_display_name(v)
                       for v in cinder.volume_list(self.request)
                       if v.status == api.cinder.VOLUME_STATE_AVAILABLE]
        except Exception:
            volumes = []
            exceptions.handle(self.request,
                              _('Unable to retrieve list of volumes.'))
        if volumes:
            volumes.insert(0, ("", _("Select Volume")))
        else:
            volumes.insert(0, ("", _("No volumes available.")))
        return volumes

    def populate_volume_snapshot_id_choices(self, request, context):
        try:
            snapshots = cinder.volume_snapshot_list(self.request)
            snapshots = [self._get_volume_display_name(s) for s in snapshots
                         if s.status == api.cinder.VOLUME_STATE_AVAILABLE]
        except Exception:
            snapshots = []
            exceptions.handle(self.request,
                              _('Unable to retrieve list of volume '
                                'snapshots.'))
        if snapshots:
            snapshots.insert(0, ("", _("Select Volume Snapshot")))
        else:
            snapshots.insert(0, ("", _("No volume snapshots available.")))
        return snapshots


class SetInstanceDetails(workflows.Step):
    action_class = SetInstanceDetailsAction
    depends_on = ("project_id", "user_id")
    contributes = ("source_type", "source_id",
                   "availability_zone", "name", "count", "flavor",
                   "device_name",  # Can be None for an image.
                   "delete_on_terminate")

    def prepare_action_context(self, request, context):
        if 'source_type' in context and 'source_id' in context:
            context[context['source_type']] = context['source_id']
        return context

    def contribute(self, data, context):
        context = super(SetInstanceDetails, self).contribute(data, context)
        # Allow setting the source dynamically.
        if ("source_type" in context and "source_id" in context
                and context["source_type"] not in context):
            context[context["source_type"]] = context["source_id"]

        # Translate form input to context for source values.
        if "source_type" in data:
            if data["source_type"] in ["image_id", "volume_image_id"]:
                context["source_id"] = data.get("image_id", None)
            else:
                context["source_id"] = data.get(data["source_type"], None)

        if "volume_size" in data:
            context["volume_size"] = data["volume_size"]

        return context


KEYPAIR_IMPORT_URL = "horizon:project:access_and_security:keypairs:import"


class SetAccessControlsAction(workflows.Action):
    keypair = forms.DynamicChoiceField(label=_("Keypair"),
                                       required=False,
                                       help_text=_("Which keypair to use for "
                                                   "authentication."),
                                       add_item_link=KEYPAIR_IMPORT_URL)
    admin_pass = forms.RegexField(
        label=_("Admin Pass"),
        required=False,
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    confirm_admin_pass = forms.CharField(
        label=_("Confirm Admin Pass"),
        required=False,
        widget=forms.PasswordInput(render_value=False))
    groups = forms.MultipleChoiceField(label=_("Security Groups"),
                                       required=True,
                                       initial=["default"],
                                       widget=forms.CheckboxSelectMultiple(),
                                       help_text=_("Launch instance in these "
                                                   "security groups."))

    class Meta:
        name = _("Access & Security")
        help_text = _("Control access to your instance via keypairs, "
                      "security groups, and other mechanisms.")

    def populate_keypair_choices(self, request, context):
        try:
            keypairs = api.nova.keypair_list(request)
            keypair_list = [(kp.name, kp.name) for kp in keypairs]
        except Exception:
            keypair_list = []
            exceptions.handle(request,
                              _('Unable to retrieve keypairs.'))
        if keypair_list:
            if len(keypair_list) == 1:
                self.fields['keypair'].initial = keypair_list[0][0]
            keypair_list.insert(0, ("", _("Select a keypair")))
        else:
            keypair_list = (("", _("No keypairs available.")),)
        return keypair_list

    def populate_groups_choices(self, request, context):
        try:
            groups = api.network.security_group_list(request)
            security_group_list = [(sg.name, sg.name) for sg in groups]
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve list of security groups'))
            security_group_list = []
        return security_group_list

    def clean(self):
        '''Check to make sure password fields match.'''
        cleaned_data = super(SetAccessControlsAction, self).clean()
        if 'admin_pass' in cleaned_data:
            if cleaned_data['admin_pass'] != cleaned_data.get(
                    'confirm_admin_pass', None):
                raise forms.ValidationError(_('Passwords do not match.'))
        return cleaned_data


class SetAccessControls(workflows.Step):
    action_class = SetAccessControlsAction
    depends_on = ("project_id", "user_id")
    contributes = ("keypair_id", "security_group_ids",
            "admin_pass", "confirm_admin_pass")

    def contribute(self, data, context):
        if data:
            post = self.workflow.request.POST
            context['security_group_ids'] = post.getlist("groups")
            context['keypair_id'] = data.get("keypair", "")
            context['admin_pass'] = data.get("admin_pass", "")
            context['confirm_admin_pass'] = data.get("confirm_admin_pass", "")
        return context


class CustomizeAction(workflows.Action):
    customization_script = forms.CharField(widget=forms.Textarea,
                                           label=_("Customization Script"),
                                           required=False,
                                           help_text=_("A script or set of "
                                                       "commands to be "
                                                       "executed after the "
                                                       "instance has been "
                                                       "built (max 16kb)."))

    class Meta:
        name = _("Post-Creation")
        help_text_template = ("project/instances/"
                              "_launch_customize_help.html")


class PostCreationStep(workflows.Step):
    action_class = CustomizeAction
    contributes = ("customization_script",)


class SetNetworkAction(workflows.Action):
    network = forms.MultipleChoiceField(label=_("Networks"),
                                        required=True,
                                        widget=forms.CheckboxSelectMultiple(),
                                        error_messages={
                                            'required': _(
                                                "At least one network must"
                                                " be specified.")},
                                        help_text=_("Launch instance with"
                                                    " these networks"))
    if api.neutron.is_port_profiles_supported():
        profile = forms.ChoiceField(label=_("Policy Profiles"),
                                    required=False,
                                    help_text=_("Launch instance with "
                                                "this policy profile"))

    class Meta:
        name = _("Networking")
        permissions = ('openstack.services.network',)
        help_text = _("Select networks for your instance.")

    def populate_network_choices(self, request, context):
        try:
            tenant_id = self.request.user.tenant_id
            networks = api.neutron.network_list_for_tenant(request, tenant_id)
            for n in networks:
                n.set_id_as_name_if_empty()
            network_list = [(network.id, network.name) for network in networks]
        except Exception:
            network_list = []
            exceptions.handle(request,
                              _('Unable to retrieve networks.'))
        return network_list

    def populate_profile_choices(self, request, context):
        try:
            profiles = api.neutron.profile_list(request, 'policy')
            profile_list = [(profile.id, profile.name) for profile in profiles]
        except Exception:
            profile_list = []
            exceptions.handle(request, _("Unable to retrieve profiles."))
        return profile_list


class SetNetwork(workflows.Step):
    action_class = SetNetworkAction
    # Disabling the template drag/drop only in the case port profiles
    # are used till the issue with the drag/drop affecting the
    # profile_id detection is fixed.
    if api.neutron.is_port_profiles_supported():
        contributes = ("network_id", "profile_id",)
    else:
        template_name = "project/instances/_update_networks.html"
        contributes = ("network_id",)

    def contribute(self, data, context):
        if data:
            networks = self.workflow.request.POST.getlist("network")
            # If no networks are explicitly specified, network list
            # contains an empty string, so remove it.
            networks = [n for n in networks if n != '']
            if networks:
                context['network_id'] = networks

            if api.neutron.is_port_profiles_supported():
                context['profile_id'] = data.get('profile', None)
        return context


class LaunchInstance(workflows.Workflow):
    slug = "launch_instance"
    name = _("Launch Instance")
    finalize_button_name = _("Launch")
    success_message = _('Launched %(count)s named "%(name)s".')
    failure_message = _('Unable to launch %(count)s named "%(name)s".')
    success_url = "horizon:project:instances:index"
    default_steps = (SelectProjectUser,
                     SetInstanceDetails,
                     SetAccessControls,
                     SetNetwork,
                     PostCreationStep)

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown instance')
        count = self.context.get('count', 1)
        if int(count) > 1:
            return message % {"count": _("%s instances") % count,
                              "name": name}
        else:
            return message % {"count": _("instance"), "name": name}

    @sensitive_variables('context')
    def handle(self, request, context):
        custom_script = context.get('customization_script', '')

        dev_mapping_1 = None
        dev_mapping_2 = None

        image_id = ''

        # Determine volume mapping options
        source_type = context.get('source_type', None)
        if source_type in ['image_id', 'instance_snapshot_id']:
            image_id = context['source_id']
        elif source_type in ['volume_id', 'volume_snapshot_id']:
            dev_mapping_1 = {context['device_name']: '%s::%s' %
                                                     (context['source_id'],
                           int(bool(context['delete_on_terminate'])))}
        elif source_type == 'volume_image_id':
            dev_mapping_2 = [
                {'device_name': str(context['device_name']),
                 'source_type': 'image',
                 'destination_type': 'volume',
                 'delete_on_termination':
                     int(bool(context['delete_on_terminate'])),
                 'uuid': context['source_id'],
                 'boot_index': '0',
                 'volume_size': context['volume_size']
                 }
            ]

        netids = context.get('network_id', None)
        if netids:
            nics = [{"net-id": netid, "v4-fixed-ip": ""}
                    for netid in netids]
        else:
            nics = None

        avail_zone = context.get('availability_zone', None)

        # Create port with Network Name and Port Profile
        # for the use with the plugin supporting port profiles.
        # neutron port-create <Network name> --n1kv:profile <Port Profile ID>
        # for net_id in context['network_id']:
        ## HACK for now use first network
        if api.neutron.is_port_profiles_supported():
            net_id = context['network_id'][0]
            LOG.debug("Horizon->Create Port with %(netid)s %(profile_id)s",
                      {'netid': net_id, 'profile_id': context['profile_id']})
            try:
                port = api.neutron.port_create(request, net_id,
                                               policy_profile_id=
                                               context['profile_id'])
            except Exception:
                msg = (_('Port not created for profile-id (%s).') %
                       context['profile_id'])
                exceptions.handle(request, msg)
            if port and port.id:
                nics = [{"port-id": port.id}]

        try:
            api.nova.server_create(request,
                                   context['name'],
                                   image_id,
                                   context['flavor'],
                                   context['keypair_id'],
                                   normalize_newlines(custom_script),
                                   context['security_group_ids'],
                                   block_device_mapping=dev_mapping_1,
                                   block_device_mapping_v2=dev_mapping_2,
                                   nics=nics,
                                   availability_zone=avail_zone,
                                   instance_count=int(context['count']),
                                   admin_pass=context['admin_pass'])
            return True
        except Exception:
            exceptions.handle(request)
            return False
