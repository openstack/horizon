# Copyright 2014, Rackspace, US, Inc.
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
import unittest2

from openstack_dashboard.api.rest import utils


class RestUtilsTestCase(unittest2.TestCase):
    def assertStatusCode(self, response, expected_code):
        if response.status_code == expected_code:
            return
        self.fail('status code %r != %r: %s' % (response.status_code,
                                                expected_code,
                                                response.content))

    def _construct_request(self, **args):
        mock_args = {
            'user.is_authenticated.return_value': True,
            'is_ajax.return_value': True,
            'policy.check.return_value': True,
            'body': ''
        }
        mock_args.update(args)
        return mock.Mock(**mock_args)

    def test_api_success(self):
        @utils.ajax()
        def f(self, request):
            return 'ok'
        request = self._construct_request()
        response = f(None, request)
        request.is_authenticated.assert_called_once()
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '"ok"')

    def test_api_success_no_auth_ok(self):
        @utils.ajax(authenticated=False)
        def f(self, request):
            return 'ok'
        request = self._construct_request()
        response = f(None, request)
        request.is_authenticated.assert_not_called_once()
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '"ok"')

    def test_api_auth_required(self):
        @utils.ajax()
        def f(self, request):
            return 'ok'
        request = self._construct_request(**{
            'user.is_authenticated.return_value': False
        })
        response = f(None, request)
        request.is_authenticated.assert_called_once()
        self.assertStatusCode(response, 401)
        self.assertEqual(response.content, '"not logged in"')

    def test_api_success_204(self):
        @utils.ajax()
        def f(self, request):
            pass
        request = self._construct_request()
        response = f(None, request)
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')

    def test_api_error(self):
        @utils.ajax()
        def f(self, request):
            raise utils.AjaxError(500, 'b0rk')
        request = self._construct_request()
        response = f(None, request)
        self.assertStatusCode(response, 500)
        self.assertEqual(response.content, '"b0rk"')

    def test_api_malformed_json(self):
        @utils.ajax()
        def f(self, request):
            assert False, "don't get here"
        request = self._construct_request(**{'body': 'spam'})
        response = f(None, request)
        self.assertStatusCode(response, 400)
        self.assertEqual(response.content, '"malformed JSON request: No JSON '
                         'object could be decoded"')

    def test_api_not_found(self):
        @utils.ajax()
        def f(self, request):
            raise utils.AjaxError(404, 'b0rk')
        request = self._construct_request()
        response = f(None, request)
        self.assertStatusCode(response, 404)
        self.assertEqual(response.content, '"b0rk"')

    def test_post_with_no_data(self):
        @utils.ajax(method='POST')
        def f(self, request):
            assert False, "don't get here"
        request = self._construct_request()
        response = f(None, request)
        self.assertStatusCode(response, 400)
        self.assertEqual(response.content, '"POST requires JSON body"')

    def test_post_with_no_post_action(self):
        self._test_bad_post('data')

    def test_post_with_no_post_data(self):
        self._test_bad_post('action')

    def _test_bad_post(self, arg):
        @utils.ajax(method='POST')
        def f(self, request):
            assert False, "don't get here"
        request = self._construct_request(**{'body': '{"%s": true}' % arg})
        response = f(None, request)
        self.assertStatusCode(response, 400)
        self.assertEqual(response.content, '"POST JSON missing action/data"')

    def test_valid_post(self):
        @utils.ajax(method='POST')
        def f(self, request):
            return 'OK'
        request = self._construct_request(**{'body': '''
            {"action": true, "data": true}
        '''})
        response = f(None, request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '"OK"')

    def test_put_with_no_data(self):
        @utils.ajax(method='PUT')
        def f(self, request):
            assert False, "don't get here"
        request = self._construct_request()
        response = f(None, request)
        self.assertStatusCode(response, 400)
        self.assertEqual(response.content, '"PUT requires JSON body"')

    def test_valid_put(self):
        @utils.ajax(method='PUT')
        def f(self, request):
            return 'OK'
        request = self._construct_request(**{'body': '''
            {"current": true, "update": true}
        '''})
        response = f(None, request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '"OK"')

    def test_api_created_response(self):
        @utils.ajax()
        def f(self, request):
            return utils.CreatedResponse('/api/spam/spam123')
        request = self._construct_request()
        response = f(None, request)
        request.is_authenticated.assert_called_once()
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'], '/api/spam/spam123')
        self.assertEqual(response.content, '')

    def test_api_created_response_content(self):
        @utils.ajax()
        def f(self, request):
            return utils.CreatedResponse('/api/spam/spam123', 'spam!')
        request = self._construct_request()
        response = f(None, request)
        request.is_authenticated.assert_called_once()
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'], '/api/spam/spam123')
        self.assertEqual(response.content, '"spam!"')
