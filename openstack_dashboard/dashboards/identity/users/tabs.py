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


from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.dashboards.identity.users.groups \
    import tables as groups_tables
from openstack_dashboard.dashboards.identity.users.role_assignments \
    import tables as role_assignments_tables


class OverviewTab(tabs.Tab):
    """Overview of the user.

    Global user informations such as user name, domain ID, email...
    """
    name = _("Overview")
    slug = "overview"
    template_name = 'identity/users/_detail_overview.html'

    def get_context_data(self, request):
        return {"user": self.tab_group.kwargs['user']}


class RoleAssignmentsTab(tabs.TableTab):
    """Role assignment of the user to domain/project."""
    table_classes = (role_assignments_tables.RoleAssignmentsTable,)
    name = _("Role assignments")
    slug = "roleassignments"
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def get_roleassignmentstable_data(self):
        user = self.tab_group.kwargs['user']

        try:
            # Get all the roles of the user
            user_roles = api.keystone.role_assignments_list(
                self.request, user=user, include_subtree=False,
                include_names=True)

            return user_roles

        except Exception:
            exceptions.handle(
                self.request,
                _("Unable to display the role assignments of this user."))

        return []


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
