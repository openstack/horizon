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
import json
import mock

from django.conf import settings

from openstack_dashboard import api
from openstack_dashboard.api.rest import cinder
from openstack_dashboard.test import helpers as test


class CinderRestTestCase(test.TestCase):

    #
    # Volumes
    #
    def test_volumes_get(self):
        self._test_volumes_get(False, {})

    def test_volumes_get_all(self):
        self._test_volumes_get(True, {})

    def test_volumes_get_with_filters(self):
        filters = {'status': 'available'}
        self._test_volumes_get(False, filters)

    @mock.patch.object(cinder.api, 'cinder')
    def _test_volumes_get(self, all, filters, cc):
        if all:
            request = self.mock_rest_request(GET={'all_projects': 'true'})
        else:
            request = self.mock_rest_request(**{'GET': filters})
        cc.volume_list_paged.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ], False, False
        response = cinder.Volumes().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"id": "one"}, {"id": "two"}],
                          "has_more_data": False,
                          "has_prev_data": False})
        if all:
            cc.volume_list_paged.assert_called_once_with(request,
                                                         {'all_tenants': 1})
        else:
            cc.volume_list_paged.assert_called_once_with(request,
                                                         search_opts=filters)

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_get(self, cc):
        request = self.mock_rest_request(**{'GET': {}})
        cc.volume_get.return_value = mock.Mock(
            **{'to_dict.return_value': {'id': 'one'}})
        response = cinder.Volume().get(request, '1')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"id": "one"})
        cc.volume_get.assert_called_once_with(request, '1')

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_create(self, cc):
        mock_body = '''{
            "size": "",
            "name": "",
            "description": "",
            "volume_type": "",
            "snapshot_id": "",
            "metadata": "",
            "image_id": "",
            "availability_zone": "",
            "source_volid": ""
        }'''

        mock_volume_create_response = {
            "size": ""
        }

        mock_post_response = '{"size": ""}'

        request = self.mock_rest_request(POST={}, body=mock_body)
        cc.volume_create.return_value = \
            mock.Mock(**{'to_dict.return_value': mock_volume_create_response})

        response = cinder.Volumes().post(request)

        self.assertStatusCode(response, 201)
        self.assertEqual(response.content.decode("utf-8"), mock_post_response)

    #
    # Volume Types
    #
    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_types_get(self, cc):
        request = self.mock_rest_request(**{'GET': {}})
        cc.VolumeType.return_value = mock.Mock(
            **{'to_dict.return_value': {'id': 'one'}})
        cc.volume_type_list.return_value = [{'id': 'one'}]
        response = cinder.VolumeTypes().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"items": [{"id": "one"}]})
        cc.volume_type_list.assert_called_once_with(request)
        cc.VolumeType.assert_called_once_with({'id': 'one'})

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_type_get(self, cc):
        request = self.mock_rest_request(**{'GET': {}})
        cc.volume_type_get.return_value = {'name': 'one'}
        cc.VolumeType.return_value = mock.Mock(
            **{'to_dict.return_value': {'id': 'one'}})
        response = cinder.VolumeType().get(request, '1')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"id": "one"})
        cc.volume_type_get.assert_called_once_with(request, '1')
        cc.VolumeType.assert_called_once_with({'name': 'one'})

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_type_get_default(self, cc):
        request = self.mock_rest_request(**{'GET': {}})
        cc.volume_type_default.return_value = {'name': 'one'}
        cc.VolumeType.return_value = mock.Mock(
            **{'to_dict.return_value': {'id': 'one'}})
        response = cinder.VolumeType().get(request, 'default')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"id": "one"})
        cc.volume_type_default.assert_called_once_with(request)
        cc.VolumeType.assert_called_once_with({'name': 'one'})

    #
    # Volume Snapshots
    #
    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_snaps_get(self, cc):
        request = self.mock_rest_request(**{'GET': {}})
        cc.volume_snapshot_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ]
        response = cinder.VolumeSnapshots().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"id": "one"}, {"id": "two"}]})
        cc.volume_snapshot_list.assert_called_once_with(request,
                                                        search_opts={})

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_snaps_get_with_filters(self, cc):
        filters = {'status': 'available'}
        request = self.mock_rest_request(**{'GET': dict(filters)})
        cc.volume_snapshot_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ]
        response = cinder.VolumeSnapshots().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"id": "one"}, {"id": "two"}]})
        cc.volume_snapshot_list.assert_called_once_with(request,
                                                        search_opts=filters)

    #
    # Extensions
    #
    @mock.patch.object(cinder.api, 'cinder')
    @mock.patch.object(settings,
                       'OPENSTACK_CINDER_EXTENSIONS_BLACKLIST', ['baz'])
    def _test_extension_list(self, cc):
        request = self.mock_rest_request()
        cc.list_extensions.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'foo'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'bar'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'baz'}}),
        ]
        response = cinder.Extensions().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content,
                         '{"items": [{"name": "foo"}, {"name": "bar"}]}')
        cc.list_extensions.assert_called_once_with(request)

    @mock.patch.object(cinder.api, 'cinder')
    def test_qos_specs_get(self, cc):
        request = self.mock_rest_request(GET={})
        cc.qos_specs_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ]
        response = cinder.QoSSpecs().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content.decode("utf-8"),
                         '{"items": [{"id": "one"}, {"id": "two"}]}')
        cc.qos_specs_list.assert_called_once_with(request)

    @mock.patch.object(cinder.api, 'cinder')
    def test_tenant_absolute_limits_get(self, cc):
        request = self.mock_rest_request(GET={})
        cc.tenant_absolute_limits.return_value = \
            {'id': 'one'}
        response = cinder.TenantAbsoluteLimits().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content.decode("utf-8"), '{"id": "one"}')
        cc.tenant_absolute_limits.assert_called_once_with(request)

    #
    # Services
    #

    @test.create_stubs({api.base: ('is_service_enabled',)})
    @mock.patch.object(cinder.api, 'cinder')
    def test_services_get(self, cc):
        request = self.mock_rest_request(GET={})
        cc.service_list.return_value = [mock.Mock(
            binary='binary_1',
            host='host_1',
            zone='zone_1',
            updated_at='updated_at_1',
            status='status_1',
            state='state_1'
        ), mock.Mock(
            binary='binary_2',
            host='host_2',
            zone='zone_2',
            updated_at='updated_at_2',
            status='status_2',
            state='state_2'
        )]
        api.base.is_service_enabled(request, 'volume').AndReturn(True)

        self.mox.ReplayAll()

        response = cinder.Services().get(request)
        self.assertStatusCode(response, 200)
        response_as_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_as_json['items'][0]['id'], 1)
        self.assertEqual(response_as_json['items'][0]['binary'], 'binary_1')
        self.assertEqual(response_as_json['items'][1]['id'], 2)
        self.assertEqual(response_as_json['items'][1]['binary'], 'binary_2')
        cc.service_list.assert_called_once_with(request)

    @test.create_stubs({api.base: ('is_service_enabled',)})
    def test_services_get_disabled(self):
        request = self.mock_rest_request(GET={})

        api.base.is_service_enabled(request, 'volume').AndReturn(False)

        self.mox.ReplayAll()

        response = cinder.Services().get(request)
        self.assertStatusCode(response, 501)
