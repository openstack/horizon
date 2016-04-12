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


class TestRouters(helpers.TestCase):
    ROUTER_NAME = helpers.gen_random_resource_name("router")

    @decorators.services_required("neutron")
    def test_router_create(self):
        """This test case checks create, clear/set gateway,
            delete router functionality
            executed by non-admin user::
            Steps:
            1. Login to Horizon Dashboard as horizon user
            2. Navigate to Project -> Network -> Routers page
            3. Create new router
            4. Check that the router appears in the routers table as active
            5. Check that no Error messages present
            6. Clear the gateway
            7. Check that the router is still in the routers table
               with no external network
            8. Check that no Error messages present
            9. Set the gateway to 'public' network
            10. Check that no Error messages present
            11. Check that router's external network is set to 'public'
            12. Delete the router
            13. Check that the router is absent in the routers table
            14. Check that no Error messages present
        """

        routers_page = self.home_pg.go_to_network_routerspage()

        routers_page.create_router(self.ROUTER_NAME)
        self.assertTrue(
            routers_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(routers_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(routers_page.is_router_present(self.ROUTER_NAME))
        self.assertTrue(routers_page.is_router_active(self.ROUTER_NAME))

        routers_page.clear_gateway(self.ROUTER_NAME)
        self.assertTrue(
            routers_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(routers_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(routers_page.is_gateway_cleared(self.ROUTER_NAME))

        routers_page.set_gateway(self.ROUTER_NAME)
        self.assertTrue(
            routers_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(routers_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(routers_page.is_gateway_set(self.ROUTER_NAME))

        routers_page.delete_router(self.ROUTER_NAME)
        self.assertTrue(
            routers_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(routers_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(routers_page.is_router_present(self.ROUTER_NAME))
