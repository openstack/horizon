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


from openstack_dashboard.test.integration_tests import decorators
from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


@decorators.services_required("neutron")
class TestNetworks(helpers.TestCase):
    NETWORK_NAME = helpers.gen_random_resource_name("network")
    SUBNET_NAME = helpers.gen_random_resource_name("subnet")

    @property
    def networks_page(self):
        return self.home_pg.go_to_project_network_networkspage()

    def test_private_network_create(self):
        """tests the network creation and deletion functionalities:

        * creates a new private network and a new subnet associated with it
        * verifies the network appears in the networks table as active
        * deletes the newly created network
        * verifies the network does not appear in the table after deletion
        """

        networks_page = self.networks_page

        networks_page.create_network(self.NETWORK_NAME, self.SUBNET_NAME)
        self.assertTrue(
            networks_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            networks_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(networks_page.is_network_present(self.NETWORK_NAME))
        self.assertTrue(networks_page.is_network_active(self.NETWORK_NAME))

        networks_page.delete_network(self.NETWORK_NAME)
        self.assertTrue(
            networks_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            networks_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(networks_page.is_network_present(self.NETWORK_NAME))


@decorators.services_required("neutron")
class TestAdminNetworks(helpers.AdminTestCase, TestNetworks):
    NETWORK_NAME = helpers.gen_random_resource_name("network")
    SUBNET_NAME = helpers.gen_random_resource_name("subnet")

    @property
    def networks_page(self):
        return self.home_pg.go_to_admin_network_networkspage()


@decorators.services_required("neutron")
class TestNetworksPagination(helpers.TestCase):
    NETWORK_NAME = helpers.gen_random_resource_name("network")
    SUBNET_NAME = helpers.gen_random_resource_name("subnet")
    ITEMS_PER_PAGE = 2

    @property
    def networks_page(self):
        return self.home_pg.go_to_project_network_networkspage()

    def setUp(self):
        super().setUp()

        count = 3
        networks_names = ["{0}_{1}".format(self.NETWORK_NAME, i)
                          for i in range(count)]
        networks_page = self.networks_page
        for network_name in networks_names:
            networks_page.create_network(network_name, self.SUBNET_NAME)
            self.assertTrue(
                networks_page.find_message_and_dismiss(messages.SUCCESS))
            self.assertFalse(
                networks_page.find_message_and_dismiss(messages.ERROR))
            self.assertTrue(networks_page.is_network_present(network_name))
            self.assertTrue(networks_page.is_network_active(network_name))
        # we have to get this now, before we change page size
        self.names = networks_page.networks_table.get_column_data(
            name_column=networks_page.NETWORKS_TABLE_NAME_COLUMN)

        self._change_page_size_setting(self.ITEMS_PER_PAGE)

        def cleanup():
            self._change_page_size_setting()
            networks_page = self.networks_page
            for network_name in networks_names:
                networks_page.delete_network(network_name)
                self.assertTrue(
                    networks_page.find_message_and_dismiss(messages.SUCCESS))
                self.assertFalse(
                    networks_page.find_message_and_dismiss(messages.ERROR))
                self.assertFalse(networks_page.is_network_present(network_name))

        self.addCleanup(cleanup)

    def test_networks_pagination(self):
        """This test checks networks pagination

        Steps:
        1) Login to Horizon Dashboard
        2) Go to Project -> Network -> Networks tab and create
        three networks
        3) Navigate to user settings page
        4) Change 'Items Per Page' value to 2
        5) Go to Project -> Network -> Networks tab or
        Admin -> Network -> Networks tab (depends on user)
        6) Check that only 'Next' link is available, only one network is
        available (and it has correct name)
        7) Click 'Next' and check that both 'Prev' and 'Next' links are
        available, only one network is available (and it has correct name)
        8) Click 'Next' and check that only 'Prev' link is available,
        only one network is visible (and it has correct name)
        9) Click 'Prev' and check result (should be the same as for step7)
        10) Click 'Prev' and check result (should be the same as for step6)
        11) Go to user settings page and restore 'Items Per Page'
        12) Delete created networks
        """

        networks_page = self.networks_page
        definitions = []
        i = 0
        total = len(self.names)
        while i < total:
            has_prev = i >= self.ITEMS_PER_PAGE
            has_next = total - i > self.ITEMS_PER_PAGE
            count = (self.ITEMS_PER_PAGE if has_next
                     else total % self.ITEMS_PER_PAGE or self.ITEMS_PER_PAGE)
            definition = {
                'Next': has_next,
                'Prev': has_prev,
                'Count': count,
                'Names': self.names[i:i + count],
            }
            definitions.append(definition)
            networks_page.networks_table.assert_definition(
                definition,
                name_column=networks_page.NETWORKS_TABLE_NAME_COLUMN)
            if has_next:
                networks_page.networks_table.turn_next_page()
            i = i + self.ITEMS_PER_PAGE

        definitions.reverse()
        for definition in definitions:
            networks_page.networks_table.assert_definition(
                definition,
                name_column=networks_page.NETWORKS_TABLE_NAME_COLUMN)
            if definition['Prev']:
                networks_page.networks_table.turn_prev_page()

    def _change_page_size_setting(self, items_per_page=None):
        settings_page = self.home_pg.go_to_settings_usersettingspage()
        if items_per_page:
            settings_page.change_pagesize(items_per_page)
        else:
            settings_page.change_pagesize()
        settings_page.find_message_and_dismiss(messages.SUCCESS)
