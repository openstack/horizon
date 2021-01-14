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

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import menus
from openstack_dashboard.test.integration_tests.regions import tables


class ProjectForm(forms.TabbedFormRegion):
    FIELDS = (("name", "description", "enabled"),
              {'members': menus.MembershipMenuRegion})

    def __init__(self, driver, conf, tab=0):
        super().__init__(driver, conf, field_mappings=self.FIELDS,
                         default_tab=tab)


class ProjectsTable(tables.TableRegion):
    name = 'tenants'

    @tables.bind_table_action('create')
    def create_project(self, create_button):
        create_button.click()
        return ProjectForm(self.driver, self.conf)

    @tables.bind_row_action('update')
    def update_members(self, members_button, row):
        members_button.click()
        return ProjectForm(self.driver, self.conf, tab=1)

    @tables.bind_table_action('delete')
    def delete_project(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf, None)


class ProjectsPage(basepage.BaseNavigationPage):

    DEFAULT_ENABLED = True
    PROJECTS_TABLE_NAME_COLUMN = 'Name'
    PROJECT_ID_TABLE_NAME_COLUMN = 'Project ID'

    def __init__(self, driver, conf):
        super().__init__(driver, conf)
        self._page_title = "Projects"

    @property
    def projects_table(self):
        return ProjectsTable(self.driver, self.conf)

    def _get_row_with_project_name(self, name):
        return self.projects_table.get_row(self.PROJECTS_TABLE_NAME_COLUMN,
                                           name)

    def create_project(self, project_name, description=None,
                       is_enabled=DEFAULT_ENABLED):
        create_project_form = self.projects_table.create_project()
        create_project_form.name.text = project_name
        if description is not None:
            create_project_form.description.text = description
        if not is_enabled:
            create_project_form.enabled.unmark()
        create_project_form.submit()

    def delete_project(self, project_name):
        row = self._get_row_with_project_name(project_name)
        row.mark()
        modal_confirmation_form = self.projects_table.delete_project()
        modal_confirmation_form.submit()

    def is_project_present(self, project_name):
        return bool(self._get_row_with_project_name(project_name))

    def get_project_id_from_row(self, name):
        row = self._get_row_with_project_name(name)
        return row.cells[self.PROJECT_ID_TABLE_NAME_COLUMN].text

    def allocate_user_to_project(self, user_name, roles, project_name):
        row = self._get_row_with_project_name(project_name)
        members_form = self.projects_table.update_members(row)
        members_form.members.allocate_member(user_name)
        members_form.members.allocate_member_roles(user_name, roles)
        members_form.submit()

    def get_user_roles_at_project(self, user_name, project_name):
        row = self._get_row_with_project_name(project_name)
        members_form = self.projects_table.update_members(row)
        roles = members_form.members.get_member_allocated_roles(user_name)
        members_form.cancel()
        return set(roles)
