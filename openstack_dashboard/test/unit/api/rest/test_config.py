# Copyright 2015 IBM Corp.
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

from unittest import mock

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class ConfigRestTestCase(test.TestCase):

    @mock.patch.object(api.glance, 'get_image_schemas')
    def test_settings_config_get(self, mock_schemas_list):
        request = self.mock_rest_request()
        response = api.rest.config.Settings().get(request)
        self.assertStatusCode(response, 200)
        self.assertIn(b"REST_API_SETTING_1", response.content)
        self.assertIn(b"REST_API_SETTING_2", response.content)
        self.assertNotIn(b"REST_API_SECURITY", response.content)
