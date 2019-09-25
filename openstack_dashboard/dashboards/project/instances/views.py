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

"""
Views for managing instances.
"""
from collections import OrderedDict
import logging

from django.conf import settings
from django import http
from django import shortcuts
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.utils import filters
from openstack_dashboard.utils import settings as setting_utils

from openstack_dashboard.dashboards.project.instances \
    import console as project_console
from openstack_dashboard.dashboards.project.instances \
    import forms as project_forms
from openstack_dashboard.dashboards.project.instances \
    import tables as project_tables
from openstack_dashboard.dashboards.project.instances \
    import tabs as project_tabs
from openstack_dashboard.dashboards.project.instances \
    import workflows as project_workflows
from openstack_dashboard.dashboards.project.networks.ports \
    import views as port_views
from openstack_dashboard.utils import futurist_utils
from openstack_dashboard.views import get_url_with_pagination

LOG = logging.getLogger(__name__)


class IndexView(tables.PagedTableMixin, tables.DataTableView):
    table_class = project_tables.InstancesTable
    page_title = _("Instances")

    def has_prev_data(self, table):
        return getattr(self, "_prev", False)

    def has_more_data(self, table):
        return self._more

    def _get_flavors(self):
        # Gather our flavors to correlate our instances to them
        try:
            flavors = api.nova.flavor_list(self.request)
            return dict((str(flavor.id), flavor) for flavor in flavors)
        except Exception:
            exceptions.handle(self.request, ignore=True)
            return {}

    def _get_images(self):
        # Gather our images to correlate our instances to them
        try:
            # Community images have to be retrieved separately and merged,
            # because their visibility has to be explicitly defined in the
            # API call and the Glance API currently does not support filtering
            # by multiple values in the visibility field.
            # TODO(gabriel): Handle pagination.
            images = api.glance.image_list_detailed(self.request)[0]
            community_images = api.glance.image_list_detailed(
                self.request, filters={'visibility': 'community'})[0]
            image_map = {
                image.id: image for image in images
            }
            # Images have to be filtered by their uuids; some users
            # have default access to certain community images.
            for image in community_images:
                image_map.setdefault(image.id, image)
            return image_map
        except Exception:
            exceptions.handle(self.request, ignore=True)
            return {}

    def _get_instances(self, search_opts, sort_dir):
        try:
            instances, self._more, self._prev = api.nova.server_list_paged(
                self.request,
                search_opts=search_opts,
                sort_dir=sort_dir)
        except Exception:
            self._more = self._prev = False
            instances = []
            exceptions.handle(self.request,
                              _('Unable to retrieve instances.'))

        # In case of exception when calling nova.server_list
        # don't call api.network
        if not instances:
            return []

        # TODO(future): Explore more efficient logic to sync IP address
        # and drop the setting OPENSTACK_INSTANCE_RETRIEVE_IP_ADDRESSES.
        # The situation servers_update_addresses() is needed is only
        # when IP address of a server is updated via neutron API and
        # nova network info cache is not synced. Precisely there is no
        # need to check IP addresses of all servers. It is sufficient to
        # fetch IP address information for servers recently updated.
        if not settings.OPENSTACK_INSTANCE_RETRIEVE_IP_ADDRESSES:
            return instances
        try:
            api.network.servers_update_addresses(self.request, instances)
        except Exception:
            exceptions.handle(
                self.request,
                message=_('Unable to retrieve IP addresses from Neutron.'),
                ignore=True)

        return instances

    def _get_volumes(self):
        # Gather our volumes to get their image metadata for instance
        try:
            volumes = api.cinder.volume_list(self.request)
            return dict((str(volume.id), volume) for volume in volumes)
        except Exception:
            exceptions.handle(self.request, ignore=True)
            return {}

    def get_data(self):
        marker, sort_dir = self._get_marker()
        search_opts = self.get_filters({'marker': marker, 'paginate': True})

        image_dict, flavor_dict, volume_dict = \
            futurist_utils.call_functions_parallel(
                self._get_images, self._get_flavors, self._get_volumes
            )

        non_api_filter_info = (
            ('image_name', 'image', image_dict.values()),
            ('flavor_name', 'flavor', flavor_dict.values()),
        )
        if not process_non_api_filters(search_opts, non_api_filter_info):
            self._more = False
            return []

        instances = self._get_instances(search_opts, sort_dir)

        # Loop through instances to get flavor info.
        for instance in instances:
            self._populate_image_info(instance, image_dict, volume_dict)

            flavor_id = instance.flavor["id"]
            if flavor_id in flavor_dict:
                instance.full_flavor = flavor_dict[flavor_id]
            else:
                # If the flavor_id is not in flavor_dict,
                # put info in the log file.
                LOG.info('Unable to retrieve flavor "%s" for instance "%s".',
                         flavor_id, instance.id)

        return instances

    def _populate_image_info(self, instance, image_dict, volume_dict):
        if not hasattr(instance, 'image'):
            return
        # Instance from image returns dict
        if isinstance(instance.image, dict):
            image_id = instance.image.get('id')
            if image_id in image_dict:
                instance.image = image_dict[image_id]
            # In case image not found in image_dict, set name to empty
            # to avoid fallback API call to Glance in api/nova.py
            # until the call is deprecated in api itself
            else:
                instance.image['name'] = _("-")
        # Otherwise trying to get image from volume metadata
        else:
            instance_volumes = [
                attachment
                for volume in volume_dict.values()
                for attachment in volume.attachments
                if attachment['server_id'] == instance.id
            ]
            # While instance from volume is being created,
            # it does not have volumes
            if not instance_volumes:
                return
            # Sorting attached volumes by device name (eg '/dev/sda')
            instance_volumes.sort(key=lambda attach: attach['device'])
            # Getting volume object, which is as attached
            # as the first device
            boot_volume = volume_dict[instance_volumes[0]['id']]
            # There is a case where volume_image_metadata contains
            # only fields other than 'image_id' (See bug 1834747),
            # so we try to populate image information only when it is found.
            volume_metadata = getattr(boot_volume, "volume_image_metadata", {})
            image_id = volume_metadata.get('image_id')
            if image_id:
                try:
                    instance.image = image_dict[image_id]
                except KeyError:
                    # KeyError occurs when volume was created from image and
                    # then this image is deleted.
                    pass


