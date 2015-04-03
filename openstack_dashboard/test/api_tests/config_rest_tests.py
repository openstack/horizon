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

import mock

from horizon import conf

from openstack_dashboard.api.rest import config
from openstack_dashboard.test import helpers as test


class ConfigRestTestCase(test.TestCase):
    def assertContains(self, response, expected_content):
        if response.find(expected_content) > 0:
            return
        self.fail('%s does not contain %s' %
                  (response, expected_content))

    def assertNotContains(self, response, expected_content):
        if response.find(expected_content) < 0:
            return
        self.fail('%s contains %s when it should not' %
                  (response, expected_content))

    def test_user_config_get(self):
        user_config = {"modal_backdrop": "static"}
        content = '"modal_backdrop": "static"'
        with mock.patch.dict(conf.HORIZON_CONFIG, user_config):
            request = self.mock_rest_request()
            response = config.DefaultUserConfigs().get(request)
            self.assertStatusCode(response, 200)
            self.assertContains(response.content, content)

    def test_admin_config_get(self):
        admin_config = {"user_home": "somewhere.com"}
        content = '"user_home": "somewhere.com"'
        with mock.patch.dict(conf.HORIZON_CONFIG, admin_config):
            request = self.mock_rest_request()
            response = config.AdminConfigs().get(request)
            self.assertStatusCode(response, 200)
            self.assertContains(response.content, content)

    def test_settings_config_get(self):
        request = self.mock_rest_request()
        response = config.Settings().get(request)
        self.assertStatusCode(response, 200)
        self.assertContains(response.content, "REST_API_SETTING_1")
        self.assertContains(response.content, "REST_API_SETTING_2")
        self.assertNotContains(response.content, "REST_API_SECURITY")

    def test_ignore_list(self):
        ignore_config = {"password_validator": "someobject"}
        content = '"password_validator": "someobject"'
        with mock.patch.dict(conf.HORIZON_CONFIG, ignore_config):
            request = self.mock_rest_request()
            response = config.AdminConfigs().get(request)
            self.assertStatusCode(response, 200)
            self.assertNotContains(response.content, content)
