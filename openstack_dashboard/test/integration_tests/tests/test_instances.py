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

INSTANCES_NAME = helpers.gen_random_resource_name('instance',
                                                  timestamp=False)


class TestInstances(helpers.AdminTestCase):
    """This is a basic scenario to test:
    * Create Instance and Terminate Instance
    """

    def test_create_terminate_instance(self):
        instances_page = self.home_pg.go_to_compute_instancespage()
        instances_page.create_instance(INSTANCES_NAME)
        self.assertTrue(instances_page.is_instance_active(INSTANCES_NAME))
        instances_page.terminate_instance(INSTANCES_NAME)
        self.assertTrue(instances_page.is_instance_terminated(INSTANCES_NAME))
