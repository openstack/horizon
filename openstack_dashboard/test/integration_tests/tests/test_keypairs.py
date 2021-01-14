# Copyright 2014 Hewlett-Packard Development Company, L.P
# All Rights Reserved.
#
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
import pytest

from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


class TestKeypair(helpers.TestCase):
    """Checks that the user is able to create/delete keypair."""
    KEYPAIR_NAME = helpers.gen_random_resource_name("keypair")

    @pytest.mark.skip(reason="Bug 1774697")
    def test_keypair(self):
        keypair_page = self.home_pg.\
            go_to_project_compute_keypairspage()
        keypair_page.create_keypair(self.KEYPAIR_NAME)
        self.assertFalse(keypair_page.find_message_and_dismiss(messages.ERROR))

        keypair_page = self.home_pg.\
            go_to_project_compute_keypairspage()
        self.assertTrue(keypair_page.is_keypair_present(self.KEYPAIR_NAME))

        keypair_page.delete_keypair(self.KEYPAIR_NAME)
        self.assertTrue(
            keypair_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(keypair_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(keypair_page.is_keypair_present(self.KEYPAIR_NAME))
