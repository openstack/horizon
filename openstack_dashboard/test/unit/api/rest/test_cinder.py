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

from openstack_dashboard import api
from openstack_dashboard.api.base import Quota
from openstack_dashboard.api.cinder import VolTypeExtraSpec
from openstack_dashboard.api.rest import cinder
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


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

    @test.create_mocks({api.cinder: ['volume_list_paged']})
    def _test_volumes_get(self, all_, filters):
        if all_:
            request = self.mock_rest_request(GET={'all_projects': 'true'})
        else:
            request = self.mock_rest_request(**{'GET': filters})

        volumes = [self.cinder_volumes.first()]
        self.maxDiff = None
        self.mock_volume_list_paged.return_value = volumes, False, False

        response = cinder.Volumes().get(request)

        self.assertStatusCode(response, 200)
        self.assertEqual({'items': [v.to_dict() for v in volumes],
                          'has_more_data': False,
                          'has_prev_data': False},
                         response.json)
        if all_:
            self.mock_volume_list_paged.assert_called_once_with(
                request, {'all_tenants': 1})
        else:
            self.mock_volume_list_paged.assert_called_once_with(
                request, search_opts=filters)

    @test.create_mocks({api.cinder: ['volume_get']})
    def test_volume_get(self):
        request = self.mock_rest_request(**{'GET': {}})
        vol = self.cinder_volumes.first()
        self.mock_volume_get.return_value = vol

        response = cinder.Volume().get(request, '1')

        self.assertStatusCode(response, 200)
        self.assertEqual(vol.to_dict(), response.json)
        self.mock_volume_get.assert_called_once_with(request, '1')

    @test.create_mocks({api.cinder: ['volume_create']})
    def test_volume_create(self):
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

        request = self.mock_rest_request(POST={}, body=mock_body)
        vol = self.cinder_volumes.first()
        self.mock_volume_create.return_value = vol

        response = cinder.Volumes().post(request)

        self.assertStatusCode(response, 201)
        self.assertEqual(vol.to_dict(), response.json)

    @test.create_mocks({api.cinder: ['volume_get']})
    def test_volume_get_metadata(self):
        request = self.mock_rest_request(**{'GET': {}})
        vol = self.cinder_volumes.first()
        vol._apiresource.metadata = {'foo': 'bar'}
        self.mock_volume_get.return_value = vol

        response = cinder.VolumeMetadata().get(request, '1')

        self.assertStatusCode(response, 200)
        self.assertEqual(vol.to_dict()['metadata'], response.json)
        self.mock_volume_get.assert_called_once_with(request, '1')

    @test.create_mocks({api.cinder: ['volume_set_metadata',
                                     'volume_delete_metadata']})
    def test_volume_update_metadata(self):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, '
                 '"removed": ["c", "d"]}'
        )
        response = cinder.VolumeMetadata().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(b'', response.content)
        self.mock_volume_set_metadata.assert_called_once_with(
            request, '1', {'a': '1', 'b': '2'}
        )
        self.mock_volume_delete_metadata.assert_called_once_with(
            request, '1', ['c', 'd']
        )

    #
    # Volume Types
    #
    @test.create_mocks({api.cinder: ['volume_type_list']})
    def test_volume_types_get(self):
        request = self.mock_rest_request(**{'GET': {}})
        types = self.cinder_volume_types.list()
        self.mock_volume_type_list.return_value = types

        response = cinder.VolumeTypes().get(request)

        self.assertStatusCode(response, 200)
        self.assertEqual([api.cinder.VolumeType(t).to_dict() for t in types],
                         response.json['items'])
        self.mock_volume_type_list.assert_called_once_with(request)

    @test.create_mocks({api.cinder: ['volume_type_get']})
    def test_volume_type_get(self):
        request = self.mock_rest_request(**{'GET': {}})
        type_ = self.cinder_volume_types.first()
        self.mock_volume_type_get.return_value = type_

        response = cinder.VolumeType().get(request, '1')

        self.assertStatusCode(response, 200)
        self.assertEqual(api.cinder.VolumeType(type_).to_dict(),
                         response.json)
        self.mock_volume_type_get.assert_called_once_with(request, '1')

    @test.create_mocks({api.cinder: ['volume_type_default']})
    def test_volume_type_get_default(self):
        request = self.mock_rest_request(**{'GET': {}})
        type_ = self.cinder_volume_types.first()
        self.mock_volume_type_default.return_value = type_

        response = cinder.VolumeType().get(request, 'default')

        self.assertStatusCode(response, 200)
        self.assertEqual(api.cinder.VolumeType(type_).to_dict(),
                         response.json)
        self.mock_volume_type_default.assert_called_once_with(request)

    @test.create_mocks({api.cinder: ['volume_type_extra_get']})
    def test_volume_type_get_metadata(self):
        request = self.mock_rest_request(**{'GET': {}})
        self.mock_volume_type_extra_get.return_value = \
            [VolTypeExtraSpec(1, 'foo', 'bar')]
        response = cinder.VolumeTypeMetadata().get(request, '1')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {'foo': 'bar'})
        self.mock_volume_type_extra_get.assert_called_once_with(request, '1')

    @test.create_mocks({api.cinder: ['volume_type_extra_set',
                                     'volume_type_extra_delete']})
    def test_volume_type_update_metadata(self):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, '
                 '"removed": ["c", "d"]}'
        )
        response = cinder.VolumeTypeMetadata().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(b'', response.content)
        self.mock_volume_type_extra_set.assert_called_once_with(
            request, '1', {'a': '1', 'b': '2'}
        )
        self.mock_volume_type_extra_delete.assert_called_once_with(
            request, '1', ['c', 'd']
        )

    #
    # Volume Snapshots
    #
    @test.create_mocks({api.cinder: ['volume_snapshot_list']})
    def test_volume_snaps_get(self):
        request = self.mock_rest_request(**{'GET': {}})
        snapshots = self.cinder_volume_snapshots.list()
        self.mock_volume_snapshot_list.return_value = snapshots

        response = cinder.VolumeSnapshots().get(request)

        self.assertStatusCode(response, 200)
        self.assertEqual([s.to_dict() for s in snapshots],
                         response.json['items'])
        self.mock_volume_snapshot_list.assert_called_once_with(request,
                                                               search_opts={})

    @test.create_mocks({api.cinder: ['volume_snapshot_list']})
    def test_volume_snaps_get_with_filters(self):
        filters = {'status': 'available'}
        request = self.mock_rest_request(**{'GET': dict(filters)})
        snapshots = self.cinder_volume_snapshots.list()
        self.mock_volume_snapshot_list.return_value = snapshots

        response = cinder.VolumeSnapshots().get(request)

        self.assertStatusCode(response, 200)
        self.assertEqual([s.to_dict() for s in snapshots],
                         response.json['items'])
        self.mock_volume_snapshot_list.assert_called_once_with(
            request, search_opts=filters)

    @test.create_mocks({api.cinder: ['volume_snapshot_get']})
    def test_volume_snapshot_get_metadata(self):
        request = self.mock_rest_request(**{'GET': {}})
        # 4th item contains metadata
        snapshot = self.cinder_volume_snapshots.list()[3]
        # Ensure metadata is contained in test data
        assert 'metadata' in snapshot.to_dict()
        self.mock_volume_snapshot_get.return_value = snapshot

        response = cinder.VolumeSnapshotMetadata().get(request, '1')

        self.assertStatusCode(response, 200)
        self.assertEqual(snapshot.metadata, response.json)
        self.mock_volume_snapshot_get.assert_called_once_with(request, '1')

    @test.create_mocks({api.cinder: ['volume_snapshot_set_metadata',
                                     'volume_snapshot_delete_metadata']})
    def test_volume_snapshot_update_metadata(self):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, '
                 '"removed": ["c", "d"]}'
        )
        self.mock_volume_snapshot_set_metadata.return_value = None
        self.mock_volume_snapshot_delete_metadata.return_value = None
        response = cinder.VolumeSnapshotMetadata().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(b'', response.content)
        self.mock_volume_snapshot_set_metadata.assert_called_once_with(
            request, '1', {'a': '1', 'b': '2'}
        )
        self.mock_volume_snapshot_delete_metadata.assert_called_once_with(
            request, '1', ['c', 'd']
        )

    #
    # Extensions
    #
    @test.create_mocks({api.cinder: ['list_extensions']})
    def test_extension_list(self):
        request = self.mock_rest_request()
        exts = tuple(self.cinder_extensions.list())
        self.mock_list_extensions.return_value = exts

        response = cinder.Extensions().get(request)

        self.assertStatusCode(response, 200)
        self.assertEqual([ext.to_dict() for ext in exts],
                         response.json['items'])
        self.mock_list_extensions.assert_called_once_with(request)

    @test.create_mocks({api.cinder: ['qos_specs_list']})
    def test_qos_specs_get(self):
        request = self.mock_rest_request(GET={})
        qos_specs = self.cinder_qos_specs.list()
        self.mock_qos_specs_list.return_value = qos_specs
        response = cinder.QoSSpecs().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual([spec.to_dict() for spec in qos_specs],
                         response.json['items'])
        self.mock_qos_specs_list.assert_called_once_with(request)

    @test.create_mocks({api.cinder: ['tenant_absolute_limits']})
    def test_tenant_absolute_limits_get(self):
        request = self.mock_rest_request(GET={})
        limits = self.cinder_limits['absolute']
        # Ensure to have float(inf) to test it is handled properly
        limits['maxTotalVolumes'] = float('inf')
        self.mock_tenant_absolute_limits.return_value = limits
        response = cinder.TenantAbsoluteLimits().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(limits, response.json)
        self.mock_tenant_absolute_limits.assert_called_once_with(request)

    #
    # Services
    #

    @test.create_mocks({api.base: ['is_service_enabled'],
                        api.cinder: ['service_list',
                                     'extension_supported']})
    def test_services_get(self):
        request = self.mock_rest_request(GET={})
        services = self.cinder_services.list()
        self.mock_service_list.return_value = services
        self.mock_is_service_enabled.return_value = True
        self.mock_extension_supported.return_value = True

        response = cinder.Services().get(request)

        def _convert_service(service, idx):
            return {'binary': service.binary,
                    'host': service.host,
                    'zone': service.zone,
                    'updated_at': service.updated_at,
                    'status': service.status,
                    'state': service.state,
                    'id': idx + 1}

        self.assertStatusCode(response, 200)
        self.assertEqual([_convert_service(s, i)
                          for i, s in enumerate(services)],
                         response.json['items'])

        self.mock_service_list.assert_called_once_with(request)
        self.mock_is_service_enabled.assert_called_once_with(request, 'volume')
        self.mock_extension_supported.assert_called_once_with(request,
                                                              'Services')

    @test.create_mocks({api.base: ['is_service_enabled']})
    def test_services_get_disabled(self):
        request = self.mock_rest_request(GET={})

        self.mock_is_service_enabled.return_value = False

        response = cinder.Services().get(request)
        self.assertStatusCode(response, 501)
        self.mock_is_service_enabled.assert_called_once_with(request, 'volume')

    @test.create_mocks({api.cinder: ['is_volume_service_enabled',
                                     'default_quota_get']})
    def test_quota_sets_defaults_get_when_service_is_enabled(self):
        self.maxDiff = None
        filters = {'user': {'tenant_id': 'tenant'}}
        request = self.mock_rest_request(**{'GET': dict(filters)})

        self.mock_is_volume_service_enabled.return_value = True
        self.mock_default_quota_get.return_value = [Quota("volumes", 1),
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

        self.mock_is_volume_service_enabled.assert_called_once_with(request)
        self.mock_default_quota_get.assert_called_once_with(
            request, request.user.tenant_id)

    @test.create_mocks({api.cinder: ['is_volume_service_enabled',
                                     'default_quota_get']})
    def test_quota_sets_defaults_get_when_service_is_disabled(self):
        filters = {'user': {'tenant_id': 'tenant'}}
        request = self.mock_rest_request(**{'GET': dict(filters)})

        self.mock_is_volume_service_enabled.return_value = False

        response = cinder.DefaultQuotaSets().get(request)

        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'),
                         '"Service Cinder is disabled."')

        self.mock_is_volume_service_enabled.assert_called_once_with(request)
        self.mock_default_quota_get.assert_not_called()

    @test.create_mocks({api.cinder: ['is_volume_service_enabled',
                                     'default_quota_update']})
    def test_quota_sets_defaults_patch_when_service_is_enabled(self):
        request = self.mock_rest_request(body='''
            {"volumes": "15", "snapshots": "5000",
            "gigabytes": "5"}
        ''')

        self.mock_is_volume_service_enabled.return_value = True
        self.mock_default_quota_update.return_value = None

        response = cinder.DefaultQuotaSets().patch(request)

        self.assertStatusCode(response, 204)
        self.assertEqual(response.content.decode('utf-8'), '')

        self.mock_is_volume_service_enabled.assert_called_once_with(request)
        self.mock_default_quota_update.assert_called_once_with(
            request, volumes='15', snapshots='5000', gigabytes='5')

    @test.create_mocks({api.cinder: ['is_volume_service_enabled',
                                     'default_quota_update']})
    def test_quota_sets_defaults_patch_when_service_is_disabled(self):
        request = self.mock_rest_request(body='''
            {"volumes": "15", "snapshots": "5000",
            "gigabytes": "5"}
        ''')

        self.mock_is_volume_service_enabled.return_value = False

        response = cinder.DefaultQuotaSets().patch(request)

        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'),
                         '"Service Cinder is disabled."')

        self.mock_is_volume_service_enabled.assert_called_once_with(request)
        self.mock_default_quota_update.assert_not_called()

    @test.create_mocks({api.cinder: ['tenant_quota_update',
                                     'is_volume_service_enabled'],
                        quotas: ['get_disabled_quotas']})
    def test_quota_sets_patch(self):
        request = self.mock_rest_request(body='''
            {"volumes": "15", "snapshots": "5000",
             "gigabytes": "5"}
        ''')

        self.mock_get_disabled_quotas.return_value = []
        self.mock_is_volume_service_enabled.return_value = True
        self.mock_tenant_quota_update.return_value = None

        response = cinder.QuotaSets().patch(request, 'spam123')

        self.assertStatusCode(response, 204)
        self.assertEqual(response.content.decode('utf-8'), '')
        self.mock_get_disabled_quotas.assert_called_once_with(request)
        self.mock_is_volume_service_enabled.assert_called_once_with(request)
        self.mock_tenant_quota_update.assert_called_once_with(
            request, 'spam123', volumes='15', snapshots='5000', gigabytes='5')

    @test.create_mocks({api.cinder: ['tenant_quota_update',
                                     'is_volume_service_enabled'],
                        quotas: ['get_disabled_quotas']})
    def test_quota_sets_when_service_is_disabled(self):
        request = self.mock_rest_request(body='''
            {"volumes": "15", "snapshots": "5000",
             "gigabytes": "5"}
        ''')

        self.mock_get_disabled_quotas.return_value = []
        self.mock_is_volume_service_enabled.return_value = False
        self.mock_tenant_quota_update.return_value = None

        response = cinder.QuotaSets().patch(request, 'spam123')

        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'),
                         '"Service Cinder is disabled."')
        self.mock_tenant_quota_update.assert_not_called()
        self.mock_get_disabled_quotas.assert_called_once_with(request)
        self.mock_is_volume_service_enabled.assert_called_once_with(request)

    @test.create_mocks({api.cinder: ['availability_zone_list']})
    def test_availability_zones_get(self):
        request = self.mock_rest_request(GET={})
        az_list = self.cinder_availability_zones.list()
        self.mock_availability_zone_list.return_value = az_list

        response = cinder.AvailabilityZones().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual([az.to_dict() for az in az_list],
                         response.json['items'])
        self.mock_availability_zone_list.assert_called_once_with(
            request, False)
