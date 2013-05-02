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


from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from horizon import exceptions
from horizon import workflows
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.api import cinder, nova
from openstack_dashboard.api.base import is_service_enabled
from openstack_dashboard.usage.quotas import (NOVA_QUOTA_FIELDS,
                                              CINDER_QUOTA_FIELDS,
                                              QUOTA_FIELDS,
                                              get_disabled_quotas)

INDEX_URL = "horizon:admin:projects:index"
ADD_USER_URL = "horizon:admin:projects:create_user"


class UpdateProjectQuotaAction(workflows.Action):
    ifcb_label = _("Injected File Content Bytes")
    metadata_items = forms.IntegerField(min_value=-1,
                                        label=_("Metadata Items"))
    cores = forms.IntegerField(min_value=-1, label=_("VCPUs"))
    instances = forms.IntegerField(min_value=-1, label=_("Instances"))
    injected_files = forms.IntegerField(min_value=-1,
                                        label=_("Injected Files"))
    injected_file_content_bytes = forms.IntegerField(min_value=-1,
                                                     label=ifcb_label)
    volumes = forms.IntegerField(min_value=-1, label=_("Volumes"))
    gigabytes = forms.IntegerField(min_value=-1, label=_("Gigabytes"))
    ram = forms.IntegerField(min_value=-1, label=_("RAM (MB)"))
    floating_ips = forms.IntegerField(min_value=-1, label=_("Floating IPs"))
    fixed_ips = forms.IntegerField(min_value=-1, label=_("Fixed IPs"))
    security_groups = forms.IntegerField(min_value=-1,
                                         label=_("Security Groups"))
    security_group_rules = forms.IntegerField(min_value=-1,
                                              label=_("Security Group Rules"))

    def __init__(self, request, *args, **kwargs):
        super(UpdateProjectQuotaAction, self).__init__(request,
                                                       *args,
                                                       **kwargs)
        disabled_quotas = get_disabled_quotas(request)
        for field in disabled_quotas:
            if field in self.fields:
                self.fields[field].required = False
                self.fields[field].widget = forms.HiddenInput()

    class Meta:
        name = _("Quota")
        slug = 'update_quotas'
        help_text = _("From here you can set quotas "
                      "(max limits) for the project.")


class UpdateProjectQuota(workflows.Step):
    action_class = UpdateProjectQuotaAction
    depends_on = ("project_id",)
    contributes = QUOTA_FIELDS


class CreateProjectInfoAction(workflows.Action):
    name = forms.CharField(label=_("Name"))
    description = forms.CharField(widget=forms.widgets.Textarea(),
                                  label=_("Description"),
                                  required=False)
    enabled = forms.BooleanField(label=_("Enabled"),
                                 required=False,
                                 initial=True)

    class Meta:
        name = _("Project Info")
        help_text = _("From here you can create a new "
                      "project to organize users.")


class CreateProjectInfo(workflows.Step):
    action_class = CreateProjectInfoAction
    contributes = ("project_id",
                   "name",
                   "description",
                   "enabled")


