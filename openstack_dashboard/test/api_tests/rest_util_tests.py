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
from openstack_dashboard.api.rest import json_encoder
from openstack_dashboard.api.rest import utils
from openstack_dashboard.test import helpers as test


class RestUtilsTestCase(test.TestCase):
    def test_api_success(self):
        @utils.ajax()
        def f(self, request):
            return 'ok'
        request = self.mock_rest_request()
        response = f(None, request)
        request.user.is_authenticated.assert_called_once_with()
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '"ok"')

    def test_api_success_no_auth_ok(self):
        @utils.ajax(authenticated=False)
        def f(self, request):
            return 'ok'
        request = self.mock_rest_request()
        response = f(None, request)
        request.user.is_authenticated.assert_not_called()
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '"ok"')

    def test_api_auth_required(self):
        @utils.ajax()
        def f(self, request):
            return 'ok'
        request = self.mock_rest_request(**{
            'user.is_authenticated.return_value': False
        })
        response = f(None, request)
        request.user.is_authenticated.assert_called_once_with()
        self.assertStatusCode(response, 401)
        self.assertEqual(response.content, '"not logged in"')

    def test_api_success_204(self):
        @utils.ajax()
        def f(self, request):
            pass
        request = self.mock_rest_request()
        response = f(None, request)
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')

    def test_api_error(self):
        @utils.ajax()
        def f(self, request):
            raise utils.AjaxError(500, 'b0rk')
        request = self.mock_rest_request()
        response = f(None, request)
        self.assertStatusCode(response, 500)
        self.assertEqual(response.content, '"b0rk"')

    def test_api_malformed_json(self):
        @utils.ajax()
        def f(self, request):
            assert False, "don't get here"
        request = self.mock_rest_request(**{'body': 'spam'})
        response = f(None, request)
        self.assertStatusCode(response, 400)
        self.assertEqual(response.content, '"malformed JSON request: No JSON '
                         'object could be decoded"')

    def test_api_not_found(self):
        @utils.ajax()
        def f(self, request):
            raise utils.AjaxError(404, 'b0rk')
        request = self.mock_rest_request()
        response = f(None, request)
        self.assertStatusCode(response, 404)
        self.assertEqual(response.content, '"b0rk"')

    def test_data_required_with_no_data(self):
        @utils.ajax(data_required=True)
        def f(self, request):
            assert False, "don't get here"
        request = self.mock_rest_request()
        response = f(None, request)
        self.assertStatusCode(response, 400)
        self.assertEqual(response.content, '"request requires JSON body"')

    def test_valid_data_required(self):
        @utils.ajax(data_required=True)
        def f(self, request):
            return 'OK'
        request = self.mock_rest_request(**{'body': '''
            {"current": true, "update": true}
        '''})
        response = f(None, request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '"OK"')

    def test_api_created_response(self):
        @utils.ajax()
        def f(self, request):
            return utils.CreatedResponse('/api/spam/spam123')
        request = self.mock_rest_request()
        response = f(None, request)
        request.user.is_authenticated.assert_called_once_with()
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'], '/api/spam/spam123')
        self.assertEqual(response.content, '')

    def test_api_created_response_content(self):
        @utils.ajax()
        def f(self, request):
            return utils.CreatedResponse('/api/spam/spam123', 'spam!')
        request = self.mock_rest_request()
        response = f(None, request)
        request.user.is_authenticated.assert_called_once_with()
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'], '/api/spam/spam123')
        self.assertEqual(response.content, '"spam!"')

    def test_parse_filters_keywords(self):
        kwargs = {
            'sort_dir': '1',
            'sort_key': '2',
        }
        filters = {
            'filter1': '1',
            'filter2': '2',
        }

        # Combined
        request_params = dict(kwargs)
        request_params.update(filters)
        request = self.mock_rest_request(**{'GET': dict(request_params)})
        output_filters, output_kwargs = utils.parse_filters_kwargs(
            request, kwargs)
        self.assertDictEqual(kwargs, output_kwargs)
        self.assertDictEqual(filters, output_filters)

        # Empty Filters
        request = self.mock_rest_request(**{'GET': dict(kwargs)})
        output_filters, output_kwargs = utils.parse_filters_kwargs(
            request, kwargs)
        self.assertDictEqual(kwargs, output_kwargs)
        self.assertDictEqual({}, output_filters)

        # Empty keywords
        request = self.mock_rest_request(**{'GET': dict(filters)})
        output_filters, output_kwargs = utils.parse_filters_kwargs(
            request)
        self.assertDictEqual({}, output_kwargs)
        self.assertDictEqual(filters, output_filters)

        # Empty both
        request = self.mock_rest_request(**{'GET': dict()})
        output_filters, output_kwargs = utils.parse_filters_kwargs(
            request)
        self.assertDictEqual({}, output_kwargs)
        self.assertDictEqual({}, output_filters)


class JSONEncoderTestCase(test.TestCase):
    # NOTE(tsufiev): NaN numeric is "conventional" in a sense that the custom
    # NaNJSONEncoder encoder translates it to the same token that the standard
    # JSONEncoder encoder does
    conventional_data = {'key1': 'string', 'key2': 10, 'key4': [1, 'some'],
                         'key5': {'subkey': 7}, 'nanKey': float('nan')}
    data_nan = float('nan')
    data_inf = float('inf')
    data_neginf = -float('inf')

    def test_custom_encoder_on_nan(self):
        @utils.ajax(json_encoder=json_encoder.NaNJSONEncoder)
        def f(self, request):
            return self.data_nan

        request = self.mock_rest_request()
        response = f(self, request)
        request.user.is_authenticated.assert_called_once_with()
        self.assertStatusCode(response, 200)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.content, 'NaN')

    def test_custom_encoder_on_infinity(self):
        @utils.ajax(json_encoder=json_encoder.NaNJSONEncoder)
        def f(self, request):
            return self.data_inf

        request = self.mock_rest_request()
        response = f(self, request)
        request.user.is_authenticated.assert_called_once_with()
        self.assertStatusCode(response, 200)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.content, '1e+999')

    def test_custom_encoder_on_negative_infinity(self):
        @utils.ajax(json_encoder=json_encoder.NaNJSONEncoder)
        def f(self, request):
            return self.data_neginf

        request = self.mock_rest_request()
        response = f(self, request)
        request.user.is_authenticated.assert_called_once_with()
        self.assertStatusCode(response, 200)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.content, '-1e+999')

    def test_custom_encoder_yields_standard_json_for_conventional_data(self):
        @utils.ajax()
        def f(self, request):
            return self.conventional_data

        @utils.ajax(json_encoder=json_encoder.NaNJSONEncoder)
        def g(self, request):
            return self.conventional_data

        request = self.mock_rest_request()
        default_encoder_response = f(self, request)
        custom_encoder_response = g(self, request)

        self.assertEqual(default_encoder_response.content,
                         custom_encoder_response.content)

    def test_custom_encoder_yields_different_json_for_enhanced_data(self):
        @utils.ajax()
        def f(self, request):
            return dict(tuple(self.conventional_data.items()) +
                        (('key3', self.data_inf),))

        @utils.ajax(json_encoder=json_encoder.NaNJSONEncoder)
        def g(self, request):
            return dict(tuple(self.conventional_data.items()) +
                        (('key3', self.data_inf),))

        request = self.mock_rest_request()
        default_encoder_response = f(self, request)
        custom_encoder_response = g(self, request)

        self.assertNotEqual(default_encoder_response.content,
                            custom_encoder_response.content)
