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


from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.api import cinder

INDEX_URL = "horizon:project:volumes:index"
CGROUP_VOLUME_MEMBER_SLUG = "update_members"


def cinder_az_supported(request):
    try:
        return cinder.extension_supported(request, 'AvailabilityZones')
    except Exception:
        exceptions.handle(request, _('Unable to determine if availability '
                                     'zones extension is supported.'))
        return False


def availability_zones(request):
    zone_list = []
    if cinder_az_supported(request):
        try:
            zones = api.cinder.availability_zone_list(request)
            zone_list = [(zone.zoneName, zone.zoneName)
                         for zone in zones if zone.zoneState['available']]
            zone_list.sort()
        except Exception:
            exceptions.handle(request, _('Unable to retrieve availability '
                                         'zones.'))
    if not zone_list:
        zone_list.insert(0, ("", _("No availability zones found")))
    elif len(zone_list) > 1:
        zone_list.insert(0, ("", _("Any Availability Zone")))

    return zone_list


class AddCGroupInfoAction(workflows.Action):
    name = forms.CharField(label=_("Name"),
                           max_length=255)
    description = forms.CharField(widget=forms.widgets.Textarea(
                                  attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    availability_zone = forms.ChoiceField(
        label=_("Availability Zone"),
        required=False,
        widget=forms.Select(
            attrs={'class': 'switched',
                   'data-switch-on': 'source',
                   'data-source-no_source_type': _('Availability Zone'),
                   'data-source-image_source': _('Availability Zone')}))

    def __init__(self, request, *args, **kwargs):
        super(AddCGroupInfoAction, self).__init__(request,
                                                  *args,
                                                  **kwargs)
        self.fields['availability_zone'].choices = \
            availability_zones(request)

    class Meta(object):
        name = _("Consistency Group Information")
        help_text = _("Volume consistency groups provide a mechanism for "
                      "creating snapshots of multiple volumes at the same "
                      "point-in-time to ensure data consistency\n\n"
                      "A consistency group can support more than one volume "
                      "type, but it can only contain volumes hosted by the "
                      "same back end.")
        slug = "set_cgroup_info"

    def clean(self):
        cleaned_data = super(AddCGroupInfoAction, self).clean()
        name = cleaned_data.get('name')

        try:
            cgroups = cinder.volume_cgroup_list(self.request)
        except Exception:
            msg = _('Unable to get consistency group list')
            exceptions.check_message(["Connection", "refused"], msg)
            raise

        if cgroups is not None and name is not None:
            for cgroup in cgroups:
                if cgroup.name.lower() == name.lower():
                    raise forms.ValidationError(
                        _('The name "%s" is already used by '
                          'another consistency group.')
                        % name
                    )

        return cleaned_data


class AddCGroupInfoStep(workflows.Step):
    action_class = AddCGroupInfoAction
    contributes = ("availability_zone",
                   "description",
                   "name")


class AddVolumeTypesToCGroupAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(AddVolumeTypesToCGroupAction, self).__init__(request,
                                                           *args,
                                                           **kwargs)
        err_msg = _('Unable to get the available volume types')

        default_role_field_name = self.get_default_role_field_name()
        self.fields[default_role_field_name] = forms.CharField(required=False)
        self.fields[default_role_field_name].initial = 'member'

        field_name = self.get_member_field_name('member')
        self.fields[field_name] = forms.MultipleChoiceField(required=False)

        vtypes = []
        try:
            vtypes = cinder.volume_type_list(request)
        except Exception:
            exceptions.handle(request, err_msg)

        vtype_names = []
        for vtype in vtypes:
            if vtype.name not in vtype_names:
                vtype_names.append(vtype.name)
        vtype_names.sort()

        self.fields[field_name].choices = \
            [(vtype_name, vtype_name) for vtype_name in vtype_names]

    class Meta(object):
        name = _("Manage Volume Types")
        slug = "add_vtypes_to_cgroup"


class AddVolTypesToCGroupStep(workflows.UpdateMembersStep):
    action_class = AddVolumeTypesToCGroupAction
    help_text = _("Add volume types to this consistency group. "
                  "Multiple volume types can be added to the same "
                  "consistency group only if they are associated with "
                  "same back end.")
    available_list_title = _("All available volume types")
    members_list_title = _("Selected volume types")
    no_available_text = _("No volume types found.")
    no_members_text = _("No volume types selected.")
    show_roles = False
    contributes = ("volume_types",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['volume_types'] = data.get(member_field_name, [])
        return context


class AddVolumesToCGroupAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(AddVolumesToCGroupAction, self).__init__(request,
                                                       *args,
                                                       **kwargs)
        err_msg = _('Unable to get the available volumes')

        default_role_field_name = self.get_default_role_field_name()
        self.fields[default_role_field_name] = forms.CharField(required=False)
        self.fields[default_role_field_name].initial = 'member'

        field_name = self.get_member_field_name('member')
        self.fields[field_name] = forms.MultipleChoiceField(required=False)

        vtypes = self.initial['vtypes']
        try:
            # get names of volume types associated with CG
            vtype_names = []
            volume_types = cinder.volume_type_list(request)
            for volume_type in volume_types:
                if volume_type.id in vtypes:
                    vtype_names.append(volume_type.name)

            # collect volumes that are associated with volume types
            vol_list = []
            volumes = cinder.volume_list(request)
            for volume in volumes:
                if volume.volume_type in vtype_names:
                    in_this_cgroup = False
                    if hasattr(volume, 'consistencygroup_id'):
                        if volume.consistencygroup_id == \
                                self.initial['cgroup_id']:
                            in_this_cgroup = True
                    vol_list.append({'volume_name': volume.name,
                                     'volume_id': volume.id,
                                     'in_cgroup': in_this_cgroup,
                                     'is_duplicate': False})
            sorted_vol_list = sorted(vol_list, key=lambda k: k['volume_name'])

            # mark any duplicate volume names
            for index, volume in enumerate(sorted_vol_list):
                if index < len(sorted_vol_list) - 1:
                    if volume['volume_name'] == \
                            sorted_vol_list[index + 1]['volume_name']:
                        volume['is_duplicate'] = True
                        sorted_vol_list[index + 1]['is_duplicate'] = True

            # update display with all available vols and those already
            # assigned to consistency group
            available_vols = []
            assigned_vols = []
            for volume in sorted_vol_list:
                if volume['is_duplicate']:
                    # add id to differentiate volumes to user
                    entry = volume['volume_name'] + \
                        " [" + volume['volume_id'] + "]"
                else:
                    entry = volume['volume_name']
                available_vols.append((entry, entry))
                if volume['in_cgroup']:
                    assigned_vols.append(entry)

        except Exception:
            exceptions.handle(request, err_msg)

        self.fields[field_name].choices = \
            available_vols
        self.fields[field_name].initial = assigned_vols

    class Meta(object):
        name = _("Manage Volumes")
        slug = "add_volumes_to_cgroup"


class AddVolumesToCGroupStep(workflows.UpdateMembersStep):
    action_class = AddVolumesToCGroupAction
    help_text = _("Add/remove volumes to/from this consistency group. "
                  "Only volumes associated with the volume type(s) assigned "
                  "to this consistency group will be available for selection.")
    available_list_title = _("All available volumes")
    members_list_title = _("Selected volumes")
    no_available_text = _("No volumes found.")
    no_members_text = _("No volumes selected.")
    show_roles = False
    depends_on = ("cgroup_id", "name", "vtypes")
    contributes = ("volumes",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['volumes'] = data.get(member_field_name, [])
        return context


class CreateCGroupWorkflow(workflows.Workflow):
    slug = "create_cgroup"
    name = _("Create Consistency Group")
    finalize_button_name = _("Create Consistency Group")
    failure_message = _('Unable to create consistency group.')
    success_message = _('Created new volume consistency group')
    success_url = INDEX_URL
    default_steps = (AddCGroupInfoStep,
                     AddVolTypesToCGroupStep)

    def handle(self, request, context):
        selected_vol_types = context['volume_types']

        try:
            vol_types = cinder.volume_type_list_with_qos_associations(
                request)
        except Exception:
            msg = _('Unable to get volume type list')
            exceptions.check_message(["Connection", "refused"], msg)
            return False

        # ensure that all selected volume types share same backend name
        backend_name = None
        invalid_backend = False
        for selected_vol_type in selected_vol_types:
            if not invalid_backend:
                for vol_type in vol_types:
                    if selected_vol_type == vol_type.name:
                        if hasattr(vol_type, "extra_specs"):
                            vol_type_backend = \
                                vol_type.extra_specs['volume_backend_name']
                            if vol_type_backend is None:
                                invalid_backend = True
                                break
                            if backend_name is None:
                                backend_name = vol_type_backend
                            if vol_type_backend != backend_name:
                                invalid_backend = True
                                break
                        else:
                            invalid_backend = True
                            break

        if invalid_backend:
            msg = _('All selected volume types must be associated '
                    'with the same volume backend name.')
            exceptions.handle(request, msg)
            return False

        try:
            vtypes_str = ",".join(context['volume_types'])
            self.object = \
                cinder.volume_cgroup_create(
                    request,
                    vtypes_str,
                    name=context['name'],
                    description=context['description'],
                    availability_zone=context['availability_zone'])
        except Exception:
            exceptions.handle(request, _('Unable to create consistency '
                                         'group.'))
            return False

        return True


class UpdateCGroupWorkflow(workflows.Workflow):
    slug = "create_cgroup"
    name = _("Add/Remove Consistency Group Volumes")
    finalize_button_name = _("Edit Consistency Group")
    success_message = _('Edit consistency group "%s".')
    failure_message = _('Unable to edit consistency group')
    success_url = INDEX_URL
    default_steps = (AddVolumesToCGroupStep,)

    def handle(self, request, context):
        cgroup_id = context['cgroup_id']
        add_vols = []
        remove_vols = []
        try:
            selected_volumes = context['volumes']
            volumes = cinder.volume_list(request)

            # scan all volumes and make correct consistency group is set
            for volume in volumes:
                selected = False
                for selection in selected_volumes:
                    if " [" in selection:
                        # handle duplicate volume names
                        sel = selection.split(" [")
                        sel_vol_name = sel[0]
                        sel_vol_id = sel[1].split("]")[0]
                    else:
                        sel_vol_name = selection
                        sel_vol_id = None

                    if volume.name == sel_vol_name:
                        if sel_vol_id:
                            if sel_vol_id == volume.id:
                                selected = True
                        else:
                            selected = True

                    if selected:
                        break

                if selected:
                    # ensure this volume is in this consistency group
                    if hasattr(volume, 'consistencygroup_id'):
                        if volume.consistencygroup_id != cgroup_id:
                            add_vols.append(volume.id)
                    else:
                        add_vols.append(volume.id)
                else:
                    # ensure this volume is not in our consistency group
                    if hasattr(volume, 'consistencygroup_id'):
                        if volume.consistencygroup_id == cgroup_id:
                            remove_vols.append(volume.id)

            add_vols_str = ",".join(add_vols)
            remove_vols_str = ",".join(remove_vols)
            cinder.volume_cgroup_update(request,
                                        cgroup_id,
                                        name=context['name'],
                                        add_vols=add_vols_str,
                                        remove_vols=remove_vols_str)

            # before returning, ensure all new volumes are correctly assigned
            self._verify_changes(request, cgroup_id, add_vols, remove_vols)

            message = _('Updating volume consistency '
                        'group "%s"') % context['name']
            messages.info(request, message)
        except Exception:
            exceptions.handle(request, _('Unable to edit consistency group.'))
            return False

        return True

    def _verify_changes(self, request, cgroup_id, add_vols, remove_vols):
        search_opts = {'consistencygroup_id': cgroup_id}
        done = False
        while not done:
            done = True
            volumes = cinder.volume_list(request,
                                         search_opts=search_opts)
            assigned_vols = []
            for volume in volumes:
                assigned_vols.append(volume.id)

            for add_vol in add_vols:
                if add_vol not in assigned_vols:
                    done = False

            for remove_vol in remove_vols:
                if remove_vol in assigned_vols:
                    done = False
