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
import os

from openstack_dashboard.test.integration_tests import decorators
from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


class TestStacks(helpers.AdminTestCase):
    KEYPAIR_NAME = 'keypair_for_stack'
    STACKS_NAME = helpers.gen_random_resource_name('stack', timestamp=False)
    STACK_TEMPLATE_PATH = os.path.join(
        os.path.dirname(__file__), 'test-data/stack_template')

    def setUp(self):
        super(TestStacks, self).setUp()
        keypair_page = self.home_pg.\
            go_to_compute_accessandsecurity_keypairspage()
        keypair_page.create_keypair(self.KEYPAIR_NAME)
        keypair_page = self.home_pg.\
            go_to_compute_accessandsecurity_keypairspage()
        self.assertTrue(keypair_page.is_keypair_present(self.KEYPAIR_NAME))

        def cleanup():
            keypair_page = self.home_pg.\
                go_to_compute_accessandsecurity_keypairspage()
            keypair_page.delete_keypairs(self.KEYPAIR_NAME)
            keypair_page.find_message_and_dismiss(messages.SUCCESS)

        self.addCleanup(cleanup)

    @decorators.skip_because(bugs=['1584057'])
    @decorators.services_required("heat")
    def test_create_delete_stack(self):
        """tests the stack creation and deletion functionality

        * creates a new stack
        * verifies the stack appears in the stacks table in Create Complete
          state
        * deletes the newly created stack
        * verifies the stack does not appear in the table after deletion
        """
        with open(self.STACK_TEMPLATE_PATH, 'r') as f:
            template = f.read()
        input_template = template.format(self.KEYPAIR_NAME,
                                         self.CONFIG.image.images_list[0],
                                         "public")
        stacks_page = self.home_pg.go_to_orchestration_stackspage()

        stacks_page.create_stack(self.STACKS_NAME, input_template)
        self.assertTrue(
            stacks_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(
            stacks_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(stacks_page.is_stack_present(self.STACKS_NAME))
        self.assertTrue(stacks_page.is_stack_create_complete(self.STACKS_NAME))

        stacks_page.delete_stack(self.STACKS_NAME)
        self.assertTrue(
            stacks_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            stacks_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(stacks_page.is_stack_deleted(self.STACKS_NAME))
