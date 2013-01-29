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


from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

from horizon import exceptions
from horizon import workflows
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.api import cinder, nova
from openstack_dashboard.api.base import is_service_enabled


INDEX_URL = "horizon:projects:instances:index"
ADD_USER_URL = "horizon:projects:instances:create_user"


class UpdateInstanceSecurityGroupsAction(workflows.Action):
    default_role = forms.CharField(required=False)
    role_member = forms.MultipleChoiceField(required=False)

    def __init__(self, request, *args, **kwargs):
        super(UpdateInstanceSecurityGroupsAction, self).__init__(request,
                                                                 *args,
                                                                 **kwargs)
        err_msg = _('Unable to retrieve security group list. '
                    'Please try again later.')
        context = args[0]
        instance_id = context.get('instance_id', '')

        self.fields['default_role'].initial = 'member'

        # Get list of available security groups
        all_groups = []
        try:
            all_groups = api.nova.security_group_list(request)
        except:
            exceptions.handle(request, err_msg)
        groups_list = [(group.name, group.name) for group in all_groups]

        instance_groups = []
        try:
            instance_groups = api.nova.server_security_groups(request,
                                                              instance_id)
        except Exception:
            exceptions.handle(request, err_msg)
        self.fields['role_member'].choices = groups_list
        self.fields['role_member'].initial = [group.name
                                              for group in instance_groups]

    def handle(self, request, data):
        instance_id = data['instance_id']

        # update instance security groups
        wanted_groups = set(data['wanted_groups'])
        try:
            current_groups = api.nova.server_security_groups(request,
                                                             instance_id)
        except:
            exceptions.handle(request, _("Couldn't get current security group "
                                         "list for instance %s."
                                         % instance_id))
            return False

        current_group_names = set(map(lambda g: g.name, current_groups))
        groups_to_add = wanted_groups - current_group_names
        groups_to_remove = current_group_names - wanted_groups

        num_groups_to_modify = len(groups_to_add | groups_to_remove)
        try:
            for group in groups_to_add:
                api.nova.server_add_security_group(request,
                                                   instance_id,
                                                   group)
                num_groups_to_modify -= 1
            for group in groups_to_remove:
                api.nova.server_remove_security_group(request,
                                                      instance_id,
                                                      group)
                num_groups_to_modify -= 1
        except Exception:
            exceptions.handle(request, _('Failed to modify %d instance '
                                         'security groups.'
                                         % num_groups_to_modify))
            return False

        return True

    class Meta:
        name = _("Security Groups")
        slug = "update_security_groups"


class UpdateInstanceSecurityGroups(workflows.UpdateMembersStep):
    action_class = UpdateInstanceSecurityGroupsAction
    help_text = _("From here you can add and remove security groups to "
                  "this project from the list of available security groups.")
    available_list_title = _("All Security Groups")
    members_list_title = _("Instance Security Groups")
    no_available_text = _("No security groups found.")
    no_members_text = _("No security groups enabled.")
    show_roles = False
    depends_on = ("instance_id",)
    contributes = ("wanted_groups",)

    def contribute(self, data, context):
        request = self.workflow.request
        if data:
            context["wanted_groups"] = request.POST.getlist("role_member")
        return context


class UpdateInstanceInfoAction(workflows.Action):
    name = forms.CharField(required=True)

    def handle(self, request, data):
        try:
            api.nova.server_update(request,
                                   data['instance_id'],
                                   data['name'])
        except:
            exceptions.handle(request, ignore=True)
            return False
        return True

    class Meta:
        name = _("Info")
        slug = 'instance_info'
        help_text = _("From here you can edit the instance details.")


class UpdateInstanceInfo(workflows.Step):
    action_class = UpdateInstanceInfoAction
    depends_on = ("instance_id",)
    contributes = ("name",)


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
