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
import json
import mock

from openstack_dashboard.api.rest import heat
from openstack_dashboard.test import helpers as test


class ValidateRestTestCase(test.TestCase):
    @mock.patch.object(heat.api, 'heat')
    def test_validate_post(self, hc):
        body = '''{"template_url":"http://localhost/template.yaml"}'''
        request = self.mock_rest_request(body=body)
        hc.template_validate.return_value = ({'Description': 'foo'})
        response = heat.Validate().post(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '{"Description": "foo"}')
        kwargs = json.loads(body)
        hc.template_validate.assert_called_once_with(request, **kwargs)
