# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.test.utils import override_settings  # noqa
from openstack_auth import policy as policy_backend

from openstack_dashboard.api.rest import policy
from openstack_dashboard.test import helpers as test


class PolicyRestTestCase(test.TestCase):
    @override_settings(POLICY_CHECK_FUNCTION=policy_backend.check)
    def test_policy(self, body='{"rules": []}'):
        request = self.mock_rest_request(body=body)
        response = policy.Policy().post(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '{"allowed": true}')

    @override_settings(POLICY_CHECK_FUNCTION=policy_backend.check)
    def test_rule_alone(self):
        body = '{"rules": [["compute", "compute:get_all" ]]}'
        self.test_policy(body)

    @override_settings(POLICY_CHECK_FUNCTION=policy_backend.check)
    def test_multiple_rule(self):
        body = '{"rules": [["compute", "compute:get_all"],' \
               '           ["compute", "compute:start"]]}'
        self.test_policy(body)

    @override_settings(POLICY_CHECK_FUNCTION=policy_backend.check)
    def test_rule_with_empty_target(self):
        body = '{"rules": [["compute", "compute:get_all"],' \
               '           ["compute", "compute:start"]],' \
               ' "target": {}}'
        self.test_policy(body)

    @override_settings(POLICY_CHECK_FUNCTION=policy_backend.check)
    def test_rule_with_target(self):
        body = '{"rules": [["compute", "compute:get_all"],' \
               '           ["compute", "compute:start"]],' \
               ' "target": {"project_id": "1"}}'
        self.test_policy(body)

    @override_settings(POLICY_CHECK_FUNCTION=policy_backend.check)
    def test_policy_fail(self):
        # admin only rule, default test case user should fail
        request = self.mock_rest_request(
            body='''{"rules": [["compute", "compute:unlock_override"]]}''')
        response = policy.Policy().post(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '{"allowed": false}')

    @override_settings(POLICY_CHECK_FUNCTION=policy_backend.check)
    def test_policy_error(self):
        # admin only rule, default test case user should fail
        request = self.mock_rest_request(
            body='''{"bad": "compute"}''')
        response = policy.Policy().post(request)
        self.assertStatusCode(response, 400)


class AdminPolicyRestTestCase(test.BaseAdminViewTests):
    @override_settings(POLICY_CHECK_FUNCTION=policy_backend.check)
    def test_rule_with_target(self):
        body = '{"rules": [["compute", "compute:unlock_override"]]}'
        request = self.mock_rest_request(body=body)
        response = policy.Policy().post(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '{"allowed": true}')
