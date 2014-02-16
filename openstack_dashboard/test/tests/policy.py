# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
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

from openstack_dashboard import policy
from openstack_dashboard.test import helpers as test


class PolicyTestCase(test.TestCase):
    def test_policy_file_load(self):
        policy.reset()
        enforcer = policy._get_enforcer()
        self.assertEqual(len(enforcer), 2)
        self.assertTrue('identity' in enforcer)
        self.assertTrue('compute' in enforcer)

    def test_policy_reset(self):
        policy._get_enforcer()
        self.assertEqual(len(policy._ENFORCER), 2)
        policy.reset()
        self.assertIsNone(policy._ENFORCER)

    def test_check_admin_required_false(self):
        policy.reset()
        value = policy.check((("identity", "admin_required"),),
                             request=self.request)
        self.assertFalse(value)

    def test_check_identity_rule_not_found_false(self):
        policy.reset()
        value = policy.check((("identity", "i_dont_exist"),),
                             request=self.request)
        # this should fail because the default check for
        # identity is admin_required
        self.assertFalse(value)

    def test_check_nova_context_is_admin_false(self):
        policy.reset()
        value = policy.check((("compute", "context_is_admin"),),
                             request=self.request)
        self.assertFalse(value)

    def test_compound_check_false(self):
        policy.reset()
        value = policy.check((("identity", "admin_required"),
                              ("identity", "identity:default"),),
                             request=self.request)
        self.assertFalse(value)

    def test_scope_not_found(self):
        policy.reset()
        value = policy.check((("dummy", "default"),),
                             request=self.request)
        self.assertTrue(value)


class PolicyTestCaseAdmin(test.BaseAdminViewTests):
    def test_check_admin_required_true(self):
        policy.reset()
        value = policy.check((("identity", "admin_required"),),
                             request=self.request)
        self.assertTrue(value)

    def test_check_identity_rule_not_found_true(self):
        policy.reset()
        value = policy.check((("identity", "i_dont_exist"),),
                             request=self.request)
        # this should succeed because the default check for
        # identity is admin_required
        self.assertTrue(value)

    def test_compound_check_true(self):
        policy.reset()
        value = policy.check((("identity", "admin_required"),
                              ("identity", "identity:default"),),
                             request=self.request)
        self.assertTrue(value)

    def test_check_nova_context_is_admin_true(self):
        policy.reset()
        value = policy.check((("compute", "context_is_admin"),),
                             request=self.request)
        self.assertTrue(value)
