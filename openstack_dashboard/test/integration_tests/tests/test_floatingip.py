# Copyright 2015 Hewlett-Packard Development Company, L.P
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

from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


class TestFloatingip(helpers.TestCase):
    """Checks that the user is able to allocate/release floatingip."""

    def test_floatingip(self):
        floatingip_page = \
            self.home_pg.go_to_compute_accessandsecurity_floatingipspage()
        floating_ip = floatingip_page.allocate_floatingip()
        self.assertTrue(
            floatingip_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            floatingip_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(floatingip_page.is_floatingip_present(floating_ip))

        floatingip_page.release_floatingip(floating_ip)
        self.assertTrue(
            floatingip_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            floatingip_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(floatingip_page.is_floatingip_present(floating_ip))