class UpdateProjectMembersAction(workflows.Action):
    default_role = forms.CharField(required=False)

    def __init__(self, request, *args, **kwargs):
        super(UpdateProjectMembersAction, self).__init__(request,
                                                         *args,
                                                         **kwargs)
        err_msg = _('Unable to retrieve user list. Please try again later.')
        project_id = ''
        if 'project_id' in args[0]:
            project_id = args[0]['project_id']

        # Get the default role
        try:
            default_role = api.keystone.get_default_role(self.request)
            # Default role is necessary to add members to a project
            if default_role is None:
                default = getattr(settings,
                                  "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
                msg = _('Could not find default role "%s" in Keystone') % \
                        default
                raise exceptions.NotFound(msg)
        except:
            exceptions.handle(self.request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        self.fields['default_role'].initial = default_role.id

        # Get list of available users
        all_users = []
        try:
            all_users = api.keystone.user_list(request)
        except:
            exceptions.handle(request, err_msg)
        users_list = [(user.id, user.name) for user in all_users]

        # Get list of roles
        role_list = []
        try:
            role_list = api.keystone.role_list(request)
        except:
            exceptions.handle(request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        for role in role_list:
            field_name = "role_" + role.id
            label = _(role.name)
            self.fields[field_name] = forms.MultipleChoiceField(required=False,
                                                                label=label)
            self.fields[field_name].choices = users_list
            self.fields[field_name].initial = []

        # Figure out users & roles
        if project_id:
            for user in all_users:
                try:
                    roles = api.keystone.roles_for_user(self.request,
                                                        user.id,
                                                        project_id)
                except:
                    exceptions.handle(request,
                                      err_msg,
                                      redirect=reverse(INDEX_URL))
                for role in roles:
                    self.fields["role_" + role.id].initial.append(user.id)

    class Meta:
        name = _("Project Members")
        slug = "update_members"


class UpdateProjectMembers(workflows.UpdateMembersStep):
    action_class = UpdateProjectMembersAction
    available_list_title = _("All Users")
    members_list_title = _("Project Members")
    no_available_text = _("No users found.")
    no_members_text = _("No users.")

    def contribute(self, data, context):
        if data:
            try:
                roles = api.keystone.role_list(self.workflow.request)
            except:
                exceptions.handle(self.workflow.request,
                                  _('Unable to retrieve user list.'))

            post = self.workflow.request.POST
            for role in roles:
                field = "role_" + role.id
                context[field] = post.getlist(field)
        return context


class CreateProject(workflows.Workflow):
    slug = "create_project"
    name = _("Create Project")
    finalize_button_name = _("Create Project")
    success_message = _('Created new project "%s".')
    failure_message = _('Unable to create project "%s".')
    success_url = "horizon:admin:projects:index"
    default_steps = (CreateProjectInfo,
                     UpdateProjectMembers,
                     UpdateProjectQuota)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown project')

    def handle(self, request, data):
        # create the project
        try:
            desc = data['description']
            self.object = api.keystone.tenant_create(request,
                                                     tenant_name=data['name'],
                                                     description=desc,
                                                     enabled=data['enabled'])
        except:
            exceptions.handle(request, ignore=True)
            return False

        project_id = self.object.id

        # update project members
        users_to_add = 0
        try:
            available_roles = api.keystone.role_list(request)

            # count how many users are to be added
            for role in available_roles:
                role_list = data["role_" + role.id]
                users_to_add += len(role_list)
            # add new users to project
            for role in available_roles:
                role_list = data["role_" + role.id]
                users_added = 0
                for user in role_list:
                    api.keystone.add_tenant_user_role(request,
                                                      tenant_id=project_id,
                                                      user_id=user,
                                                      role_id=role.id)
                    users_added += 1
                users_to_add -= users_added
        except:
            exceptions.handle(request, _('Failed to add %s project members '
                                         'and set project quotas.'
                                         % users_to_add))

        # Update the project quota.
        nova_data = dict([(key, data[key]) for key in NOVA_QUOTA_FIELDS])
        try:
            nova.tenant_quota_update(request, project_id, **nova_data)

            if is_service_enabled(request, 'volume'):
                cinder_data = dict([(key, data[key]) for key in
                                    CINDER_QUOTA_FIELDS])
                cinder.tenant_quota_update(request,
                                           project_id,
                                           **cinder_data)
        except:
            exceptions.handle(request, _('Unable to set project quotas.'))
        return True


class UpdateProjectInfoAction(CreateProjectInfoAction):
    enabled = forms.BooleanField(required=False, label=_("Enabled"))

    class Meta:
        name = _("Project Info")
        slug = 'update_info'
        help_text = _("From here you can edit the project details.")


class UpdateProjectInfo(workflows.Step):
    action_class = UpdateProjectInfoAction
    depends_on = ("project_id",)
    contributes = ("name",
                   "description",
                   "enabled")


class UpdateProject(workflows.Workflow):
    slug = "update_project"
    name = _("Edit Project")
    finalize_button_name = _("Save")
    success_message = _('Modified project "%s".')
    failure_message = _('Unable to modify project "%s".')
    success_url = "horizon:admin:projects:index"
    default_steps = (UpdateProjectInfo,
                     UpdateProjectMembers,
                     UpdateProjectQuota)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown project')

    def handle(self, request, data):
        project_id = data['project_id']
        # update project info
        try:
            api.keystone.tenant_update(request,
                                       tenant_id=project_id,
                                       tenant_name=data['name'],
                                       description=data['description'],
                                       enabled=data['enabled'])
        except:
            exceptions.handle(request, ignore=True)
            return False

        # update project members
        users_to_modify = 0
        try:
            available_roles = api.keystone.role_list(request)
            project_members = api.keystone.user_list(request,
                                                     tenant_id=project_id)
            users_to_modify = len(project_members)
            for user in project_members:
                current_roles = [role for role in
                                 api.keystone.roles_for_user(self.request,
                                                             user.id,
                                                             project_id)]
                effective_roles = []
                for role in available_roles:
                    role_list = data["role_" + role.id]
                    if user.id in role_list:
                        effective_roles.append(role)
                        if role not in current_roles:
                            # user role has changed
                            api.keystone.add_tenant_user_role(
                                request,
                                tenant_id=project_id,
                                user_id=user.id,
                                role_id=role.id)
                        else:
                            # user role is unchanged
                            current_roles.pop(current_roles.index(role))
                if user.id == request.user.id and \
                        project_id == request.user.tenant_id and \
                        any(x.name == 'admin' for x in current_roles):
                    # Cannot remove "admin" role on current(admin) project
                    msg = _('You cannot remove the "admin" role from the '
                            'project you are currently logged into. Please '
                            'switch to another project with admin permissions '
                            'or remove the role manually via the CLI')
                    messages.warning(request, msg)
                else:
                    # delete user's removed roles
                    for to_delete in current_roles:
                        api.keystone.remove_tenant_user_role(
                            request,
                            tenant_id=project_id,
                            user_id=user.id,
                            role_id=to_delete.id)
                users_to_modify -= 1

            # add new roles to project
            for role in available_roles:
                # count how many users may be added for exception handling
                role_list = data["role_" + role.id]
                users_to_modify += len(role_list)
            for role in available_roles:
                role_list = data["role_" + role.id]
                users_added = 0
                for user_id in role_list:
                    if not filter(lambda x: user_id == x.id, project_members):
                        api.keystone.add_tenant_user_role(request,
                                                          tenant_id=project_id,
                                                          user_id=user_id,
                                                          role_id=role.id)
                    users_added += 1
                users_to_modify -= users_added
        except:
            exceptions.handle(request, _('Failed to modify %s project members '
                                         'and update project quotas.'
                                         % users_to_modify))
            return True

        # update the project quota
        nova_data = dict([(key, data[key]) for key in NOVA_QUOTA_FIELDS])
        try:
            nova.tenant_quota_update(request,
                                     project_id,
                                     **nova_data)

            if is_service_enabled(request, 'volume'):
                cinder_data = dict([(key, data[key]) for key in
                                    CINDER_QUOTA_FIELDS])
                cinder.tenant_quota_update(request,
                                           project_id,
                                           **cinder_data)
            return True
        except:
            exceptions.handle(request, _('Modified project information and '
                                         'members, but unable to modify '
                                         'project quotas.'))
            return True
