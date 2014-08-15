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

import random

from openstack_dashboard.test.integration_tests import helpers


class TestKeypair(helpers.TestCase):
    """Checks that the user is able to create/delete keypair."""
    KEYPAIR_NAME = 'horizonkeypair' + str(random.randint(0, 1000))

    def test_keypair(self):
        accesssecurity_page = self.home_pg.go_to_accesssecurity_page()
        keypair_page = accesssecurity_page.go_to_keypair_page()

        keypair_page.create_keypair(self.KEYPAIR_NAME)
        accesssecurity_page = self.home_pg.go_to_accesssecurity_page()
        keypair_page = accesssecurity_page.go_to_keypair_page()
        self.assertTrue(keypair_page.get_keypair_status(self.KEYPAIR_NAME))

        keypair_page.delete_keypair(self.KEYPAIR_NAME)
        self.assertFalse(keypair_page.get_keypair_status(self.KEYPAIR_NAME))
