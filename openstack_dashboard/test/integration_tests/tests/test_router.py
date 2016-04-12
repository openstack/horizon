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

    def test_router_create(self):
        """tests the router creation and deletion functionalities:
        * creates a new router for public network
        * verifies the router appears in the routers table as active
        * deletes the newly created router
        * verifies the router does not appear in the table after deletion
        """
        routers_page = self.home_pg.go_to_network_routerspage()

        routers_page.create_router(self.ROUTER_NAME)
        self.assertTrue(
            routers_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(routers_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(routers_page.is_router_present(self.ROUTER_NAME))
        self.assertTrue(routers_page.is_router_active(self.ROUTER_NAME))

        routers_page.delete_router(self.ROUTER_NAME)
        self.assertTrue(
            routers_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(routers_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(routers_page.is_router_present(self.ROUTER_NAME))


class TestAdminRouters(helpers.AdminTestCase):
    ROUTER_NAME = helpers.gen_random_resource_name("router")

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
        routers_page = self.home_pg.go_to_network_routerspage()

        routers_page.create_router(self.ROUTER_NAME)
        self.assertTrue(
            routers_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(routers_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(routers_page.is_router_present(self.ROUTER_NAME))
        self.assertTrue(routers_page.is_router_active(self.ROUTER_NAME))

        admin_routers_page = self.home_pg.go_to_system_routerspage()
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
