#  (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
#
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

from openstack_dashboard import api
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
        self.assertEqual(response.json, {"Description": "foo"})
        kwargs = json.loads(body)
        hc.template_validate.assert_called_once_with(request, **kwargs)


class HeatRestTestCase(test.TestCase):
    #
    # Services
    #

    @test.create_stubs({api.base: ('is_service_enabled',)})
    @mock.patch.object(heat.api, 'heat')
    def test_services_get(self, hc):
        request = self.mock_rest_request(GET={})

        api.base.is_service_enabled(request, 'orchestration').AndReturn(True)

        hc.service_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'to_dict.return_value': {'id': '2'}})
        ]
        self.mox.ReplayAll()

        response = heat.Services().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content.decode('utf-8'),
                         '{"items": [{"id": "1"}, {"id": "2"}]}')
        hc.service_list.assert_called_once_with(request)

    @test.create_stubs({api.base: ('is_service_enabled',)})
    def test_services_get_disabled(self):
        request = self.mock_rest_request(GET={})

        api.base.is_service_enabled(request, 'orchestration').AndReturn(False)

        self.mox.ReplayAll()

        response = heat.Services().get(request)
        self.assertStatusCode(response, 501)
