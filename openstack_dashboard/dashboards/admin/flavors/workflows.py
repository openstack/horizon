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
    _flavor_id_regex = (r'^[a-zA-Z0-9. _-]+$')
    _flavor_id_help_text = _("flavor id can only contain alphanumeric "
                             "characters, underscores, periods, hyphens, "
                             "spaces.")
    name = forms.CharField(
        label=_("Name"),
        max_length=255)
    flavor_id = forms.RegexField(label=_("ID"),
                                 regex=_flavor_id_regex,
                                 required=False,
                                 initial='auto',
                                 max_length=255,
                                 help_text=_flavor_id_help_text)
    vcpus = forms.IntegerField(label=_("VCPUs"),
                               min_value=1,
                               max_value=2147483647)
    memory_mb = forms.IntegerField(label=_("RAM (MB)"),
                                   min_value=1,
                                   max_value=2147483647)
    disk_gb = forms.IntegerField(label=_("Root Disk (GB)"),
                                 min_value=0,
                                 max_value=2147483647)
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

    def clean_name(self):
        name = self.cleaned_data.get('name').strip()
        if not name:
            msg = _('Flavor name cannot be empty.')
            self._errors['name'] = self.error_class([msg])
        return name

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


class FlavorAccessAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(FlavorAccessAction, self).__init__(request, *args, **kwargs)
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
        flavor = context.get('flavor')
        flavor_access = []
        try:
            if flavor and not flavor.is_public:
                flavor_access = [project.tenant_id for project in
                                 context['current_flavor_access']]
        except Exception:
            exceptions.handle(request, err_msg)

        self.fields[field_name].initial = flavor_access

    class Meta(object):
        name = _("Flavor Access")
        slug = "flavor_access"


class FlavorAccess(workflows.UpdateMembersStep):
    action_class = FlavorAccessAction
    help_text = _("Select the projects where the flavors will be used. If no "
                  "projects are selected, then the flavor will be available "
                  "in all projects.")
    available_list_title = _("All Projects")
    members_list_title = _("Selected Projects")
    no_available_text = _("No projects found.")
    no_members_text = _("No projects selected. "
                        "All projects can use the flavor.")
    show_roles = False

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['flavor_access'] = data.get(member_field_name, [])
        return context


class CreateFlavorAccess(FlavorAccess):
    contributes = ("flavor_access",)


class UpdateFlavorAccess(FlavorAccess):
    depends_on = ("flavor", "current_flavor_access")
    contributes = ("flavor_access",)


class CreateFlavor(workflows.Workflow):
    slug = "create_flavor"
    name = _("Create Flavor")
    finalize_button_name = _("Create Flavor")
    success_message = _('Created new flavor "%s".')
    failure_message = _('Unable to create flavor "%s".')
    success_url = "horizon:admin:flavors:index"
    default_steps = (CreateFlavorInfo,
                     CreateFlavorAccess)

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


class UpdateFlavor(workflows.Workflow):
    slug = "update_flavor"
    name = _("Edit Flavor")
    finalize_button_name = _("Save")
    success_message = _('Modified flavor access of "%s".')
    failure_message = _('Unable to modify flavor access of "%s".')
    success_url = "horizon:admin:flavors:index"
    default_steps = (UpdateFlavorAccess,)

    def format_status_message(self, message):
        return message % self.context['flavor'].name

    def handle(self, request, data):
        flavor_projects = data["flavor_access"]
        flavor = self.context['flavor']

        # Check if the flavor info is not actually changed
        try:
            if flavor.is_public:
                old_flavor_projects = []
            else:
                old_flavor_projects = [project.tenant_id for project in
                                       self.context['current_flavor_access']]
            to_remove = [project for project in old_flavor_projects if project
                         not in flavor_projects]
            to_add = [project for project in flavor_projects if project not in
                      old_flavor_projects]
            for project in to_remove:
                api.nova.remove_tenant_from_flavor(request,
                                                   flavor.id,
                                                   project)
            for project in to_add:
                api.nova.add_tenant_to_flavor(request,
                                              flavor.id,
                                              project)
            return True
        except Exception:
            # Error message will be shown by the workflow view.
            return False
