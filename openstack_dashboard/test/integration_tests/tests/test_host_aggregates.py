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

from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


class TestHostAggregates(helpers.AdminTestCase):
    HOST_AGGREGATE_NAME = helpers.gen_random_resource_name("host_aggregate")
    HOST_AGGREGATE_AVAILABILITY_ZONE = "nova"

    def test_host_aggregate_create(self):
        """tests the host aggregate creation and deletion functionalities:
        * creates a new host aggregate
        * verifies the host aggregate appears in the host aggregates table
        * deletes the newly created host aggregate
        * verifies the host aggregate does not appear in the table
        * after deletion
        """

        hostaggregates_page = self.home_pg.go_to_system_hostaggregatespage()

        hostaggregates_page.create_host_aggregate(
            name=self.HOST_AGGREGATE_NAME,
            availability_zone=self.HOST_AGGREGATE_AVAILABILITY_ZONE)
        self.assertTrue(
            hostaggregates_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(hostaggregates_page.find_message_and_dismiss(
            messages.ERROR))
        self.assertTrue(hostaggregates_page.is_host_aggregate_present(
            self.HOST_AGGREGATE_NAME))

        hostaggregates_page.delete_host_aggregate(self.HOST_AGGREGATE_NAME)
        self.assertTrue(
            hostaggregates_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(hostaggregates_page.find_message_and_dismiss(
            messages.ERROR))
        self.assertFalse(hostaggregates_page.is_host_aggregate_present(
            self.HOST_AGGREGATE_NAME))
