# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.dashboards.identity.users.groups \
    import tables as groups_tables
from openstack_dashboard.dashboards.identity.users.role_assignments \
    import tables as role_assignments_tables
from openstack_dashboard import policy


LOG = logging.getLogger(__name__)


class OverviewTab(tabs.Tab):
    """Overview of the user.

    Global user informations such as user name, domain ID, email...
    """
    name = _("Overview")
    slug = "overview"
    template_name = 'identity/users/_detail_overview.html'

    def _get_domain_name(self, user):
        domain_name = ''
        if api.keystone.VERSIONS.active >= 3:
            try:
                if policy.check((("identity", "identity:get_domain"),),
                                self.request):
                    domain = api.keystone.domain_get(
                        self.request, user.domain_id)
                    domain_name = domain.name
                else:
                    domain = api.keystone.get_default_domain(self.request)
                    domain_name = domain.get('name')
            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve user domain.'))
        return domain_name

    def _get_project_name(self, user):
        project_id = user.project_id
        if not project_id:
            return
        try:
            tenant = api.keystone.tenant_get(self.request, project_id)
            return tenant.name
        except Exception as e:
            LOG.error('Failed to get tenant %(project_id)s: %(reason)s',
                      {'project_id': project_id, 'reason': e})

    def _get_extras(self, user):
        if api.keystone.VERSIONS.active >= 3:
            extra_info = settings.USER_TABLE_EXTRA_INFO
            return dict((display_key, getattr(user, key, ''))
                        for key, display_key in extra_info.items())
        else:
            return {}

    def get_context_data(self, request):
        user = self.tab_group.kwargs['user']
        return {
            "user": user,
            "domain_name": self._get_domain_name(user),
            'extras': self._get_extras(user),
            'project_name': self._get_project_name(user),
        }


class RoleAssignmentsTab(tabs.TableTab):
    """Role assignment of the user to domain/project."""
    table_classes = (role_assignments_tables.RoleAssignmentsTable,)
    name = _("Role assignments")
    slug = "roleassignments"
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def get_roleassignmentstable_data(self):
        user = self.tab_group.kwargs['user']

        role_assignments = []

        try:
            # Get all the roles of the user
            role_assignments = api.keystone.role_assignments_list(
                self.request, user=user, include_subtree=False,
                include_names=True)

        except Exception:
            exceptions.handle(
                self.request,
                _("Unable to display the role assignments of this user."))
        else:
            # Find all the role assignments through the groups of the user
            try:
                user_groups = api.keystone.group_list(
                    self.request, user=user.id)

                # Get the role for each group of the user:
                for group in user_groups:
                    group_role_assignments = api.keystone. \
                        role_assignments_list(
                            self.request, group=group, include_subtree=False,
                            include_names=True)

                    role_assignments.extend(group_role_assignments)

            except Exception:
                exceptions.handle(
                    self.request,
                    _("Unable to display role assignment through groups."))

        return role_assignments


class GroupsTab(tabs.TableTab):
    """Groups of the user."""
    table_classes = (groups_tables.GroupsTable,)
    name = _("Groups")
    slug = "groups"
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def get_groupstable_data(self):
        user_groups = []
        user = self.tab_group.kwargs['user']

        try:
            user_groups = api.keystone.group_list(self.request, user=user.id)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to display the groups of this user."))

        return user_groups


class UserDetailTabs(tabs.DetailTabsGroup):
    slug = "user_details"
    tabs = (OverviewTab, RoleAssignmentsTab, GroupsTab,)
