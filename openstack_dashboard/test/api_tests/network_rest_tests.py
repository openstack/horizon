# Copyright 2015, Hewlett-Packard Development Company, L.P.
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
import mock

from openstack_dashboard.api.rest import network
from openstack_dashboard.test import helpers as test


class RestNetworkApiSecurityGroupTests(test.TestCase):

    @mock.patch.object(network.api, 'network')
    def test_security_group_detailed(self, client):
        request = self.mock_rest_request()
        client.security_group_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'default'}}),
        ]

        response = network.SecurityGroups().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content,
                         '{"items": [{"name": "default"}]}')
        client.security_group_list.assert_called_once_with(request)
