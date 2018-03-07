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
from openstack_dashboard.utils import filters

INDEX_URL = "horizon:projects:instances:index"
ADD_USER_URL = "horizon:projects:instances:create_user"
INSTANCE_SEC_GROUP_SLUG = "update_security_groups"


class BaseSecurityGroupsAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(BaseSecurityGroupsAction, self).__init__(request,
                                                       *args,
                                                       **kwargs)
        err_msg = _('Unable to retrieve security group list. '
                    'Please try again later.')
        context = args[0]

        default_role_name = self.get_default_role_field_name()
        self.fields[default_role_name] = forms.CharField(required=False)
        self.fields[default_role_name].initial = 'member'

        # Get list of available security groups
        all_groups = []
        try:
            # target_tenant_id is required when the form is used as admin.
            # Owner of security group and port should match.
            tenant_id = context.get('target_tenant_id')
            all_groups = api.neutron.security_group_list(request,
                                                         tenant_id=tenant_id)
        except Exception:
            exceptions.handle(request, err_msg)
        groups_list = [(group.id, group.name) for group in all_groups]

        field_name = self.get_member_field_name('member')
        self.fields[field_name] = forms.MultipleChoiceField(required=False)
        self.fields[field_name].choices = groups_list
        sec_groups = []
        try:
            sec_groups = self._get_initial_security_groups(context)
        except Exception:
            exceptions.handle(request, err_msg)
        self.fields[field_name].initial = sec_groups

    def _get_initial_security_groups(self, context):
        # This depends on each cases
        pass

    def handle(self, request, data):
        # This depends on each cases
        pass


class BaseSecurityGroups(workflows.UpdateMembersStep):
    available_list_title = _("All Security Groups")
    no_available_text = _("No security groups found.")
    no_members_text = _("No security groups enabled.")
    show_roles = False
    contributes = ("wanted_groups",)

    def contribute(self, data, context):
        request = self.workflow.request
        if data:
            field_name = self.get_member_field_name('member')
            context["wanted_groups"] = request.POST.getlist(field_name)
        return context


class UpdateInstanceSecurityGroupsAction(BaseSecurityGroupsAction):
    def _get_initial_security_groups(self, context):
        instance_id = context.get('instance_id', '')
        sec_groups = api.neutron.server_security_groups(self.request,
                                                        instance_id)
        return [group.id for group in sec_groups]

    def handle(self, request, data):
        instance_id = data['instance_id']
        wanted_groups = [filters.get_int_or_uuid(sg)
                         for sg in data['wanted_groups']]
        try:
            api.neutron.server_update_security_groups(request, instance_id,
                                                      wanted_groups)
        except Exception as e:
            exceptions.handle(request, str(e))
            return False
        return True

    class Meta(object):
        name = _("Security Groups")
        slug = INSTANCE_SEC_GROUP_SLUG


class UpdateInstanceSecurityGroups(BaseSecurityGroups):
    action_class = UpdateInstanceSecurityGroupsAction
    members_list_title = _("Instance Security Groups")
    help_text = _("Add and remove security groups to this instance "
                  "from the list of available security groups.")
    depends_on = ("instance_id",)

    def allowed(self, request):
        return api.base.is_service_enabled(request, 'network')


class UpdateInstanceInfoAction(workflows.Action):
    name = forms.CharField(label=_("Name"),
                           max_length=255)
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(attrs={'rows': 4}),
        max_length=255,
        required=False
    )

    def __init__(self, request, *args, **kwargs):
        super(UpdateInstanceInfoAction, self).__init__(request,
                                                       *args,
                                                       **kwargs)
        if not api.nova.is_feature_available(request, "instance_description"):
            del self.fields["description"]

    def handle(self, request, data):
        try:
            api.nova.server_update(request,
                                   data['instance_id'],
                                   data['name'],
                                   description=data.get('description'))
        except Exception:
            exceptions.handle(request, ignore=True)
            return False
        return True

    class Meta(object):
        name = _("Information")
        slug = 'instance_info'
        help_text = _("Edit the instance details.")


class UpdateInstanceInfo(workflows.Step):
    action_class = UpdateInstanceInfoAction
    depends_on = ("instance_id",)
    contributes = ("name", "description")


class UpdateInstance(workflows.Workflow):
    slug = "update_instance"
    name = _("Edit Instance")
    finalize_button_name = _("Save")
    success_message = _('Modified instance "%s".')
    failure_message = _('Unable to modify instance "%s".')
    success_url = "horizon:project:instances:index"
    default_steps = (UpdateInstanceInfo,
                     UpdateInstanceSecurityGroups)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown instance')


# NOTE(kspear): nova doesn't support instance security group management
#               by an admin. This isn't really the place for this code,
#               but the other ways of special-casing this are even messier.
class AdminUpdateInstance(UpdateInstance):
    success_url = "horizon:admin:instances:index"
    default_steps = (UpdateInstanceInfo,)
