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

from django.conf import settings
import mock

from openstack_dashboard import api
from openstack_dashboard.api.base import Quota
from openstack_dashboard.api.cinder import VolTypeExtraSpec
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
            mock.Mock(**{'to_dict.return_value': {'id': 'test123'}}),
        ], False, False
        cc.Volume.return_value = mock.Mock(
            **{'to_dict.return_value': {"id": "test123"}})
        response = cinder.Volumes().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"id": "test123"}],
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

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_get_metadata(self, cc):
        request = self.mock_rest_request(**{'GET': {}})
        cc.volume_get.return_value = mock.Mock(
            **{'to_dict.return_value': {'id': 'one',
                                        'metadata': {'foo': 'bar'}}})
        response = cinder.VolumeMetadata().get(request, '1')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {'foo': 'bar'})
        cc.volume_get.assert_called_once_with(request, '1')

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_update_metadata(self, cc):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, '
                 '"removed": ["c", "d"]}'
        )
        response = cinder.VolumeMetadata().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(b'', response.content)
        cc.volume_set_metadata.assert_called_once_with(
            request, '1', {'a': '1', 'b': '2'}
        )
        cc.volume_delete_metadata.assert_called_once_with(
            request, '1', ['c', 'd']
        )

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

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_type_get_metadata(self, cc):
        request = self.mock_rest_request(**{'GET': {}})
        cc.volume_type_extra_get = mock.Mock()

        cc.volume_type_extra_get.return_value = \
            [VolTypeExtraSpec(1, 'foo', 'bar')]
        # cc.volume_type_extra_get.side_effect = [{'foo': 'bar'}]
        response = cinder.VolumeTypeMetadata().get(request, '1')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {'foo': 'bar'})
        cc.volume_type_extra_get.assert_called_once_with(request, '1')

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_type_update_metadata(self, cc):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, '
                 '"removed": ["c", "d"]}'
        )
        response = cinder.VolumeTypeMetadata().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(b'', response.content)
        cc.volume_type_extra_set.assert_called_once_with(
            request, '1', {'a': '1', 'b': '2'}
        )
        cc.volume_type_extra_delete.assert_called_once_with(
            request, '1', ['c', 'd']
        )

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

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_snapshot_get_metadata(self, cc):
        request = self.mock_rest_request(**{'GET': {}})
        cc.volume_snapshot_get.return_value = mock.Mock(
            **{'to_dict.return_value': {'id': 'one',
                                        'metadata': {'foo': 'bar'}}})
        response = cinder.VolumeSnapshotMetadata().get(request, '1')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {'foo': 'bar'})
        cc.volume_snapshot_get.assert_called_once_with(request, '1')

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_snapshot_update_metadata(self, cc):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, '
                 '"removed": ["c", "d"]}'
        )
        response = cinder.VolumeSnapshotMetadata().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(b'', response.content)
        cc.volume_snapshot_set_metadata.assert_called_once_with(
            request, '1', {'a': '1', 'b': '2'}
        )
        cc.volume_snapshot_delete_metadata.assert_called_once_with(
            request, '1', ['c', 'd']
        )

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
            {'id': 'one', 'val': float('inf')}
        response = cinder.TenantAbsoluteLimits().get(request)
        self.assertStatusCode(response, 200)
        response_as_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_as_json['id'], 'one')
        self.assertEqual(response_as_json['val'], 1e+999)
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

    @mock.patch.object(cinder.api, 'cinder')
    def test_quota_sets_defaults_get_when_service_is_enabled(self, cc):
        self.maxDiff = None
        filters = {'user': {'tenant_id': 'tenant'}}
        request = self.mock_rest_request(**{'GET': dict(filters)})

        cc.is_service_enabled.return_value = True
        cc.default_quota_get.return_value = [Quota("volumes", 1),
                                             Quota("snapshots", 2),
                                             Quota("gigabytes", 3),
                                             Quota("some_other_1", 100),
                                             Quota("yet_another", 101)]

        response = cinder.DefaultQuotaSets().get(request)

        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items":
                          [{"limit": 1,
                            "display_name": "Volumes", "name": "volumes"},
                           {"limit": 2,
                            "display_name": "Volume Snapshots",
                            "name": "snapshots"},
                           {"limit": 3,
                            "display_name":
                                "Total Size of Volumes and Snapshots (GB)",
                            "name": "gigabytes"},
                           {"limit": 100,
                            "display_name": "Some Other 1",
                            "name": "some_other_1"},
                           {"limit": 101,
                            "display_name": "Yet Another",
                            "name": "yet_another"}]})

        cc.default_quota_get.assert_called_once_with(request,
                                                     request.user.tenant_id)

    @mock.patch.object(cinder.api, 'cinder')
    def test_quota_sets_defaults_get_when_service_is_disabled(self, cc):
        filters = {'user': {'tenant_id': 'tenant'}}
        request = self.mock_rest_request(**{'GET': dict(filters)})

        cc.is_volume_service_enabled.return_value = False

        response = cinder.DefaultQuotaSets().get(request)

        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'),
                         '"Service Cinder is disabled."')

        cc.default_quota_get.assert_not_called()

    @mock.patch.object(cinder.api, 'cinder')
    def test_quota_sets_defaults_patch_when_service_is_enabled(self, cc):
        request = self.mock_rest_request(body='''
            {"volumes": "15", "snapshots": "5000",
            "gigabytes": "5", "cores": "10"}
        ''')

        cc.is_volume_service_enabled.return_value = True

        response = cinder.DefaultQuotaSets().patch(request)

        self.assertStatusCode(response, 204)
        self.assertEqual(response.content.decode('utf-8'), '')

        cc.default_quota_update.assert_called_once_with(request,
                                                        volumes='15',
                                                        snapshots='5000',
                                                        gigabytes='5')

    @mock.patch.object(cinder.api, 'cinder')
    def test_quota_sets_defaults_patch_when_service_is_disabled(self, cc):
        request = self.mock_rest_request(body='''
            {"volumes": "15", "snapshots": "5000",
            "gigabytes": "5", "cores": "10"}
        ''')

        cc.is_volume_service_enabled.return_value = False

        response = cinder.DefaultQuotaSets().patch(request)

        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'),
                         '"Service Cinder is disabled."')

        cc.default_quota_update.assert_not_called()

    @mock.patch.object(cinder.api, 'cinder')
    @mock.patch.object(cinder, 'quotas')
    def test_quota_sets_patch(self, qc, cc):
        quota_set = self.cinder_quotas.list()[0]
        quota_data = {}

        for quota in quota_set:
            quota_data[quota.name] = quota.limit

        request = self.mock_rest_request(body='''
            {"volumes": "15", "snapshots": "5000",
             "gigabytes": "5", "cores": "10"}
        ''')

        qc.get_disabled_quotas.return_value = []
        qc.CINDER_QUOTA_FIELDS = {n for n in quota_data}
        cc.is_volume_service_enabled.return_value = True

        response = cinder.QuotaSets().patch(request, 'spam123')

        self.assertStatusCode(response, 204)
        self.assertEqual(response.content.decode('utf-8'), '')
        cc.tenant_quota_update.assert_called_once_with(request, 'spam123',
                                                       volumes='15',
                                                       snapshots='5000',
                                                       gigabytes='5')

    @mock.patch.object(cinder.api, 'cinder')
    @mock.patch.object(cinder, 'quotas')
    def test_quota_sets_when_service_is_disabled(self, qc, cc):
        quota_set = self.cinder_quotas.list()[0]
        quota_data = {}

        for quota in quota_set:
            quota_data[quota.name] = quota.limit

        request = self.mock_rest_request(body='''
            {"volumes": "15", "snapshots": "5000",
             "gigabytes": "5", "cores": "10"}
        ''')

        qc.get_disabled_quotas.return_value = []
        qc.CINDER_QUOTA_FIELDS = {n for n in quota_data}
        cc.is_volume_service_enabled.return_value = False

        response = cinder.QuotaSets().patch(request, 'spam123')

        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'),
                         '"Service Cinder is disabled."')
        cc.tenant_quota_update.assert_not_called()

    @test.create_stubs({api.base: ('is_service_enabled',)})
    @mock.patch.object(cinder.api, 'cinder')
    def test_availability_zones_get(self, cc):
        request = self.mock_rest_request(GET={})
        mock_az = mock.Mock()
        mock_az.to_dict.return_value = {
            'name': 'cinder',
            'status': 'available'
        }
        cc.availability_zone_list.return_value = [mock_az]
        self.mox.ReplayAll()

        response = cinder.AvailabilityZones().get(request)
        self.assertStatusCode(response, 200)
        response_as_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_as_json['items'][0]['name'], 'cinder')
        cc.availability_zone_list.assert_called_once_with(request, False)
