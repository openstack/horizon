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

import abc
import logging

from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from openstack_auth import utils

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone
from openstack_dashboard.api import nova
from openstack_dashboard.usage import quotas
from openstack_dashboard.utils import identity

LOG = logging.getLogger(__name__)


INDEX_URL = "horizon:identity:projects:index"
ADD_USER_URL = "horizon:identity:projects:create_user"
PROJECT_USER_MEMBER_SLUG = "update_members"
PROJECT_GROUP_MEMBER_SLUG = "update_group_members"
COMMON_HORIZONTAL_TEMPLATE = "identity/projects/_common_horizontal_form.html"


class CommonQuotaAction(workflows.Action):

    _quota_fields = None

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        disabled_quotas = self.initial['disabled_quotas']
        for field in disabled_quotas:
            if field in self.fields:
                self.fields[field].required = False
                self.fields[field].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        usages = quotas.tenant_quota_usages(
            self.request, tenant_id=self.initial['project_id'],
            targets=tuple(self._quota_fields))
        # Validate the quota values before updating quotas.
        bad_values = []
        for key, value in cleaned_data.items():
            used = usages[key].get('used', 0)
            if value is not None and 0 <= value < used:
                bad_values.append(_('%(used)s %(key)s used') %
                                  {'used': used,
                                   'key': quotas.QUOTA_NAMES.get(key, key)})
        if bad_values:
            value_str = ", ".join(bad_values)
            msg = (_('Quota value(s) cannot be less than the current usage '
                     'value(s): %s.') %
                   value_str)
            raise forms.ValidationError(msg)
        return cleaned_data

    def handle(self, request, context):
        project_id = context['project_id']
        disabled_quotas = context['disabled_quotas']
        data = {key: context[key] for key in
                self._quota_fields - disabled_quotas}
        if data:
            self._tenant_quota_update(request, project_id, data)

    @abc.abstractmethod
    def _tenant_quota_update(self, request, project_id, data):
        pass


class ComputeQuotaAction(CommonQuotaAction):
    instances = forms.IntegerField(min_value=-1, label=_("Instances"))
    cores = forms.IntegerField(min_value=-1, label=_("VCPUs"))
    ram = forms.IntegerField(min_value=-1, label=_("RAM (MB)"))
    metadata_items = forms.IntegerField(min_value=-1,
                                        label=_("Metadata Items"))
    key_pairs = forms.IntegerField(min_value=-1, label=_("Key Pairs"))
    server_groups = forms.IntegerField(min_value=-1, label=_("Server Groups"))
    server_group_members = forms.IntegerField(
        min_value=-1, label=_("Server Group Members"))
    injected_files = forms.IntegerField(min_value=-1,
                                        label=_("Injected Files"))
    injected_file_content_bytes = forms.IntegerField(
        min_value=-1,
        label=_("Injected File Content (Bytes)"))
    injected_file_path_bytes = forms.IntegerField(
        min_value=-1,
        label=_("Length of Injected File Path"))

    _quota_fields = quotas.NOVA_QUOTA_FIELDS

    def _tenant_quota_update(self, request, project_id, data):
        nova.tenant_quota_update(request, project_id, **data)

    class Meta(object):
        name = _("Compute")
        slug = 'update_compute_quotas'
        help_text = _("Set maximum quotas for the project.")
        permissions = ('openstack.roles.admin', 'openstack.services.compute')


class VolumeQuotaAction(CommonQuotaAction):
    volumes = forms.IntegerField(min_value=-1, label=_("Volumes"))
    snapshots = forms.IntegerField(min_value=-1, label=_("Volume Snapshots"))
    gigabytes = forms.IntegerField(
        min_value=-1, label=_("Total Size of Volumes and Snapshots (GiB)"))

    _quota_fields = quotas.CINDER_QUOTA_FIELDS

    def _tenant_quota_update(self, request, project_id, data):
        cinder.tenant_quota_update(request, project_id, **data)

    class Meta(object):
        name = _("Volume")
        slug = 'update_volume_quotas'
        help_text = _("Set maximum quotas for the project.")
        permissions = ('openstack.roles.admin', 'openstack.services.compute')


