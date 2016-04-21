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


from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api


class CreateFlavorInfoAction(workflows.Action):
    _flavor_id_regex = (r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-'
                        r'[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|[0-9]+|auto$')
    _flavor_id_help_text = _("Flavor ID should be UUID4 or integer. "
                             "Leave this field blank or use 'auto' to set "
                             "a random UUID4.")
    name = forms.RegexField(
        label=_("Name"),
        max_length=255,
        regex=r'^[\w\.\- ]+$',
        error_messages={'invalid': _('Name may only contain letters, numbers, '
                                     'underscores, periods and hyphens.')})
    flavor_id = forms.RegexField(label=_("ID"),
                                 regex=_flavor_id_regex,
                                 required=False,
                                 initial='auto',
                                 help_text=_flavor_id_help_text)
    vcpus = forms.IntegerField(label=_("VCPUs"),
                               min_value=1)
    memory_mb = forms.IntegerField(label=_("RAM (MB)"),
                                   min_value=1)
    disk_gb = forms.IntegerField(label=_("Root Disk (GB)"),
                                 min_value=0)
    eph_gb = forms.IntegerField(label=_("Ephemeral Disk (GB)"),
                                required=False,
                                initial=0,
                                min_value=0)
    swap_mb = forms.IntegerField(label=_("Swap Disk (MB)"),
                                 required=False,
                                 initial=0,
                                 min_value=0)
    rxtx_factor = forms.FloatField(label=_("RX/TX Factor"),
                                   required=False,
                                   initial=1,
                                   min_value=1)

    class Meta(object):
        name = _("Flavor Information")
        help_text = _("Flavors define the sizes for RAM, disk, number of "
                      "cores, and other resources and can be selected when "
                      "users deploy instances.")

    def clean(self):
        cleaned_data = super(CreateFlavorInfoAction, self).clean()
        name = cleaned_data.get('name')
        flavor_id = cleaned_data.get('flavor_id')

        try:
            flavors = api.nova.flavor_list(self.request, None)
        except Exception:
            flavors = []
            msg = _('Unable to get flavor list')
            exceptions.check_message(["Connection", "refused"], msg)
            raise
        if flavors is not None and name is not None:
            for flavor in flavors:
                if flavor.name.lower() == name.lower():
                    error_msg = _('The name "%s" is already used by '
                                  'another flavor.') % name
                    self._errors['name'] = self.error_class([error_msg])
                if flavor.id == flavor_id:
                    error_msg = _('The ID "%s" is already used by '
                                  'another flavor.') % flavor_id
                    self._errors['flavor_id'] = self.error_class([error_msg])
        return cleaned_data


class CreateFlavorInfo(workflows.Step):
    action_class = CreateFlavorInfoAction
    contributes = ("flavor_id",
                   "name",
                   "vcpus",
                   "memory_mb",
                   "disk_gb",
                   "eph_gb",
                   "swap_mb",
                   "rxtx_factor")


class UpdateFlavorAccessAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(UpdateFlavorAccessAction, self).__init__(request,
                                                       *args,
                                                       **kwargs)
        err_msg = _('Unable to retrieve flavor access list. '
                    'Please try again later.')
        context = args[0]

        default_role_field_name = self.get_default_role_field_name()
        self.fields[default_role_field_name] = forms.CharField(required=False)
        self.fields[default_role_field_name].initial = 'member'

        field_name = self.get_member_field_name('member')
        self.fields[field_name] = forms.MultipleChoiceField(required=False)

        # Get list of available projects.
        all_projects = []
        try:
            all_projects, has_more = api.keystone.tenant_list(request)
        except Exception:
            exceptions.handle(request, err_msg)
        projects_list = [(project.id, project.name)
                         for project in all_projects]

        self.fields[field_name].choices = projects_list

        # If we have a POST from the CreateFlavor workflow, the flavor id
        # isn't an existing flavor. For the UpdateFlavor case, we don't care
        # about the access list for the current flavor anymore as we're about
        # to replace it.
        if request.method == 'POST':
            return

        # Get list of flavor projects if the flavor is not public.
        flavor_id = context.get('flavor_id')
        flavor_access = []
        try:
            if flavor_id:
                flavor = api.nova.flavor_get(request, flavor_id)
                if not flavor.is_public:
                    flavor_access = [project.tenant_id for project in
                                     api.nova.flavor_access_list(request,
                                                                 flavor_id)]
        except Exception:
            exceptions.handle(request, err_msg)

        self.fields[field_name].initial = flavor_access

    class Meta(object):
        name = _("Flavor Access")
        slug = "update_flavor_access"


