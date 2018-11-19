# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django import http
from django import test
import mock

from openstack_auth import policy
from openstack_auth import user
from openstack_auth import utils


class PolicyLoaderTestCase(test.TestCase):
    def test_policy_file_load(self):
        policy.reset()
        enforcer = policy._get_enforcer()
        self.assertEqual(2, len(enforcer))
        self.assertIn('identity', enforcer)
        self.assertIn('compute', enforcer)

    def test_nonexisting_policy_file_load(self):
        policy_files = {
            'dinosaur': 'no_godzilla.json',
        }
        policy.reset()
        with self.settings(POLICY_FILES=policy_files):
            enforcer = policy._get_enforcer()
            self.assertEqual(0, len(enforcer))

    def test_policy_reset(self):
        policy._get_enforcer()
        self.assertEqual(2, len(policy._ENFORCER))
        policy.reset()
        self.assertIsNone(policy._ENFORCER)


class PolicyTestCase(test.TestCase):
    _roles = []

    def setUp(self):
        mock_user = user.User(id=1, roles=self._roles)
        patcher = mock.patch('openstack_auth.utils.get_user',
                             return_value=mock_user)
        self.MockClass = patcher.start()
        self.addCleanup(patcher.stop)
        self.request = http.HttpRequest()


class PolicyTestCaseNonAdmin(PolicyTestCase):
    _roles = [{'id': '1', 'name': 'member'}]

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


class PolicyTestCheckCredentials(PolicyTestCase):
    _roles = [{'id': '1', 'name': 'member'}]

    def setUp(self):
        policy_files = {
            'no_default': 'no_default_policy.json',
            'with_default': 'with_default_policy.json',
        }

        override = self.settings(POLICY_FILES=policy_files)
        override.enable()
        self.addCleanup(override.disable)

        mock_user = user.User(id=1, roles=self._roles,
                              user_domain_id='admin_domain_id')
        patcher = mock.patch('openstack_auth.utils.get_user',
                             return_value=mock_user)
        self.MockClass = patcher.start()
        self.addCleanup(patcher.stop)
        self.request = http.HttpRequest()

    def test_check_credentials(self):
        policy.reset()
        enforcer = policy._get_enforcer()
        scope = enforcer['no_default']
        user = utils.get_user()
        credentials = policy._user_to_credentials(user)
        target = {
            'project_id': user.project_id,
            'tenant_id': user.project_id,
            'user_id': user.id,
            'domain_id': user.user_domain_id,
            'user.domain_id': user.user_domain_id,
            'group.domain_id': user.user_domain_id,
            'project.domain_id': user.user_domain_id,
        }
        is_valid = policy._check_credentials(scope, 'action', target,
                                             credentials)
        self.assertTrue(is_valid)

    def test_check_credentials_default(self):
        policy.reset()
        enforcer = policy._get_enforcer()
        scope = enforcer['with_default']
        user = utils.get_user()
        credentials = policy._user_to_credentials(user)
        target = {
            'project_id': user.project_id,
            'tenant_id': user.project_id,
            'user_id': user.id,
            'domain_id': user.user_domain_id,
            'user.domain_id': user.user_domain_id,
            'group.domain_id': user.user_domain_id,
            'project.domain_id': user.user_domain_id,
        }
        is_valid = policy._check_credentials(scope, 'action', target,
                                             credentials)
        self.assertFalse(is_valid)


class PolicyTestCaseAdmin(PolicyTestCase):
    _roles = [{'id': '1', 'name': 'admin'}]

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


class PolicyTestCaseV3Admin(PolicyTestCase):
    _roles = [{'id': '1', 'name': 'admin'}]

    def setUp(self):
        policy_files = {
            'identity': 'policy.v3cloudsample.json',
            'compute': 'nova_policy.json'}

        override = self.settings(POLICY_FILES=policy_files)
        override.enable()
        self.addCleanup(override.disable)

        mock_user = user.User(id=1, roles=self._roles,
                              user_domain_id='admin_domain_id')
        patcher = mock.patch('openstack_auth.utils.get_user',
                             return_value=mock_user)
        self.MockClass = patcher.start()
        self.addCleanup(patcher.stop)
        self.request = http.HttpRequest()

    def test_check_cloud_admin_required_true(self):
        policy.reset()
        value = policy.check((("identity", "cloud_admin"),),
                             request=self.request)
        self.assertTrue(value)

    def test_check_domain_admin_required_true(self):
        policy.reset()
        value = policy.check((
            ("identity", "admin_and_matching_domain_id"),),
            request=self.request)
        self.assertTrue(value)

    def test_check_any_admin_required_true(self):
        policy.reset()
        value = policy.check((("identity", "admin_or_cloud_admin"),),
                             request=self.request)
        self.assertTrue(value)
