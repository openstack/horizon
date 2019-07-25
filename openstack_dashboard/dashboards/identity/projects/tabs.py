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

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard import policy

from openstack_dashboard.dashboards.identity.projects.groups \
    import tables as groups_tables
from openstack_dashboard.dashboards.identity.projects.users \
    import tables as users_tables


class OverviewTab(tabs.Tab):
    """Overview of the project. """
    name = _("Overview")
    slug = "overview"
    template_name = 'identity/projects/_detail_overview.html'

    def get_context_data(self, request):
        project = self.tab_group.kwargs['project']
        return {
            "project": project,
            "domain_name": self._get_domain_name(project),
            "extras": self._get_extras(project),
        }

    def _get_domain_name(self, project):
        domain_name = ''
        if api.keystone.VERSIONS.active >= 3:
            try:
                if policy.check((("identity", "identity:get_domain"),),
                                self.request):
                    domain = api.keystone.domain_get(
                        self.request, project.domain_id)
                    domain_name = domain.name
                else:
                    domain = api.keystone.get_default_domain(self.request)
                    domain_name = domain.get('name')
            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve project domain.'))
        return domain_name

    def _get_extras(self, project):
        if api.keystone.VERSIONS.active >= 3:
            extra_info = settings.PROJECT_TABLE_EXTRA_INFO
            return dict((display_key, getattr(project, key, ''))
                        for key, display_key in extra_info.items())
        else:
            return {}


class UsersTab(tabs.TableTab):
    """Display users member of the project. (directly or through a group)."""
    table_classes = (users_tables.UsersTable,)
    name = _("Users")
    slug = "users"
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def _update_user_roles_names_from_roles_id(self, user, users_roles,
                                               roles_list):
        """Add roles names to user.roles, based on users_roles.

        :param user: user to update
        :param users_roles: list of roles ID
        :param roles_list: list of roles obtained with keystone
        """
        user_roles_names = [role.name for role in roles_list
                            if role.id in users_roles]
        current_user_roles_names = set(getattr(user, "roles", []))
        user.roles = list(current_user_roles_names.union(user_roles_names))

    def _get_users_from_project(self, project_id, roles, project_users):
        """Update with users which have role on project NOT through a group.

        :param project_id: ID of the project
        :param roles: list of roles from keystone
        :param project_users: list to be updated with the users found
        """

        # For keystone.user_list project_id is not passed as argument because
        # it is ignored when using admin credentials
        # Get all users (to be able to find user name)
        users = api.keystone.user_list(self.request)
        users = {user.id: user for user in users}

        # Get project_users_roles ({user_id: [role_id_1, role_id_2]})
        project_users_roles = api.keystone.get_project_users_roles(
            self.request,
            project=project_id)

        for user_id in project_users_roles:

            if user_id not in project_users:
                # Add user to the project_users
                project_users[user_id] = users[user_id]
                project_users[user_id].roles = []
                project_users[user_id].roles_from_groups = []

            # Update the project_user role in order to get:
            # project_users[user_id].roles = [role_name1, role_name2]
            self._update_user_roles_names_from_roles_id(
                user=project_users[user_id],
                users_roles=project_users_roles[user_id],
                roles_list=roles
            )

    def _get_users_from_groups(self, project_id, roles, project_users):
        """Update with users which have role on project through a group.

        :param project_id: ID of the project
        :param roles: list of roles from keystone
        :param project_users: list to be updated with the users found
        """

        # For keystone.group_list project_id is not passed as argument because
        # it is ignored when using admin credentials
        # Get all groups (to be able to find group name)
        groups = api.keystone.group_list(self.request)
        group_names = {group.id: group.name for group in groups}

        # Get a dictionary {group_id: [role_id_1, role_id_2]}
        project_groups_roles = api.keystone.get_project_groups_roles(
            self.request,
            project=project_id)

        for group_id in project_groups_roles:
            group_users = api.keystone.user_list(self.request,
                                                 group=group_id)
            group_roles_names = [
                role.name for role in roles
                if role.id in project_groups_roles[group_id]]

            roles_from_group = [(role_name, group_names[group_id])
                                for role_name in group_roles_names]

            for user in group_users:
                if user.id not in project_users:
                    # New user: Add the user to the list
                    project_users[user.id] = user
                    project_users[user.id].roles = []
                    project_users[user.id].roles_from_groups = []

                # Add roles from group
                project_users[user.id].roles_from_groups.extend(
                    roles_from_group)

    def get_userstable_data(self):
        """Get users with roles on the project.

        Roles can be applied directly on the project or through a group.
        """
        project_users = {}
        project = self.tab_group.kwargs['project']

        try:
            # Get all global roles once to avoid multiple requests.
            roles = api.keystone.role_list(self.request)

            # Update project_users with users which have role directly on
            # the project, (NOT through a group)
            self._get_users_from_project(project_id=project.id,
                                         roles=roles,
                                         project_users=project_users)

            # Update project_users with users which have role indirectly on
            # the project, (through a group)
            self._get_users_from_groups(project_id=project.id,
                                        roles=roles,
                                        project_users=project_users)

        except Exception:
            exceptions.handle(self.request,
                              _("Unable to display the users of this project.")
                              )

        return project_users.values()


class GroupsTab(tabs.TableTab):
    """Display groups member of the project. """
    table_classes = (groups_tables.GroupsTable,)
    name = _("Groups")
    slug = "groups"
    template_name = "horizon/common/_detail_table.html"
    preload = False

    def get_groupstable_data(self):
        groups_in_project = []
        project = self.tab_group.kwargs['project']

        try:
            # Get project_groups_roles: {group_id: [role_id_1, role_id_2]}
            project_groups_roles = api.keystone.get_project_groups_roles(
                self.request,
                project=project.id)
            # Get global roles and groups
            roles = api.keystone.role_list(self.request)
            # For keystone.group_list, we do not give the project_id because it
            # is ignored when called with admin creds.
            groups = api.keystone.group_list(self.request)
            groups = {group.id: group for group in groups}
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to display the groups of this"
                                " project."))
        else:
            # Construct Groups list, adding the role attribute
            for group_id in project_groups_roles:
                group = groups[group_id]
                group.roles = [role.name for role in roles
                               if role.id in project_groups_roles[group_id]]
                groups_in_project.append(group)

        return groups_in_project


class ProjectDetailTabs(tabs.DetailTabsGroup):
    slug = "project_details"
    tabs = (OverviewTab, UsersTab, GroupsTab,)