class UpdateFlavorAccess(workflows.UpdateMembersStep):
    action_class = UpdateFlavorAccessAction
    help_text = _("Select the projects where the flavors will be used. If no "
                  "projects are selected, then the flavor will be available "
                  "in all projects.")
    available_list_title = _("All Projects")
    members_list_title = _("Selected Projects")
    no_available_text = _("No projects found.")
    no_members_text = _("No projects selected. "
                        "All projects can use the flavor.")
    show_roles = False
    depends_on = ("flavor_id",)
    contributes = ("flavor_access",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['flavor_access'] = data.get(member_field_name, [])
        return context


class CreateFlavor(workflows.Workflow):
    slug = "create_flavor"
    name = _("Create Flavor")
    finalize_button_name = _("Create Flavor")
    success_message = _('Created new flavor "%s".')
    failure_message = _('Unable to create flavor "%s".')
    success_url = "horizon:admin:flavors:index"
    default_steps = (CreateFlavorInfo,
                     UpdateFlavorAccess)

    def format_status_message(self, message):
        return message % self.context['name']

    def handle(self, request, data):
        flavor_id = data.get('flavor_id') or 'auto'
        swap = data.get('swap_mb') or 0
        ephemeral = data.get('eph_gb') or 0
        flavor_access = data['flavor_access']
        is_public = not flavor_access
        rxtx_factor = data.get('rxtx_factor') or 1

        # Create the flavor
        try:
            self.object = api.nova.flavor_create(request,
                                                 name=data['name'],
                                                 memory=data['memory_mb'],
                                                 vcpu=data['vcpus'],
                                                 disk=data['disk_gb'],
                                                 ephemeral=ephemeral,
                                                 swap=swap,
                                                 flavorid=flavor_id,
                                                 is_public=is_public,
                                                 rxtx_factor=rxtx_factor)
        except Exception:
            exceptions.handle(request, _('Unable to create flavor.'))
            return False

        # Update flavor access if the new flavor is not public
        flavor_id = self.object.id
        for project in flavor_access:
            try:
                api.nova.add_tenant_to_flavor(
                    request, flavor_id, project)
            except Exception:
                exceptions.handle(
                    request,
                    _('Unable to set flavor access for project %s.') % project)
        return True


class UpdateFlavorInfoAction(CreateFlavorInfoAction):
    flavor_id = forms.CharField(widget=forms.widgets.HiddenInput)

    class Meta(object):
        name = _("Flavor Information")
        slug = 'update_info'
        help_text = _("Edit the flavor details. Flavors define the sizes for "
                      "RAM, disk, number of cores, and other resources. "
                      "Flavors are selected when users deploy instances.")

    def clean(self):
        name = self.cleaned_data.get('name')
        flavor_id = self.cleaned_data.get('flavor_id')
        try:
            flavors = api.nova.flavor_list(self.request, None)
        except Exception:
            flavors = []
            msg = _('Unable to get flavor list')
            exceptions.check_message(["Connection", "refused"], msg)
            raise
        # Check if there is no flavor with the same name
        if flavors is not None and name is not None:
            for flavor in flavors:
                if (flavor.name.lower() == name.lower() and
                        flavor.id != flavor_id):
                    error_msg = _('The name "%s" is already used by '
                                  'another flavor.') % name
                    self._errors['name'] = self.error_class([error_msg])
        return self.cleaned_data


class UpdateFlavorInfo(workflows.Step):
    action_class = UpdateFlavorInfoAction
    depends_on = ("flavor_id",)
    contributes = ("name",
                   "vcpus",
                   "memory_mb",
                   "disk_gb",
                   "eph_gb",
                   "swap_mb",
                   "rxtx_factor")


class UpdateFlavor(workflows.Workflow):
    slug = "update_flavor"
    name = _("Edit Flavor")
    finalize_button_name = _("Save")
    success_message = _('Modified flavor "%s".')
    failure_message = _('Unable to modify flavor "%s".')
    success_url = "horizon:admin:flavors:index"
    default_steps = (UpdateFlavorInfo,
                     UpdateFlavorAccess)

    def format_status_message(self, message):
        return message % self.context['name']

    def handle(self, request, data):
        flavor_projects = data["flavor_access"]
        is_public = not flavor_projects

        # Update flavor information
        try:
            flavor_id = data['flavor_id']
            # Grab any existing extra specs, because flavor edit is currently
            # implemented as a delete followed by a create.
            extras_dict = api.nova.flavor_get_extras(self.request,
                                                     flavor_id,
                                                     raw=True)
            # Mark the existing flavor as deleted.
            api.nova.flavor_delete(request, flavor_id)
            # Then create a new flavor with the same name but a new ID.
            # This is in the same try/except block as the delete call
            # because if the delete fails the API will error out because
            # active flavors can't have the same name.
            flavor = api.nova.flavor_create(request,
                                            data['name'],
                                            data['memory_mb'],
                                            data['vcpus'],
                                            data['disk_gb'],
                                            ephemeral=data['eph_gb'],
                                            swap=data['swap_mb'],
                                            is_public=is_public,
                                            rxtx_factor=data['rxtx_factor'])
            if (extras_dict):
                api.nova.flavor_extra_set(request, flavor.id, extras_dict)
        except Exception:
            exceptions.handle(request, ignore=True)
            return False

        # Add flavor access if the flavor is not public.
        for project in flavor_projects:
            try:
                api.nova.add_tenant_to_flavor(request, flavor.id, project)
            except Exception:
                exceptions.handle(request, _('Modified flavor information, '
                                             'but unable to modify flavor '
                                             'access.'))
        return True
