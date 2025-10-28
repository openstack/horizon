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

from openstack_dashboard.test.integration_tests.pages.project.network \
    import routerspage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class RoutersTable(routerspage.RoutersTable):
    EDIT_ROUTER_FORM_FIELDS = ("name", "admin_state")

    @tables.bind_row_action('update')
    def edit_router(self, edit_button, row):
        edit_button.click()
        return forms.FormRegion(self.driver, self.conf, None,
                                self.EDIT_ROUTER_FORM_FIELDS)


class RoutersPage(routerspage.RoutersPage):

    @property
    def routers_table(self):
        return RoutersTable(self.driver, self.conf)

    def edit_router(self, name, new_name, admin_state=None):
        row = self._get_row_with_router_name(name)
        edit_router_form = self.routers_table.edit_router(row)
        edit_router_form.name.text = new_name
        if admin_state is not None:
            edit_router_form.admin_state.text = admin_state
        edit_router_form.submit()