def process_non_api_filters(search_opts, non_api_filter_info):
    """Process filters by non-API fields

    There are cases where it is useful to provide a filter field
    which does not exist in a resource in a backend service.
    For example, nova server list provides 'image' field with image ID
    but 'image name' is more useful for GUI users.
    This function replaces fake fields into corresponding real fields.

    The format of non_api_filter_info is a tuple/list of
    (fake_field, real_field, resources).

    This returns True if further lookup is required.
    It returns False if there are no matching resources,
    for example, if no corresponding real field exists.
    """
    for fake_field, real_field, resources in non_api_filter_info:
        if not _swap_filter(resources, search_opts, fake_field, real_field):
            return False
    return True


def _swap_filter(resources, search_opts, fake_field, real_field):
    if fake_field not in search_opts:
        return True
    filter_string = search_opts[fake_field]
    matched = [resource for resource in resources
               if resource.name.lower() == filter_string.lower()]
    if not matched:
        return False
    search_opts[real_field] = matched[0].id
    del search_opts[fake_field]
    return True


class LaunchInstanceView(workflows.WorkflowView):
    workflow_class = project_workflows.LaunchInstance

    def get_initial(self):
        initial = super(LaunchInstanceView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        initial['config_drive'] = setting_utils.get_dict_config(
            'LAUNCH_INSTANCE_DEFAULTS', 'config_drive')
        return initial


# TODO(stephenfin): Migrate to CBV
def console(request, instance_id):
    data = _('Unable to get log for instance "%s".') % instance_id
    tail = request.GET.get('length')
    if tail and not tail.isdigit():
        msg = _('Log length must be a nonnegative integer.')
        messages.warning(request, msg)
    else:
        try:
            data = api.nova.server_console_output(request,
                                                  instance_id,
                                                  tail_length=tail)
        except Exception:
            exceptions.handle(request, ignore=True)
    return http.HttpResponse(data.encode('utf-8'), content_type='text/plain')


# TODO(stephenfin): Migrate to CBV
def auto_console(request, instance_id):
    console_type = settings.CONSOLE_TYPE
    try:
        instance = api.nova.server_get(request, instance_id)
        console_url = project_console.get_console(request, console_type,
                                                  instance)[1]
        return shortcuts.redirect(console_url)
    except Exception:
        redirect = reverse("horizon:project:instances:index")
        msg = _('Unable to get console for instance "%s".') % instance_id
        exceptions.handle(request, msg, redirect=redirect)


# TODO(stephenfin): Migrate to CBV
def vnc(request, instance_id):
    try:
        instance = api.nova.server_get(request, instance_id)
        console_url = project_console.get_console(request, 'VNC', instance)[1]
        return shortcuts.redirect(console_url)
    except Exception:
        redirect = reverse("horizon:project:instances:index")
        msg = _('Unable to get VNC console for instance "%s".') % instance_id
        exceptions.handle(request, msg, redirect=redirect)


# TODO(stephenfin): Migrate to CBV
def mks(request, instance_id):
    try:
        instance = api.nova.server_get(request, instance_id)
        console_url = project_console.get_console(request, 'MKS', instance)[1]
        return shortcuts.redirect(console_url)
    except Exception:
        redirect = reverse("horizon:project:instances:index")
        msg = _('Unable to get MKS console for instance "%s".') % instance_id
        exceptions.handle(request, msg, redirect=redirect)


# TODO(stephenfin): Migrate to CBV
def spice(request, instance_id):
    try:
        instance = api.nova.server_get(request, instance_id)
        console_url = project_console.get_console(request, 'SPICE',
                                                  instance)[1]
        return shortcuts.redirect(console_url)
    except Exception:
        redirect = reverse("horizon:project:instances:index")
        msg = _('Unable to get SPICE console for instance "%s".') % instance_id
        exceptions.handle(request, msg, redirect=redirect)


# TODO(stephenfin): Migrate to CBV
def rdp(request, instance_id):
    try:
        instance = api.nova.server_get(request, instance_id)
        console_url = project_console.get_console(request, 'RDP', instance)[1]
        return shortcuts.redirect(console_url)
    except Exception:
        redirect = reverse("horizon:project:instances:index")
        msg = _('Unable to get RDP console for instance "%s".') % instance_id
        exceptions.handle(request, msg, redirect=redirect)


class SerialConsoleView(generic.TemplateView):
    template_name = 'serial_console.html'

    def get_context_data(self, **kwargs):
        context = super(SerialConsoleView, self).get_context_data(**kwargs)
        instance = None
        try:
            instance = api.nova.server_get(self.request,
                                           self.kwargs['instance_id'])
        except Exception:
            context["error_message"] = _(
                "Cannot find instance %s.") % self.kwargs['instance_id']
            # name is unknown, so leave it blank for the window title
            # in full-screen mode, so only the instance id is shown.
            context['page_title'] = self.kwargs['instance_id']
            return context
        context['page_title'] = "%s (%s)" % (instance.name, instance.id)
        try:
            console_url = project_console.get_console(self.request,
                                                      "SERIAL", instance)[1]
            context["console_url"] = console_url
            context["protocols"] = "['binary', 'base64']"
        except exceptions.NotAvailable:
            context["error_message"] = _(
                "Cannot get console for instance %s.") % self.kwargs[
                'instance_id']
        return context


class UpdateView(workflows.WorkflowView):
    workflow_class = project_workflows.UpdateInstance
    success_url = reverse_lazy("horizon:project:instances:index")

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context["instance_id"] = self.kwargs['instance_id']
        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        instance_id = self.kwargs['instance_id']
        try:
            return api.nova.server_get(self.request, instance_id)
        except Exception:
            redirect = reverse("horizon:project:instances:index")
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        initial = super(UpdateView, self).get_initial()
        instance = self.get_object()
        initial.update({'instance_id': self.kwargs['instance_id'],
                        'name': getattr(instance, 'name', ''),
                        'description': getattr(instance, 'description', ''),
                        'target_tenant_id': self.request.user.tenant_id})
        return initial


class RebuildView(forms.ModalFormView):
    form_class = project_forms.RebuildInstanceForm
    template_name = 'project/instances/rebuild.html'
    success_url = reverse_lazy('horizon:project:instances:index')
    page_title = _("Rebuild Instance")
    submit_label = page_title

    def get_context_data(self, **kwargs):
        context = super(RebuildView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        context['can_set_server_password'] = api.nova.can_set_server_password()
        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        instance_id = self.kwargs['instance_id']
        try:
            return api.nova.server_get(self.request, instance_id)
        except Exception:
            redirect = reverse("horizon:project:instances:index")
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        instance = self.get_object()
        initial = {'instance_id': self.kwargs['instance_id'],
                   'description': getattr(instance, 'description', '')}
        return initial


class DecryptPasswordView(forms.ModalFormView):
    form_class = project_forms.DecryptPasswordInstanceForm
    template_name = 'project/instances/decryptpassword.html'
    success_url = reverse_lazy('horizon:project:instances:index')
    page_title = _("Retrieve Instance Password")

    def get_context_data(self, **kwargs):
        context = super(DecryptPasswordView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        context['keypair_name'] = self.kwargs['keypair_name']
        return context

    def get_initial(self):
        return {'instance_id': self.kwargs['instance_id'],
                'keypair_name': self.kwargs['keypair_name']}


class DisassociateView(forms.ModalFormView):
    form_class = project_forms.Disassociate
    template_name = 'project/instances/disassociate.html'
    success_url = reverse_lazy('horizon:project:instances:index')
    page_title = _("Disassociate floating IP")
    submit_label = _("Disassociate")

    def get_context_data(self, **kwargs):
        context = super(DisassociateView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        return context

    def get_initial(self):
        return {'instance_id': self.kwargs['instance_id']}


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.InstanceDetailTabs
    template_name = 'horizon/common/_detail.html'
    redirect_url = 'horizon:project:instances:index'
    page_title = "{{ instance.name|default:instance.id }}"
    image_url = 'horizon:project:images:images:detail'
    volume_url = 'horizon:project:volumes:detail'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        instance = self.get_data()
        if instance.image:
            instance.image_url = reverse(self.image_url,
                                         args=[instance.image['id']])
        instance.volume_url = self.volume_url
        context["instance"] = instance
        context["url"] = get_url_with_pagination(
            self.request,
            project_tables.InstancesTable._meta.pagination_param,
            project_tables.InstancesTable._meta.prev_pagination_param,
            self.redirect_url)

        context["actions"] = self._get_actions(instance)
        return context

    def _get_actions(self, instance):
        table = project_tables.InstancesTable(self.request)
        return table.render_row_actions(instance)

    def _get_volumes(self, instance):
        instance_id = instance.id
        try:
            instance.volumes = api.nova.instance_volumes_list(self.request,
                                                              instance_id)
            # Sort by device name
            instance.volumes.sort(key=lambda vol: vol.device)
        except Exception:
            msg = _('Unable to retrieve volume list for instance '
                    '"%(name)s" (%(id)s).') % {'name': instance.name,
                                               'id': instance_id}
            exceptions.handle(self.request, msg, ignore=True)

    def _get_flavor(self, instance):
        instance_id = instance.id
        try:
            instance.full_flavor = api.nova.flavor_get(
                self.request, instance.flavor["id"])
        except Exception:
            msg = _('Unable to retrieve flavor information for instance '
                    '"%(name)s" (%(id)s).') % {'name': instance.name,
                                               'id': instance_id}
            exceptions.handle(self.request, msg, ignore=True)

    def _get_security_groups(self, instance):
        instance_id = instance.id
        try:
            instance.security_groups = api.neutron.server_security_groups(
                self.request, instance_id)
        except Exception:
            msg = _('Unable to retrieve security groups for instance '
                    '"%(name)s" (%(id)s).') % {'name': instance.name,
                                               'id': instance_id}
            exceptions.handle(self.request, msg, ignore=True)

    def _update_addresses(self, instance):
        instance_id = instance.id
        try:
            api.network.servers_update_addresses(self.request, [instance])
        except Exception:
            msg = _('Unable to retrieve IP addresses from Neutron for '
                    'instance "%(name)s" (%(id)s).') \
                % {'name': instance.name, 'id': instance_id}
            exceptions.handle(self.request, msg, ignore=True)

    @memoized.memoized_method
    def get_data(self):
        instance_id = self.kwargs['instance_id']

        try:
            instance = api.nova.server_get(self.request, instance_id)
        except Exception:
            redirect = reverse(self.redirect_url)
            exceptions.handle(self.request,
                              _('Unable to retrieve details for '
                                'instance "%s".') % instance_id,
                              redirect=redirect)
            # Not all exception types handled above will result in a redirect.
            # Need to raise here just in case.
            raise exceptions.Http302(redirect)

        choices = project_tables.STATUS_DISPLAY_CHOICES
        instance.status_label = (
            filters.get_display_label(choices, instance.status))

        futurist_utils.call_functions_parallel(
            (self._get_volumes, [instance]),
            (self._get_flavor, [instance]),
            (self._get_security_groups, [instance]),
            (self._update_addresses, [instance]),
        )

        return instance

    def get_tabs(self, request, *args, **kwargs):
        instance = self.get_data()
        return self.tab_group_class(request, instance=instance, **kwargs)


class ResizeView(workflows.WorkflowView):
    workflow_class = project_workflows.ResizeInstance
    success_url = reverse_lazy("horizon:project:instances:index")

    def get_context_data(self, **kwargs):
        context = super(ResizeView, self).get_context_data(**kwargs)
        context["instance_id"] = self.kwargs['instance_id']
        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        instance_id = self.kwargs['instance_id']
        try:
            instance = api.nova.server_get(self.request, instance_id)
        except Exception:
            redirect = reverse("horizon:project:instances:index")
            msg = _('Unable to retrieve instance details.')
            exceptions.handle(self.request, msg, redirect=redirect)
        flavor_id = instance.flavor['id']
        flavors = self.get_flavors()
        if flavor_id in flavors:
            instance.flavor_name = flavors[flavor_id].name
        else:
            try:
                flavor = api.nova.flavor_get(self.request, flavor_id)
                instance.flavor_name = flavor.name
            except Exception:
                msg = _('Unable to retrieve flavor information for instance '
                        '"%s".') % instance_id
                exceptions.handle(self.request, msg, ignore=True)
                instance.flavor_name = _("Not available")
        return instance

    @memoized.memoized_method
    def get_flavors(self, *args, **kwargs):
        try:
            flavors = api.nova.flavor_list(self.request)
            return OrderedDict((str(flavor.id), flavor) for flavor in flavors)
        except Exception:
            redirect = reverse("horizon:project:instances:index")
            exceptions.handle(self.request,
                              _('Unable to retrieve flavors.'),
                              redirect=redirect)

    def get_initial(self):
        initial = super(ResizeView, self).get_initial()
        _object = self.get_object()
        if _object:
            initial.update(
                {'instance_id': self.kwargs['instance_id'],
                 'name': getattr(_object, 'name', None),
                 'old_flavor_id': _object.flavor['id'],
                 'old_flavor_name': getattr(_object, 'flavor_name', ''),
                 'flavors': self.get_flavors()})
        return initial


class AttachInterfaceView(forms.ModalFormView):
    form_class = project_forms.AttachInterface
    template_name = 'project/instances/attach_interface.html'
    page_title = _("Attach Interface")
    form_id = "attach_interface_form"
    submit_label = _("Attach Interface")
    success_url = reverse_lazy('horizon:project:instances:index')

    def get_context_data(self, **kwargs):
        context = super(AttachInterfaceView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        return context

    def get_initial(self):
        args = {'instance_id': self.kwargs['instance_id']}
        submit_url = "horizon:project:instances:attach_interface"
        self.submit_url = reverse(submit_url, kwargs=args)
        return args


class AttachVolumeView(forms.ModalFormView):
    form_class = project_forms.AttachVolume
    template_name = 'project/instances/attach_volume.html'
    page_title = _("Attach Volume")
    modal_id = "attach_volume_modal"
    submit_label = _("Attach Volume")
    success_url = reverse_lazy('horizon:project:instances:index')

    def get_initial(self):
        args = {'instance_id': self.kwargs['instance_id']}
        submit_url = "horizon:project:instances:attach_volume"
        self.submit_url = reverse(submit_url, kwargs=args)
        try:
            volume_list = api.cinder.volume_list(self.request)
        except Exception:
            volume_list = []
            exceptions.handle(self.request,
                              _("Unable to retrieve volume information."))
        return {"instance_id": self.kwargs["instance_id"],
                "volume_list": volume_list}

    def get_context_data(self, **kwargs):
        context = super(AttachVolumeView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        return context


class DetachVolumeView(forms.ModalFormView):
    form_class = project_forms.DetachVolume
    template_name = 'project/instances/detach_volume.html'
    page_title = _("Detach Volume")
    modal_id = "detach_volume_modal"
    submit_label = _("Detach Volume")
    success_url = reverse_lazy('horizon:project:instances:index')

    def get_initial(self):
        args = {'instance_id': self.kwargs['instance_id']}
        submit_url = "horizon:project:instances:detach_volume"
        self.submit_url = reverse(submit_url, kwargs=args)
        return {"instance_id": self.kwargs["instance_id"]}

    def get_context_data(self, **kwargs):
        context = super(DetachVolumeView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        return context


class DetachInterfaceView(forms.ModalFormView):
    form_class = project_forms.DetachInterface
    template_name = 'project/instances/detach_interface.html'
    page_title = _("Detach Interface")
    form_id = "detach_interface_form"
    submit_label = _("Detach Interface")
    success_url = reverse_lazy('horizon:project:instances:index')

    def get_context_data(self, **kwargs):
        context = super(DetachInterfaceView, self).get_context_data(**kwargs)
        context['instance_id'] = self.kwargs['instance_id']
        return context

    def get_initial(self):
        args = {"instance_id": self.kwargs["instance_id"]}
        submit_url = "horizon:project:instances:detach_interface"
        self.submit_url = reverse(submit_url, kwargs=args)
        return args


class UpdatePortView(port_views.UpdateView):
    workflow_class = project_workflows.UpdatePort
    failure_url = 'horizon:project:instances:detail'

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        port_id = self.kwargs['port_id']
        try:
            return api.neutron.port_get(self.request, port_id)
        except Exception:
            redirect = reverse(self.failure_url,
                               args=(self.kwargs['instance_id'],))
            msg = _('Unable to retrieve port details')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        initial = super(UpdatePortView, self).get_initial()
        initial['instance_id'] = self.kwargs['instance_id']
        return initial


class RescueView(forms.ModalFormView):
    form_class = project_forms.RescueInstanceForm
    template_name = 'project/instances/rescue.html'
    submit_label = _("Confirm")
    submit_url = "horizon:project:instances:rescue"
    success_url = reverse_lazy('horizon:project:instances:index')
    page_title = _("Rescue Instance")

    def get_context_data(self, **kwargs):
        context = super(RescueView, self).get_context_data(**kwargs)
        context["instance_id"] = self.kwargs['instance_id']
        args = (self.kwargs['instance_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        return {'instance_id': self.kwargs["instance_id"]}
