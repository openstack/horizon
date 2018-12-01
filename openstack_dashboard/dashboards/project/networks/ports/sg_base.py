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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api


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

    @abc.abstractmethod
    def _get_initial_security_groups(self, context):
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