class NetworkQuotaAction(CommonQuotaAction):
    network = forms.IntegerField(min_value=-1, label=_("Networks"))
    subnet = forms.IntegerField(min_value=-1, label=_("Subnets"))
    port = forms.IntegerField(min_value=-1, label=_("Ports"))
    router = forms.IntegerField(min_value=-1, label=_("Routers"))
    floatingip = forms.IntegerField(min_value=-1, label=_("Floating IPs"))
    security_group = forms.IntegerField(min_value=-1,
                                        label=_("Security Groups"))
    security_group_rule = forms.IntegerField(min_value=-1,
                                             label=_("Security Group Rules"))

    _quota_fields = quotas.NEUTRON_QUOTA_FIELDS

    def _tenant_quota_update(self, request, project_id, data):
        api.neutron.tenant_quota_update(request, project_id, **data)

    class Meta(object):
        name = _("Network")
        slug = 'update_network_quotas'
        help_text = _("Set maximum quotas for the project.")
        permissions = ('openstack.roles.admin', 'openstack.services.compute')


class UpdateComputeQuota(workflows.Step):
    action_class = ComputeQuotaAction
    template_name = COMMON_HORIZONTAL_TEMPLATE
    depends_on = ("project_id", "disabled_quotas")
    contributes = quotas.NOVA_QUOTA_FIELDS

    def allowed(self, request):
        return api.base.is_service_enabled(request, 'compute')


class UpdateVolumeQuota(workflows.Step):
    action_class = VolumeQuotaAction
    template_name = COMMON_HORIZONTAL_TEMPLATE
    depends_on = ("project_id", "disabled_quotas")
    contributes = quotas.CINDER_QUOTA_FIELDS

    def allowed(self, request):
        return cinder.is_volume_service_enabled(request)


class UpdateNetworkQuota(workflows.Step):
    action_class = NetworkQuotaAction
    template_name = COMMON_HORIZONTAL_TEMPLATE
    depends_on = ("project_id", "disabled_quotas")
    contributes = quotas.NEUTRON_QUOTA_FIELDS

    def allowed(self, request):
        return (api.base.is_service_enabled(request, 'network') and
                api.neutron.is_quotas_extension_supported(request))


class UpdateQuota(workflows.Workflow):
    slug = "update_quotas"
    name = _("Edit Quotas")
    finalize_button_name = _("Save")
    success_message = _('Modified quotas of project')
    failure_message = _('Unable to modify quotas of project')
    success_url = "horizon:identity:projects:index"
    default_steps = (UpdateComputeQuota,
                     UpdateVolumeQuota,
                     UpdateNetworkQuota)


