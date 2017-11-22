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

from horizon.test import helpers as test
from horizon.utils import functions


class GetConfigValueTests(test.TestCase):
    key = 'key'
    value = 'value'
    requested_url = '/project/instances/'
    int_default = 30
    str_default = 'default'

    def test_bad_session_value(self):
        request = self.factory.get(self.requested_url)
        request.session[self.key] = self.value
        res = functions.get_config_value(request, self.key, self.int_default)
        self.assertEqual(res, self.int_default)

    def test_bad_cookie_value(self):
        request = self.factory.get(self.requested_url)
        if self.key in request.session:
            del request.session[self.key]
        request.COOKIES[self.key] = self.value
        res = functions.get_config_value(request, self.key, self.int_default)
        self.assertEqual(res, self.int_default)

    def test_float_default_value(self):
        default = 30.1
        request = self.factory.get(self.requested_url)
        request.session[self.key] = self.value
        res = functions.get_config_value(request, self.key, default)
        self.assertEqual(res, self.value)

    def test_session_gets_set(self):
        request = self.factory.get(self.requested_url)
        request.session[self.key] = self.value
        functions.get_config_value(request, self.key, self.int_default)
        self.assertEqual(request.session[self.key], self.int_default)

    def test_found_in_session(self):
        request = self.factory.get(self.requested_url)
        request.session[self.key] = self.value
        if request.COOKIES.get(self.key):
            del request.COOKIES[self.key]
        res = functions.get_config_value(request, self.key, self.str_default)
        self.assertEqual(res, self.value)

    def test_found_in_cookie(self):
        request = self.factory.get(self.requested_url)
        if request.session.get(self.key):
            del request.session[self.key]
        request.COOKIES[self.key] = self.value
        res = functions.get_config_value(request, self.key, self.str_default)
        self.assertEqual(res, self.value)

    def test_found_in_config(self):
        key = 'TESTSERVER'
        value = 'http://testserver'
        request = self.factory.get(self.requested_url)
        if request.session.get(key):
            del request.session[key]
        if request.COOKIES.get(key):
            del request.COOKIES[key]
        res = functions.get_config_value(request, key, self.str_default)
        self.assertEqual(res, value)

    def test_return_default(self):
        key = 'NOT FOUND ANYWHERE'
        request = self.factory.get(self.requested_url)
        if request.session.get(key):
            del request.session[key]
        if request.COOKIES.get(key):
            del request.COOKIES[key]
        res = functions.get_config_value(request, key, self.str_default)
        self.assertEqual(res, self.str_default)

    def test_return_default_no_settings(self):
        key = 'TESTSERVER'
        request = self.factory.get(self.requested_url)
        if request.session.get(key):
            del request.session[key]
        if request.COOKIES.get(key):
            del request.COOKIES[key]
        res = functions.get_config_value(request, key, self.str_default,
                                         search_in_settings=False)
        self.assertEqual(res, self.str_default)
