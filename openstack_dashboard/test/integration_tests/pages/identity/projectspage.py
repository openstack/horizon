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

from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class ProjectsPage(basepage.BaseNavigationPage):

    _create_project_cancel_button_locator = (
        by.By.CSS_SELECTOR,
        'a.btn.btn-default.secondary.cancel.close')

    _delete_project_submit_button_locator = (
        by.By.CSS_SELECTOR,
        'a.btn.btn-primary')

    _modal_locator = (
        by.By.CSS_SELECTOR,
        'div.modal-backdrop')

    DEFAULT_ENABLED = True
    PROJECTS_TABLE_NAME_COLUMN = 'name'
    PROJECTS_TABLE_NAME = "tenants"
    PROJECTS_TABLE_ACTIONS = ("create", "delete")
    PROJECTS_TABLE_ROW_ACTIONS = {
        tables.ComplexActionRowRegion.PRIMARY_ACTION: "manage_members",
        tables.ComplexActionRowRegion.SECONDARY_ACTIONS: (
            "edit_project",
            "view_usage",
            "modify_quotas",
            "delete_project",
            "set_as_active_project"
        )
    }

    CREATE_PROJECT_FORM_FIELDS = (("name", "description", "enabled"),)

    def __init__(self, driver, conf):
        super(ProjectsPage, self).__init__(driver, conf)
        self._page_title = "Projects"

    @property
    def projects_table(self):
        return tables.ComplexActionTableRegion(self.driver, self.conf,
                                               self.PROJECTS_TABLE_NAME,
                                               self.PROJECTS_TABLE_ACTIONS,
                                               self.PROJECTS_TABLE_ROW_ACTIONS)

    @property
    def create_project_form(self):
        return forms.TabbedFormRegion(self.driver, self.conf, None,
                                      self.CREATE_PROJECT_FORM_FIELDS)

    @property
    def create_project_cancel_button(self):
        return self._get_element(
            *self._create_project_cancel_button_locator)

    @property
    def delete_project_submit_button(self):
        return self._get_element(
            *self._delete_project_submit_button_locator)

    def _get_row_with_project_name(self, name):
        return self.projects_table.get_row(self.PROJECTS_TABLE_NAME_COLUMN,
                                           name)

    def _cancel_popup(self):
        self.create_project_cancel_button.click()

    def switch_project_tab(self, tab_name):
        if tab_name == "information":
            self.create_project_form.tabs.switch_to(0)
        if tab_name == "members":
            self.create_project_form.tabs.switch_to(1)
        if tab_name == "quota":
            self.create_project_form.tabs.switch_to(2)

    def create_project(self, project_name, description=None,
                       is_enabled=DEFAULT_ENABLED):
        self.projects_table.create.click()
        self.create_project_form.name.text = project_name
        if description is not None:
            self.create_project_form.description.text = description
        if not is_enabled:
            self.create_project_form.enabled.unmark()
        self.create_project_form.submit.click()
        self.wait_till_popups_disappear()

    def delete_project(self, project_name):
        row = self._get_row_with_project_name(project_name)
        row.mark()
        self.projects_table.delete.click()
        self.delete_project_submit_button.click()
        self.wait_till_popups_disappear()

    def is_project_present(self, project_name):
        return bool(self._get_row_with_project_name(project_name))

    def delete_from_dropdown_menu(self, project_name):
        row = self._get_row_with_project_name(project_name)
        row.delete_project.click()
        self.delete_project_submit_button.click()
