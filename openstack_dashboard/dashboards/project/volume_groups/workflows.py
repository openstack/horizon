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
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.api import cinder

INDEX_URL = "horizon:project:volume_groups:index"


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


class AddGroupInfoAction(workflows.Action):
    name = forms.CharField(label=_("Name"),
                           max_length=255)
    description = forms.CharField(widget=forms.widgets.Textarea(
                                  attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    group_type = forms.ChoiceField(
        label=_("Group Type"),
        widget=forms.ThemableSelectWidget())
    availability_zone = forms.ChoiceField(
        label=_("Availability Zone"),
        required=False,
        widget=forms.ThemableSelectWidget(
            attrs={'class': 'switched',
                   'data-switch-on': 'source',
                   'data-source-no_source_type': _('Availability Zone'),
                   'data-source-image_source': _('Availability Zone')}))

    def __init__(self, request, *args, **kwargs):
        super(AddGroupInfoAction, self).__init__(request,
                                                 *args,
                                                 **kwargs)
        self.fields['availability_zone'].choices = \
            availability_zones(request)
        try:
            # Group type name 'default_cgsnapshot_type' is reserved for
            # consistency group and it cannot be used for a group type.
            # Let's exclude it.
            group_types = [(t.id, t.name) for t
                           in api.cinder.group_type_list(request)
                           if t.name != 'default_cgsnapshot_type']
        except Exception:
            exceptions.handle(request, _('Unable to retrieve group types.'))
        if group_types:
            group_types.insert(0, ("", _("Select group type")))
        else:
            group_types.insert(0, ("", _("No valid group type")))
        self.fields['group_type'].choices = group_types

    class Meta(object):
        name = _("Group Information")
        help_text = _("Volume groups provide a mechanism for "
                      "creating snapshots of multiple volumes at the same "
                      "point-in-time to ensure data consistency\n\n"
                      "A volume group can support more than one volume "
                      "type, but it can only contain volumes hosted by the "
                      "same back end.")
        slug = "set_group_info"


class AddGroupInfoStep(workflows.Step):
    action_class = AddGroupInfoAction
    contributes = ("availability_zone", "group_type",
                   "description",
                   "name")


class AddVolumeTypesToGroupAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(AddVolumeTypesToGroupAction, self).__init__(request,
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

        vtype_list = [(vtype.id, vtype.name)
                      for vtype in vtypes]
        self.fields[field_name].choices = vtype_list

    class Meta(object):
        name = _("Manage Volume Types")
        slug = "add_vtypes_to_group"

    def clean(self):
        cleaned_data = super(AddVolumeTypesToGroupAction, self).clean()
        volume_types = cleaned_data.get('add_vtypes_to_group_role_member')
        if not volume_types:
            raise forms.ValidationError(
                _('At least one volume type must be assigned '
                  'to a group.')
            )

        return cleaned_data


class AddVolTypesToGroupStep(workflows.UpdateMembersStep):
    action_class = AddVolumeTypesToGroupAction
    help_text = _("Add volume types to this group. "
                  "Multiple volume types can be added to the same "
                  "group only if they are associated with "
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


class AddVolumesToGroupAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(AddVolumesToGroupAction, self).__init__(request,
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
            # get names of volume types associated with group
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
                    group_id = None
                    vol_is_available = False
                    in_this_group = False
                    if hasattr(volume, 'group_id'):
                        # this vol already belongs to a group
                        # only include it here if it belongs to this group
                        group_id = volume.group_id

                    if not group_id:
                        # put this vol in the available list
                        vol_is_available = True
                    elif group_id == self.initial['group_id']:
                        # put this vol in the assigned to group list
                        vol_is_available = True
                        in_this_group = True

                    if vol_is_available:
                        vol_list.append({'volume_name': volume.name,
                                         'volume_id': volume.id,
                                         'in_group': in_this_group,
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
            # assigned to group
            available_vols = []
            assigned_vols = []
            for volume in sorted_vol_list:
                if volume['is_duplicate']:
                    # add id to differentiate volumes to user
                    entry = volume['volume_name'] + \
                        " [" + volume['volume_id'] + "]"
                else:
                    entry = volume['volume_name']
                available_vols.append((volume['volume_id'], entry))
                if volume['in_group']:
                    assigned_vols.append(volume['volume_id'])

        except Exception:
            exceptions.handle(request, err_msg)

        self.fields[field_name].choices = available_vols
        self.fields[field_name].initial = assigned_vols

    class Meta(object):
        name = _("Manage Volumes")
        slug = "add_volumes_to_group"


class AddVolumesToGroupStep(workflows.UpdateMembersStep):
    action_class = AddVolumesToGroupAction
    help_text = _("Add/remove volumes to/from this group. "
                  "Only volumes associated with the volume type(s) assigned "
                  "to this group will be available for selection.")
    available_list_title = _("All available volumes")
    members_list_title = _("Selected volumes")
    no_available_text = _("No volumes found.")
    no_members_text = _("No volumes selected.")
    show_roles = False
    depends_on = ("group_id", "name", "vtypes")
    contributes = ("volumes",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['volumes'] = data.get(member_field_name, [])
        return context


class CreateGroupWorkflow(workflows.Workflow):
    slug = "create_group"
    name = _("Create Group")
    finalize_button_name = _("Create Group")
    failure_message = _('Unable to create group.')
    success_message = _('Created new volume group')
    success_url = INDEX_URL
    default_steps = (AddGroupInfoStep,
                     AddVolTypesToGroupStep)

    def handle(self, request, context):
        try:
            self.object = cinder.group_create(
                request,
                context['name'],
                context['group_type'],
                context['volume_types'],
                description=context['description'],
                availability_zone=context['availability_zone'])
        except Exception:
            exceptions.handle(request, _('Unable to create group.'))
            return False

        return True


class UpdateGroupWorkflow(workflows.Workflow):
    slug = "update_group"
    name = _("Add/Remove Group Volumes")
    finalize_button_name = _("Submit")
    success_message = _('Updated volumes for group.')
    failure_message = _('Unable to update volumes for group')
    success_url = INDEX_URL
    default_steps = (AddVolumesToGroupStep,)

    def handle(self, request, context):
        group_id = context['group_id']
        add_vols = []
        remove_vols = []
        try:
            selected_volumes = context['volumes']
            volumes = cinder.volume_list(request)

            # scan all volumes and make correct consistency group is set
            for volume in volumes:
                selected = False
                for selection in selected_volumes:
                    if selection == volume.id:
                        selected = True
                        break

                if selected:
                    # ensure this volume is in this consistency group
                    if hasattr(volume, 'group_id'):
                        if volume.group_id != group_id:
                            add_vols.append(volume.id)
                    else:
                        add_vols.append(volume.id)
                else:
                    # ensure this volume is not in our consistency group
                    if hasattr(volume, 'group_id'):
                        if volume.group_id == group_id:
                            # remove from this group
                            remove_vols.append(volume.id)

            if not add_vols and not remove_vols:
                # nothing to change
                return True

            cinder.group_update(request, group_id,
                                add_volumes=add_vols,
                                remove_volumes=remove_vols)

        except Exception:
            # error message supplied by form
            return False

        return True
