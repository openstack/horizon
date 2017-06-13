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

import random

from openstack_dashboard.test.integration_tests import decorators
from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


@decorators.config_option_required('flavors.panel_type', 'angular',
                                   message="Legacy Panels not tested")
class TestFlavorAngular(helpers.AdminTestCase):
    @property
    def flavors_page(self):
        from openstack_dashboard.test.integration_tests.pages.admin.\
            system.flavorspage import FlavorsPageNG
        self.home_pg.go_to_system_flavorspage()
        return FlavorsPageNG(self.driver, self.CONFIG)

    def test_basic_flavors_browse(self):
        flavors_page = self.flavors_page
        self.assertEqual(flavors_page.header.text, 'Flavors')


@decorators.config_option_required('flavors.panel_type', 'legacy',
                                   message="Angular Panels not tested")
class TestFlavors(helpers.AdminTestCase):
    FLAVOR_NAME = helpers.gen_random_resource_name("flavor")

    def setUp(self):
        super(TestFlavors, self).setUp()
        self.flavors_page = self.home_pg.go_to_system_flavorspage()

    def _create_flavor(self, flavor_name):
        self.flavors_page.create_flavor(
            name=flavor_name,
            vcpus=1,
            ram=1024,
            root_disk=20,
            ephemeral_disk=0,
            swap_disk=0
        )
        self.assertTrue(
            self.flavors_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.flavors_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(
            self.flavors_page.is_flavor_present(self.FLAVOR_NAME))

    def _delete_flavor(self, flavor_name):
        self.flavors_page.delete_flavor_by_row(flavor_name)
        self.assertTrue(
            self.flavors_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.flavors_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(
            self.flavors_page.is_flavor_present(self.FLAVOR_NAME))

    def test_flavor_header(self):
        header_text = self.driver.find_element_by_tag_name('h1').text
        self.assertEqual(header_text, 'Flavors')

    def test_flavor_module_exists(self):
        js_cmd = "$('html').append('<div id=\"testonly\">'"\
            " + angular.module('horizon.app.core.flavors').name"\
            " + '</div>');"
        self.driver.execute_script(js_cmd)
        value = self.driver.find_element_by_id('testonly').text
        self.assertEqual(value, 'horizon.app.core.flavors')

    def test_flavor_create(self):
        """tests the flavor creation and deletion functionalities:

        * creates a new flavor
        * verifies the flavor appears in the flavors table
        * deletes the newly created flavor
        * verifies the flavor does not appear in the table after deletion
        """
        self._create_flavor(self.FLAVOR_NAME)
        self._delete_flavor(self.FLAVOR_NAME)

    def test_flavor_update_info(self):
        """Tests the flavor Edit row action functionality"""

        self._create_flavor(self.FLAVOR_NAME)

        add_up = random.randint(1, 10)
        old_vcpus = self.flavors_page.get_flavor_vcpus(self.FLAVOR_NAME)
        old_ram = self.flavors_page.get_flavor_ram(self.FLAVOR_NAME)
        old_disk = self.flavors_page.get_flavor_disk(self.FLAVOR_NAME)

        self.flavors_page.update_flavor_info(self.FLAVOR_NAME, add_up)

        self.assertTrue(
            self.flavors_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.flavors_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(
            self.flavors_page.is_flavor_present("edited-" + self.FLAVOR_NAME))

        new_vcpus = self.flavors_page.get_flavor_vcpus(
            "edited-" + self.FLAVOR_NAME)
        new_ram = self.flavors_page.get_flavor_ram(
            "edited-" + self.FLAVOR_NAME)
        new_disk = self.flavors_page.get_flavor_disk(
            "edited-" + self.FLAVOR_NAME)

        self.assertIsNot(old_disk, new_disk)
        self.assertIsNot(old_ram, new_ram)
        self.assertIsNot(old_vcpus, new_vcpus)

        self._delete_flavor("edited-" + self.FLAVOR_NAME)

    def test_flavor_update_access(self):
        self._create_flavor(self.FLAVOR_NAME)

        self.flavors_page.update_flavor_access(self.FLAVOR_NAME,
                                               self.HOME_PROJECT)

        self.assertFalse(self.flavors_page.is_flavor_public(self.FLAVOR_NAME))

        self.flavors_page.update_flavor_access(self.FLAVOR_NAME,
                                               self.HOME_PROJECT,
                                               allocate=False)

        self.assertTrue(self.flavors_page.is_flavor_public(self.FLAVOR_NAME))

        self._delete_flavor(self.FLAVOR_NAME)
