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
class TestRouters(helpers.TestCase):
    ROUTER_NAME = helpers.gen_random_resource_name("router")

    @property
    def routers_page(self):
        return self.home_pg.go_to_project_network_routerspage()

    def _create_router(self):
        routers_page = self.routers_page

        routers_page.create_router(self.ROUTER_NAME)
        self.assertTrue(
            routers_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(routers_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(routers_page.is_router_present(self.ROUTER_NAME))
        self.assertTrue(routers_page.is_router_active(self.ROUTER_NAME))

    def _delete_router(self):
        routers_page = self.routers_page
        routers_page.delete_router(self.ROUTER_NAME)
        self.assertTrue(
            routers_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(routers_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(routers_page.is_router_present(self.ROUTER_NAME))

    def test_router_create(self):
        """tests the router creation and deletion functionalities:

        * creates a new router for public network
        * verifies the router appears in the routers table as active
        * deletes the newly created router
        * verifies the router does not appear in the table after deletion
        """
        self._create_router()
        self._delete_router()

    def _create_interface(self, interfaces_page):
        interfaces_page.create_interface()
        interface_name = interfaces_page.interfaces_names[0]
        self.assertTrue(
            interfaces_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            interfaces_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(interfaces_page.is_interface_present(interface_name))
        self.assertTrue(interfaces_page.is_interface_status(
            interface_name, 'Down'))

    def _delete_interface(self, interfaces_page, interface_name):
        interfaces_page.delete_interface(interface_name)
        self.assertTrue(
            interfaces_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            interfaces_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(interfaces_page.is_interface_present(interface_name))

    @decorators.skip_because(bugs=['1792028'])
    def test_router_add_delete_interface(self):
        """Tests the router interface creation and deletion functionalities:

        * Follows the steps to create a new router
        * Clicks on the new router name from the routers table
        * Moves to the Interfaces page/tab
        * Adds a new Interface for the first subnet id available
        * Verifies the new interface is in the routers table by checking that
          the interface is present in the table
        * Deletes the newly created interface
        * Verifies the interface is no longer in the interfaces table
        * Switches to the routers view by clicking on the breadcrumb link
        * Follows the steps to delete the router
        """
        self._create_router()

        routers_page = self.routers_page

        router_interfaces_page = routers_page. \
            go_to_interfaces_page(self.ROUTER_NAME)

        self._create_interface(router_interfaces_page)

        interface_name = router_interfaces_page.interfaces_names[0]

        self._delete_interface(router_interfaces_page, interface_name)

        router_interfaces_page.switch_to_routers_page()

        self._delete_router()

    @decorators.skip_because(bugs=['1792028'])
    def test_router_delete_interface_by_row(self):
        """Tests the router interface creation and deletion by row action:

        * Follows the steps to create a new router
        * Clicks on the new router name from the routers table
        * Moves to the Interfaces page/tab
        * Adds a new Interface for the first subnet id available
        * Verifies the new interface is in the routers table
        * Deletes the newly created interface by row action
        * Verifies the interface is no longer in the interfaces table
        * Switches to the routers view by clicking on the breadcrumb link
        * Follows the steps to delete the router
        """
        self._create_router()

        routers_page = self.routers_page

        router_interfaces_page = routers_page. \
            go_to_interfaces_page(self.ROUTER_NAME)

        self._create_interface(router_interfaces_page)

        interface_name = router_interfaces_page.interfaces_names[0]

        router_interfaces_page.delete_interface_by_row_action(interface_name)

        router_interfaces_page.switch_to_routers_page()

        self._delete_router()

    @decorators.skip_because(bugs=['1792028'])
    def test_router_overview_data(self):
        self._create_router()

        routers_page = self.routers_page

        router_overview_page = routers_page.\
            go_to_overview_page(self.ROUTER_NAME)

        self.assertTrue(router_overview_page.
                        is_router_name_present(self.ROUTER_NAME))
        self.assertTrue(router_overview_page.is_router_status("Active"))

        network_overview_page = router_overview_page.go_to_router_network()

        # By default the router is created in the 'public' network so the line
        # below checks that such name is present in the network
        # details/overview page
        self.assertTrue(network_overview_page.is_network_name_present())
        self.assertTrue(network_overview_page.is_network_status("Active"))

        self._delete_router()


class TestAdminRouters(helpers.AdminTestCase):
    ROUTER_NAME = helpers.gen_random_resource_name("router")

    @decorators.skip_because(bugs=['1792028'])
    @decorators.services_required("neutron")
    def test_router_create_admin(self):
        """tests the router creation and deletion functionalities:

        * creates a new router for public network
        * verifies the router appears in the routers table as active
        * edits router name
        * checks router name was updated properly
        * deletes the newly created router
        * verifies the router does not appear in the table after deletion
        """
        routers_page = self.home_pg.go_to_project_network_routerspage()

        routers_page.create_router(self.ROUTER_NAME)
        self.assertTrue(
            routers_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(routers_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(routers_page.is_router_present(self.ROUTER_NAME))
        self.assertTrue(routers_page.is_router_active(self.ROUTER_NAME))

        self.home_pg.go_to_admin_overviewpage()
        admin_routers_page = self.home_pg.go_to_admin_network_routerspage()
        self.assertTrue(routers_page.is_router_present(self.ROUTER_NAME))
        self.assertTrue(routers_page.is_router_active(self.ROUTER_NAME))

        new_name = "edited_" + self.ROUTER_NAME
        admin_routers_page.edit_router(self.ROUTER_NAME, new_name=new_name)
        self.assertTrue(
            admin_routers_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            admin_routers_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(
            admin_routers_page.is_router_present(new_name))
        self.assertTrue(
            admin_routers_page.is_router_active(new_name))

        admin_routers_page.delete_router(new_name)
        self.assertTrue(
            admin_routers_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            admin_routers_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(admin_routers_page.is_router_present(new_name))