class CreateProjectInfoAction(workflows.Action):
    # Hide the domain_id and domain_name by default
    domain_id = forms.CharField(label=_("Domain ID"),
                                required=False,
                                widget=forms.HiddenInput())
    domain_name = forms.CharField(label=_("Domain Name"),
                                  required=False,
                                  widget=forms.HiddenInput())
    name = forms.CharField(label=_("Name"),
                           max_length=64)
    description = forms.CharField(widget=forms.widgets.Textarea(
                                  attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    enabled = forms.BooleanField(label=_("Enabled"),
                                 required=False,
                                 initial=True)

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        readonlyInput = forms.TextInput(attrs={'readonly': 'readonly'})
        self.fields["domain_id"].widget = readonlyInput
        self.fields["domain_name"].widget = readonlyInput
        self.add_extra_fields()

    def add_extra_fields(self):
        # add extra column defined by setting
        EXTRA_INFO = settings.PROJECT_TABLE_EXTRA_INFO
        for key, value in EXTRA_INFO.items():
            form = forms.CharField(label=value, required=False,)
            self.fields[key] = form

    class Meta(object):
        name = _("Project Information")
        help_text = _("Create a project to organize users.")


class CreateProjectInfo(workflows.Step):
    action_class = CreateProjectInfoAction
    template_name = COMMON_HORIZONTAL_TEMPLATE
    contributes = ("domain_id",
                   "domain_name",
                   "project_id",
                   "name",
                   "description",
                   "enabled")

    def __init__(self, workflow):
        super().__init__(workflow)
        EXTRA_INFO = settings.PROJECT_TABLE_EXTRA_INFO
        self.contributes += tuple(EXTRA_INFO.keys())


class UpdateProjectMembersAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        err_msg = _('Unable to retrieve user list. Please try again later.')
        # Use the domain_id from the project
        domain_id = self.initial.get("domain_id", None)

        project_id = ''
        if 'project_id' in self.initial:
            project_id = self.initial['project_id']

        # Get the default role
        try:
            default_role = keystone.get_default_role(self.request)
            # Default role is necessary to add members to a project
            if default_role is None:
                default = settings.OPENSTACK_KEYSTONE_DEFAULT_ROLE
                msg = (_('Could not find default role "%s" in Keystone') %
                       default)
                raise exceptions.NotFound(msg)
        except Exception:
            exceptions.handle(self.request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        default_role_name = self.get_default_role_field_name()
        self.fields[default_role_name] = forms.CharField(required=False)
        self.fields[default_role_name].initial = default_role.id

        # Get list of available users
        all_users = []
        try:
            all_users = api.keystone.user_list(request,
                                               domain=domain_id)
        except Exception:
            exceptions.handle(request, err_msg)
        users_list = [(user.id, user.name) for user in all_users]

        # Get list of roles
        role_list = []
        try:
            role_list = api.keystone.role_list(request)
        except Exception:
            exceptions.handle(request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        for role in role_list:
            field_name = self.get_member_field_name(role.id)
            label = role.name
            self.fields[field_name] = forms.MultipleChoiceField(required=False,
                                                                label=label)
            self.fields[field_name].choices = users_list
            self.fields[field_name].initial = []

        # Figure out users & roles
        if project_id:
            try:
                users_roles = api.keystone.get_project_users_roles(request,
                                                                   project_id)
            except Exception:
                exceptions.handle(request,
                                  err_msg,
                                  redirect=reverse(INDEX_URL))

            for user_id in users_roles:
                roles_ids = users_roles[user_id]
                for role_id in roles_ids:
                    field_name = self.get_member_field_name(role_id)
                    self.fields[field_name].initial.append(user_id)

    class Meta(object):
        name = _("Project Members")
        slug = PROJECT_USER_MEMBER_SLUG


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
            except Exception:
                exceptions.handle(self.workflow.request,
                                  _('Unable to retrieve user list.'))

            post = self.workflow.request.POST
            for role in roles:
                field = self.get_member_field_name(role.id)
                context[field] = post.getlist(field)
        return context


class UpdateProjectGroupsAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        err_msg = _('Unable to retrieve group list. Please try again later.')
        # Use the domain_id from the project
        domain_id = self.initial.get("domain_id", None)
        project_id = ''
        if 'project_id' in self.initial:
            project_id = self.initial['project_id']

        # Get the default role
        try:
            default_role = api.keystone.get_default_role(self.request)
            # Default role is necessary to add members to a project
            if default_role is None:
                default = settings.OPENSTACK_KEYSTONE_DEFAULT_ROLE
                msg = (_('Could not find default role "%s" in Keystone') %
                       default)
                raise exceptions.NotFound(msg)
        except Exception:
            exceptions.handle(self.request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        default_role_name = self.get_default_role_field_name()
        self.fields[default_role_name] = forms.CharField(required=False)
        self.fields[default_role_name].initial = default_role.id

        # Get list of available groups
        all_groups = []
        try:
            all_groups = api.keystone.group_list(request,
                                                 domain=domain_id)
        except Exception:
            exceptions.handle(request, err_msg)
        # some backends (e.g. LDAP) do not provide group names
        groups_list = [
            (group.id, getattr(group, 'name', group.id))
            for group in all_groups]

        # Get list of roles
        role_list = []
        try:
            role_list = api.keystone.role_list(request)
        except Exception:
            exceptions.handle(request,
                              err_msg,
                              redirect=reverse(INDEX_URL))
        for role in role_list:
            field_name = self.get_member_field_name(role.id)
            label = role.name
            self.fields[field_name] = forms.MultipleChoiceField(required=False,
                                                                label=label)
            self.fields[field_name].choices = groups_list
            self.fields[field_name].initial = []

        # Figure out groups & roles
        if project_id:
            try:
                groups_roles = api.keystone.get_project_groups_roles(
                    request, project_id)
            except Exception:
                exceptions.handle(request,
                                  err_msg,
                                  redirect=reverse(INDEX_URL))

            for group_id in groups_roles:
                roles_ids = groups_roles[group_id]
                for role_id in roles_ids:
                    field_name = self.get_member_field_name(role_id)
                    self.fields[field_name].initial.append(group_id)

    class Meta(object):
        name = _("Project Groups")
        slug = PROJECT_GROUP_MEMBER_SLUG


class UpdateProjectGroups(workflows.UpdateMembersStep):
    action_class = UpdateProjectGroupsAction
    available_list_title = _("All Groups")
    members_list_title = _("Project Groups")
    no_available_text = _("No groups found.")
    no_members_text = _("No groups.")

    def contribute(self, data, context):
        if data:
            try:
                roles = api.keystone.role_list(self.workflow.request)
            except Exception:
                exceptions.handle(self.workflow.request,
                                  _('Unable to retrieve role list.'))

            post = self.workflow.request.POST
            for role in roles:
                field = self.get_member_field_name(role.id)
                context[field] = post.getlist(field)
        return context


class CreateProject(workflows.Workflow):
    slug = "create_project"
    name = _("Create Project")
    finalize_button_name = _("Create Project")
    success_message = _('Created new project "%s".')
    failure_message = _('Unable to create project "%s".')
    success_url = "horizon:identity:projects:index"
    default_steps = (CreateProjectInfo,
                     UpdateProjectMembers)

    def __init__(self, request=None, context_seed=None, entry_point=None,
                 *args, **kwargs):
        self.default_steps = (CreateProjectInfo,
                              UpdateProjectMembers,
                              UpdateProjectGroups)
        super().__init__(request=request, context_seed=context_seed,
                         entry_point=entry_point, *args, **kwargs)

    def format_status_message(self, message):
        if "%s" in message:
            return message % self.context.get('name', 'unknown project')
        return message

    def _create_project(self, request, data):
        # create the project
        domain_id = data['domain_id']
        try:
            # add extra information
            EXTRA_INFO = settings.PROJECT_TABLE_EXTRA_INFO
            kwargs = dict((key, data.get(key)) for key in EXTRA_INFO)

            desc = data['description']
            self.object = api.keystone.tenant_create(request,
                                                     name=data['name'],
                                                     description=desc,
                                                     enabled=data['enabled'],
                                                     domain=domain_id,
                                                     **kwargs)
            return self.object
        except exceptions.Conflict:
            msg = _('Project name "%s" is already used.') % data['name']
            self.failure_message = msg
            return
        except Exception:
            exceptions.handle(request, ignore=True)
            return

    def _update_project_members(self, request, data, project_id):
        # update project members
        users_to_add = 0
        try:
            available_roles = api.keystone.role_list(request)
            member_step = self.get_step(PROJECT_USER_MEMBER_SLUG)
            # count how many users are to be added
            for role in available_roles:
                field_name = member_step.get_member_field_name(role.id)
                role_list = data[field_name]
                users_to_add += len(role_list)
            # add new users to project
            for role in available_roles:
                field_name = member_step.get_member_field_name(role.id)
                role_list = data[field_name]
                users_added = 0
                for user in role_list:
                    api.keystone.add_tenant_user_role(request,
                                                      project=project_id,
                                                      user=user,
                                                      role=role.id)
                    users_added += 1
                users_to_add -= users_added
        except Exception:
            group_msg = _(", add project groups")
            exceptions.handle(request,
                              _('Failed to add %(users_to_add)s project '
                                'members%(group_msg)s and set project quotas.')
                              % {'users_to_add': users_to_add,
                                 'group_msg': group_msg})

    def _update_project_groups(self, request, data, project_id):
        # update project groups
        groups_to_add = 0
        try:
            available_roles = api.keystone.role_list(request)
            member_step = self.get_step(PROJECT_GROUP_MEMBER_SLUG)

            # count how many groups are to be added
            for role in available_roles:
                field_name = member_step.get_member_field_name(role.id)
                role_list = data[field_name]
                groups_to_add += len(role_list)
            # add new groups to project
            for role in available_roles:
                field_name = member_step.get_member_field_name(role.id)
                role_list = data[field_name]
                groups_added = 0
                for group in role_list:
                    api.keystone.add_group_role(request,
                                                role=role.id,
                                                group=group,
                                                project=project_id)
                    groups_added += 1
                groups_to_add -= groups_added
        except Exception:
            exceptions.handle(request,
                              _('Failed to add %s project groups '
                                'and update project quotas.')
                              % groups_to_add)

    def handle(self, request, data):
        project = self._create_project(request, data)
        if not project:
            return False
        project_id = project.id
        self._update_project_members(request, data, project_id)
        self._update_project_groups(request, data, project_id)
        return True


class UpdateProjectInfoAction(CreateProjectInfoAction):
    enabled = forms.BooleanField(required=False, label=_("Enabled"))
    domain_name = forms.CharField(label=_("Domain Name"),
                                  required=False,
                                  widget=forms.HiddenInput())

    def __init__(self, request, initial, *args, **kwargs):
        super().__init__(request, initial, *args, **kwargs)
        if initial['project_id'] == request.user.project_id:
            self.fields['enabled'].widget.attrs['disabled'] = True
            self.fields['enabled'].help_text = _(
                'You cannot disable your current project')

    def clean(self):
        cleaned_data = super().clean()
        # NOTE(tsufiev): in case the current project is being edited, its
        # 'enabled' field is disabled to prevent changing the field value
        # which is always `True` for the current project (because the user
        # logged in it). Since Django treats disabled checkbox as providing
        # `False` value even if its initial value is `True`, we need to
        # restore the original `True` value of 'enabled' field here.
        if self.fields['enabled'].widget.attrs.get('disabled', False):
            cleaned_data['enabled'] = True
        return cleaned_data

    class Meta(object):
        name = _("Project Information")
        slug = 'update_info'
        help_text = _("Edit the project details.")


class UpdateProjectInfo(workflows.Step):
    action_class = UpdateProjectInfoAction
    template_name = COMMON_HORIZONTAL_TEMPLATE
    depends_on = ("project_id",)
    contributes = ("domain_id",
                   "domain_name",
                   "name",
                   "description",
                   "enabled")

    def __init__(self, workflow):
        super().__init__(workflow)
        EXTRA_INFO = settings.PROJECT_TABLE_EXTRA_INFO
        self.contributes += tuple(EXTRA_INFO.keys())


class UpdateProject(workflows.Workflow):
    slug = "update_project"
    name = _("Edit Project")
    finalize_button_name = _("Save")
    success_message = _('Modified project "%s".')
    failure_message = _('Unable to modify project "%s".')
    success_url = "horizon:identity:projects:index"
    default_steps = (UpdateProjectInfo,
                     UpdateProjectMembers)

    def __init__(self, request=None, context_seed=None, entry_point=None,
                 *args, **kwargs):
        self.default_steps = (UpdateProjectInfo,
                              UpdateProjectMembers,
                              UpdateProjectGroups)

        super().__init__(request=request, context_seed=context_seed,
                         entry_point=entry_point, *args, **kwargs)

    def format_status_message(self, message):
        if "%s" in message:
            return message % self.context.get('name', 'unknown project')
        return message

    @memoized.memoized_method
    def _get_available_roles(self, request):
        return api.keystone.role_list(request)

    def _update_project(self, request, data):
        """Update project info"""
        domain_id = identity.get_domain_id_for_operation(request)
        try:
            project_id = data['project_id']

            # add extra information
            EXTRA_INFO = settings.PROJECT_TABLE_EXTRA_INFO
            kwargs = dict((key, data.get(key)) for key in EXTRA_INFO)

            return api.keystone.tenant_update(
                request,
                project_id,
                name=data['name'],
                description=data['description'],
                enabled=data['enabled'],
                domain=domain_id,
                **kwargs)
        except exceptions.Conflict:
            msg = _('Project name "%s" is already used.') % data['name']
            self.failure_message = msg
            return
        except Exception as e:
            LOG.debug('Project update failed: %s', e)
            exceptions.handle(request, ignore=True)
            return

    def _add_roles_to_users(self, request, data, project_id, user_id,
                            role_ids, available_roles):
        member_step = self.get_step(PROJECT_USER_MEMBER_SLUG)
        current_role_ids = list(role_ids)

        for role in available_roles:
            field_name = member_step.get_member_field_name(role.id)
            # Check if the user is in the list of users with this role.
            if user_id in data[field_name]:
                # Add it if necessary
                if role.id not in current_role_ids:
                    # user role has changed
                    api.keystone.add_tenant_user_role(
                        request,
                        project=project_id,
                        user=user_id,
                        role=role.id)
                else:
                    # User role is unchanged, so remove it from the
                    # remaining roles list to avoid removing it later.
                    index = current_role_ids.index(role.id)
                    current_role_ids.pop(index)
        return current_role_ids

    def _remove_roles_from_user(self, request, project_id, user_id,
                                current_role_ids):
        for id_to_delete in current_role_ids:
            api.keystone.remove_tenant_user_role(
                request,
                project=project_id,
                user=user_id,
                role=id_to_delete)

    def _is_removing_self_admin_role(self, request, project_id, user_id,
                                     available_roles, current_role_ids):
        is_current_user = user_id == request.user.id
        is_current_project = project_id == request.user.tenant_id
        _admin_roles = utils.get_admin_roles()
        available_admin_role_ids = [role.id for role in available_roles
                                    if role.name.lower() in _admin_roles]
        admin_roles = [role for role in current_role_ids
                       if role in available_admin_role_ids]
        if admin_roles:
            removing_admin = any([role in current_role_ids
                                  for role in admin_roles])
        else:
            removing_admin = False

        if is_current_user and is_current_project and removing_admin:
            # Cannot remove "admin" role on current(admin) project
            msg = _('You cannot revoke your administrative privileges '
                    'from the project you are currently logged into. '
                    'Please switch to another project with '
                    'administrative privileges or remove the '
                    'administrative role manually via the CLI.')
            messages.warning(request, msg)
            return True
        return False

    def _update_project_members(self, request, data, project_id):
        # update project members
        users_to_modify = 0
        # Project-user member step
        member_step = self.get_step(PROJECT_USER_MEMBER_SLUG)
        try:
            # Get our role options
            available_roles = self._get_available_roles(request)
            # Get the users currently associated with this project so we
            # can diff against it.
            users_roles = api.keystone.get_project_users_roles(
                request, project=project_id)
            users_to_modify = len(users_roles)

            # TODO(bpokorny): The following lines are needed to make sure we
            # only modify roles for users who are in the current domain.
            # Otherwise, we'll end up removing roles for users who have roles
            # on the project but aren't in the domain.  For now, Horizon won't
            # support managing roles across domains.  The Keystone CLI
            # supports it, so we may want to add that in the future.
            all_users = api.keystone.user_list(request,
                                               domain=data['domain_id'])
            users_dict = {user.id: user.name for user in all_users}

            for user_id in users_roles:
                # Don't remove roles if the user isn't in the domain
                if user_id not in users_dict:
                    users_to_modify -= 1
                    continue

                # Check if there have been any changes in the roles of
                # Existing project members.
                current_role_ids = list(users_roles[user_id])
                modified_role_ids = self._add_roles_to_users(
                    request, data, project_id, user_id,
                    current_role_ids, available_roles)
                # Prevent admins from doing stupid things to themselves.
                removing_admin = self._is_removing_self_admin_role(
                    request, project_id, user_id, available_roles,
                    modified_role_ids)
                # Otherwise go through and revoke any removed roles.
                if not removing_admin:
                    self._remove_roles_from_user(request, project_id, user_id,
                                                 modified_role_ids)
                users_to_modify -= 1

            # Grant new roles on the project.
            for role in available_roles:
                field_name = member_step.get_member_field_name(role.id)
                # Count how many users may be added for exception handling.
                users_to_modify += len(data[field_name])
            for role in available_roles:
                users_added = 0
                field_name = member_step.get_member_field_name(role.id)
                for user_id in data[field_name]:
                    if user_id not in users_roles:
                        api.keystone.add_tenant_user_role(request,
                                                          project=project_id,
                                                          user=user_id,
                                                          role=role.id)
                    users_added += 1
                users_to_modify -= users_added
            return True
        except Exception:
            group_msg = _(", update project groups")
            exceptions.handle(request,
                              _('Failed to modify %(users_to_modify)s'
                                ' project members%(group_msg)s and '
                                'update project quotas.')
                              % {'users_to_modify': users_to_modify,
                                 'group_msg': group_msg})
            return False

    def _update_project_groups(self, request, data, project_id, domain_id):
        # update project groups
        groups_to_modify = 0
        member_step = self.get_step(PROJECT_GROUP_MEMBER_SLUG)
        try:
            available_roles = self._get_available_roles(request)
            # Get the groups currently associated with this project so we
            # can diff against it.
            project_groups = api.keystone.group_list(request,
                                                     domain=domain_id,
                                                     project=project_id)
            groups_to_modify = len(project_groups)
            for group in project_groups:
                # Check if there have been any changes in the roles of
                # Existing project members.
                current_roles = api.keystone.roles_for_group(
                    self.request,
                    group=group.id,
                    project=project_id)
                current_role_ids = [role.id for role in current_roles]
                for role in available_roles:
                    # Check if the group is in the list of groups with
                    # this role.
                    field_name = member_step.get_member_field_name(role.id)
                    if group.id in data[field_name]:
                        # Add it if necessary
                        if role.id not in current_role_ids:
                            # group role has changed
                            api.keystone.add_group_role(
                                request,
                                role=role.id,
                                group=group.id,
                                project=project_id)
                        else:
                            # Group role is unchanged, so remove it from
                            # the remaining roles list to avoid removing it
                            # later.
                            index = current_role_ids.index(role.id)
                            current_role_ids.pop(index)

                # Revoke any removed roles.
                for id_to_delete in current_role_ids:
                    api.keystone.remove_group_role(request,
                                                   role=id_to_delete,
                                                   group=group.id,
                                                   project=project_id)
                groups_to_modify -= 1

            # Grant new roles on the project.
            for role in available_roles:
                field_name = member_step.get_member_field_name(role.id)
                # Count how many groups may be added for error handling.
                groups_to_modify += len(data[field_name])
            for role in available_roles:
                groups_added = 0
                field_name = member_step.get_member_field_name(role.id)
                project_group_ids = [x.id for x in project_groups]
                for group_id in data[field_name]:
                    if group_id not in project_group_ids:
                        api.keystone.add_group_role(request,
                                                    role=role.id,
                                                    group=group_id,
                                                    project=project_id)
                    groups_added += 1
                groups_to_modify -= groups_added
            return True
        except Exception:
            exceptions.handle(request,
                              _('Failed to modify %s project '
                                'members, update project groups '
                                'and update project quotas.')
                              % groups_to_modify)
            return False

    def handle(self, request, data):
        # FIXME(gabriel): This should be refactored to use Python's built-in
        # sets and do this all in a single "roles to add" and "roles to remove"
        # pass instead of the multi-pass thing happening now.

        project = self._update_project(request, data)
        if not project:
            return False

        project_id = data['project_id']
        # Use the domain_id from the project if available
        domain_id = getattr(project, "domain_id", '')

        ret = self._update_project_members(request, data, project_id)
        if not ret:
            return False

        ret = self._update_project_groups(request, data,
                                          project_id, domain_id)
        if not ret:
            return False

        return True
