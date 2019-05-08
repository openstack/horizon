# Copyright 2012 Red Hat, Inc.
#
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

from django.conf import settings
from django.test.utils import override_settings

import cinderclient as cinder_client
import mock

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class CinderApiTests(test.APIMockTestCase):

    def _stub_cinderclient_with_generic_group(self):
        p = mock.patch.object(api.cinder,
                              '_cinderclient_with_generic_groups').start()
        return p.return_value

    @test.create_mocks({
        api.cinder: [
            'cinderclient',
            ('_cinderclient_with_generic_groups', 'cinderclient_groups'),
        ]
    })
    def test_volume_list(self):
        search_opts = {'all_tenants': 1}
        detailed = True

        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()
        cinderclient = self.mock_cinderclient.return_value
        cinderclient_with_group = self.mock_cinderclient_groups.return_value

        volumes_mock = cinderclient_with_group.volumes.list
        volumes_mock.return_value = volumes

        transfers_mock = cinderclient.transfers.list
        transfers_mock.return_value = volume_transfers

        api_volumes = api.cinder.volume_list(self.request,
                                             search_opts=search_opts)

        volumes_mock.assert_called_once_with(search_opts=search_opts)
        transfers_mock.assert_called_once_with(detailed=detailed,
                                               search_opts=search_opts)
        self.assertEqual(len(volumes), len(api_volumes))

    @test.create_mocks({
        api.cinder: [
            'cinderclient',
            ('_cinderclient_with_generic_groups', 'cinderclient_groups'),
        ]
    })
    def test_volume_list_paged(self):
        search_opts = {'all_tenants': 1}
        detailed = True
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()
        cinderclient = self.mock_cinderclient.return_value
        cinderclient_with_group = self.mock_cinderclient_groups.return_value

        volumes_mock = cinderclient_with_group.volumes.list
        volumes_mock.return_value = volumes

        transfers_mock = cinderclient.transfers.list
        transfers_mock.return_value = volume_transfers

        api_volumes, has_more, has_prev = api.cinder.volume_list_paged(
            self.request, search_opts=search_opts)

        volumes_mock.assert_called_once_with(search_opts=search_opts)
        transfers_mock.assert_called_once_with(detailed=detailed,
                                               search_opts=search_opts)
        self.assertEqual(len(volumes), len(api_volumes))
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    @test.create_mocks({
        api.cinder: [
            'cinderclient',
            ('_cinderclient_with_generic_groups', 'cinderclient_groups'),
        ]
    })
    def test_volume_list_paginate_first_page(self):
        api.cinder.VERSIONS._active = None
        page_size = settings.API_RESULT_PAGE_SIZE
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()

        search_opts = {'all_tenants': 1}
        mock_volumes = volumes[:page_size + 1]
        expected_volumes = mock_volumes[:-1]

        cinderclient = self.mock_cinderclient.return_value
        cinderclient_with_group = self.mock_cinderclient_groups.return_value

        volumes_mock = cinderclient_with_group.volumes.list
        volumes_mock.return_value = mock_volumes

        transfers_mock = cinderclient.transfers.list
        transfers_mock.return_value = volume_transfers

        api_volumes, more_data, prev_data = api.cinder.volume_list_paged(
            self.request, search_opts=search_opts, paginate=True)

        volumes_mock.assert_called_once_with(search_opts=search_opts,
                                             limit=page_size + 1,
                                             sort='created_at:desc',
                                             marker=None)
        transfers_mock.assert_called_once_with(detailed=True,
                                               search_opts=search_opts)
        self.assertEqual(len(expected_volumes), len(api_volumes))
        self.assertTrue(more_data)
        self.assertFalse(prev_data)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    @test.create_mocks({
        api.cinder: [
            'cinderclient',
            ('_cinderclient_with_generic_groups', 'cinderclient_groups'),
        ]
    })
    def test_volume_list_paginate_second_page(self):
        api.cinder.VERSIONS._active = None
        page_size = settings.API_RESULT_PAGE_SIZE
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()

        search_opts = {'all_tenants': 1}
        mock_volumes = volumes[page_size:page_size * 2 + 1]
        expected_volumes = mock_volumes[:-1]
        marker = expected_volumes[0].id

        cinderclient = self.mock_cinderclient.return_value
        cinderclient_with_group = self.mock_cinderclient_groups.return_value

        volumes_mock = cinderclient_with_group.volumes.list
        volumes_mock.return_value = mock_volumes

        transfers_mock = cinderclient.transfers.list
        transfers_mock.return_value = volume_transfers

        api_volumes, more_data, prev_data = api.cinder.volume_list_paged(
            self.request, search_opts=search_opts, marker=marker,
            paginate=True)

        volumes_mock.assert_called_once_with(search_opts=search_opts,
                                             limit=page_size + 1,
                                             sort='created_at:desc',
                                             marker=marker)
        transfers_mock.assert_called_once_with(detailed=True,
                                               search_opts=search_opts)
        self.assertEqual(len(expected_volumes), len(api_volumes))
        self.assertTrue(more_data)
        self.assertTrue(prev_data)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    @test.create_mocks({
        api.cinder: [
            'cinderclient',
            ('_cinderclient_with_generic_groups', 'cinderclient_groups'),
        ]
    })
    def test_volume_list_paginate_last_page(self):
        api.cinder.VERSIONS._active = None
        page_size = settings.API_RESULT_PAGE_SIZE
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()

        search_opts = {'all_tenants': 1}
        mock_volumes = volumes[-1 * page_size:]
        expected_volumes = mock_volumes
        marker = expected_volumes[0].id

        cinderclient = self.mock_cinderclient.return_value
        cinderclient_with_group = self.mock_cinderclient_groups.return_value

        volumes_mock = cinderclient_with_group.volumes.list
        volumes_mock.return_value = mock_volumes

        transfers_mock = cinderclient.transfers.list
        transfers_mock.return_value = volume_transfers

        api_volumes, more_data, prev_data = api.cinder.volume_list_paged(
            self.request, search_opts=search_opts, marker=marker,
            paginate=True)

        volumes_mock.assert_called_once_with(search_opts=search_opts,
                                             limit=page_size + 1,
                                             sort='created_at:desc',
                                             marker=marker)
        transfers_mock.assert_called_once_with(detailed=True,
                                               search_opts=search_opts)
        self.assertEqual(len(expected_volumes), len(api_volumes))
        self.assertFalse(more_data)
        self.assertTrue(prev_data)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    @test.create_mocks({
        api.cinder: [
            'cinderclient',
            ('_cinderclient_with_generic_groups', 'cinderclient_groups'),
        ]
    })
    def test_volume_list_paginate_back_from_some_page(self):
        api.cinder.VERSIONS._active = None
        page_size = settings.API_RESULT_PAGE_SIZE
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()

        search_opts = {'all_tenants': 1}
        mock_volumes = volumes[page_size:page_size * 2 + 1]
        expected_volumes = mock_volumes[:-1]
        marker = expected_volumes[0].id

        cinderclient = self.mock_cinderclient.return_value
        cinderclient_with_group = self.mock_cinderclient_groups.return_value

        volumes_mock = cinderclient_with_group.volumes.list
        volumes_mock.return_value = mock_volumes

        transfers_mock = cinderclient.transfers.list
        transfers_mock.return_value = volume_transfers

        api_volumes, more_data, prev_data = api.cinder.volume_list_paged(
            self.request, search_opts=search_opts, sort_dir="asc",
            marker=marker, paginate=True)

        volumes_mock.assert_called_once_with(search_opts=search_opts,
                                             limit=page_size + 1,
                                             sort='created_at:asc',
                                             marker=marker)
        transfers_mock.assert_called_once_with(detailed=True,
                                               search_opts=search_opts)
        self.assertEqual(len(expected_volumes), len(api_volumes))
        self.assertTrue(more_data)
        self.assertTrue(prev_data)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    @test.create_mocks({
        api.cinder: [
            'cinderclient',
            ('_cinderclient_with_generic_groups', 'cinderclient_groups'),
        ]
    })
    def test_volume_list_paginate_back_to_first_page(self):
        api.cinder.VERSIONS._active = None
        page_size = settings.API_RESULT_PAGE_SIZE
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()

        search_opts = {'all_tenants': 1}
        mock_volumes = volumes[:page_size]
        expected_volumes = mock_volumes
        marker = expected_volumes[0].id

        cinderclient = self.mock_cinderclient.return_value
        cinderclient_with_group = self.mock_cinderclient_groups.return_value

        volumes_mock = cinderclient_with_group.volumes.list
        volumes_mock.return_value = mock_volumes

        transfers_mock = cinderclient.transfers.list
        transfers_mock.return_value = volume_transfers

        api_volumes, more_data, prev_data = api.cinder.volume_list_paged(
            self.request, search_opts=search_opts, sort_dir="asc",
            marker=marker, paginate=True)

        volumes_mock.assert_called_once_with(search_opts=search_opts,
                                             limit=page_size + 1,
                                             sort='created_at:asc',
                                             marker=marker)
        transfers_mock.assert_called_once_with(detailed=True,
                                               search_opts=search_opts)
        self.assertEqual(len(expected_volumes), len(api_volumes))
        self.assertTrue(more_data)
        self.assertFalse(prev_data)

    @test.create_mocks({
        api.cinder: [
            ('_cinderclient_with_generic_groups', 'cinderclient_groups'),
        ]
    })
    def test_volume_snapshot_list(self):
        search_opts = {'all_tenants': 1}
        volume_snapshots = self.cinder_volume_snapshots.list()
        cinderclient = self.mock_cinderclient_groups.return_value

        snapshots_mock = cinderclient.volume_snapshots.list
        snapshots_mock.return_value = volume_snapshots

        api.cinder.volume_snapshot_list(self.request, search_opts=search_opts)
        snapshots_mock.assert_called_once_with(search_opts=search_opts)

    @test.create_mocks({
        api.cinder: [
            ('_cinderclient_with_generic_groups', 'cinderclient_groups'),
        ]
    })
    def test_volume_snapshot_list_no_volume_configured(self):
        # remove volume from service catalog
        catalog = self.service_catalog
        for service in catalog:
            if service["type"] == "volume":
                self.service_catalog.remove(service)
        search_opts = {'all_tenants': 1}
        volume_snapshots = self.cinder_volume_snapshots.list()

        cinderclient = self.mock_cinderclient_groups.return_value

        snapshots_mock = cinderclient.volume_snapshots.list
        snapshots_mock.return_value = volume_snapshots

        api.cinder.volume_snapshot_list(self.request, search_opts=search_opts)

        snapshots_mock.assert_called_once_with(search_opts=search_opts)

    @mock.patch.object(api.cinder, 'cinderclient')
    def test_volume_type_list_with_qos_associations(self, mock_cinderclient):
        volume_types = self.cinder_volume_types.list()
        # Due to test data limitations, we can only run this test using
        # one qos spec, which is associated with one volume type.
        # If we use multiple qos specs, the test data will always
        # return the same associated volume type, which is invalid
        # and prevented by the UI.
        qos_specs_full = self.cinder_qos_specs.list()
        qos_specs_only_one = [qos_specs_full[0]]
        associations = self.cinder_qos_spec_associations.list()

        cinderclient = mock_cinderclient.return_value

        volume_types_mock = cinderclient.volume_types.list
        volume_types_mock.return_value = volume_types

        cinderclient.qos_specs.list.return_value = qos_specs_only_one

        qos_associations_mock = cinderclient.qos_specs.get_associations
        qos_associations_mock.return_value = associations

        assoc_vol_types = \
            api.cinder.volume_type_list_with_qos_associations(self.request)
        associate_spec = assoc_vol_types[0].associated_qos_spec

        volume_types_mock.assert_called_once()
        cinderclient.qos_specs.list.assert_called_once()
        qos_associations_mock.assert_called_once_with(qos_specs_only_one[0].id)
        self.assertEqual(associate_spec, qos_specs_only_one[0].name)

    @mock.patch.object(api.cinder, 'cinderclient')
    def test_volume_type_get_with_qos_association(self, mock_cinderclient):
        volume_type = self.cinder_volume_types.first()
        qos_specs_full = self.cinder_qos_specs.list()
        qos_specs_only_one = [qos_specs_full[0]]
        associations = self.cinder_qos_spec_associations.list()

        cinderclient = mock_cinderclient.return_value

        volume_types_mock = cinderclient.volume_types.get
        volume_types_mock.return_value = volume_type

        qos_specs_mock = cinderclient.qos_specs.list
        qos_specs_mock.return_value = qos_specs_only_one

        qos_associations_mock = cinderclient.qos_specs.get_associations
        qos_associations_mock.return_value = associations

        assoc_vol_type = \
            api.cinder.volume_type_get_with_qos_association(self.request,
                                                            volume_type.id)
        associate_spec = assoc_vol_type.associated_qos_spec

        volume_types_mock.assert_called_once_with(volume_type.id)
        qos_specs_mock.assert_called_once()
        qos_associations_mock.assert_called_once_with(qos_specs_only_one[0].id)
        self.assertEqual(associate_spec, qos_specs_only_one[0].name)

    @mock.patch.object(api.cinder, '_cinderclient_with_features')
    def test_absolute_limits_with_negative_values(self, mock_cinderclient):
        values = {"maxTotalVolumes": -1, "totalVolumesUsed": -1}
        expected_results = {"maxTotalVolumes": float("inf"),
                            "totalVolumesUsed": 0}

        class AbsoluteLimit(object):
            def __init__(self, absolute):
                self.absolute = absolute

        class FakeLimit(object):
            def __init__(self, name, value):
                self.name = name
                self.value = value

        fake_limits = [FakeLimit(k, v) for k, v in values.items()]

        cinderclient = mock_cinderclient.return_value
        mock_limit = cinderclient.limits.get
        mock_limit.return_value = AbsoluteLimit(fake_limits)

        ret_val = api.cinder.tenant_absolute_limits(self.request)

        for key in expected_results:
            self.assertEqual(expected_results[key], ret_val[key])

        mock_limit.assert_called_once()
        mock_cinderclient.assert_called_once_with(
            self.request, ['limits_project_id_query'], message=test.IsA(str))

    @mock.patch.object(api.cinder, 'cinderclient')
    def test_pool_list(self, mock_cinderclient):
        pools = self.cinder_pools.list()
        cinderclient = mock_cinderclient.return_value

        cinderclient.pools.list.return_value = pools

        api.cinder.pool_list(self.request, detailed=True)

        cinderclient.pools.list.assert_called_once_with(detailed=True)

    @mock.patch.object(api.cinder, 'cinderclient')
    def test_volume_type_default(self, mock_cinderclient):
        volume_type = self.cinder_volume_types.first()
        cinderclient = mock_cinderclient.return_value

        cinderclient.volume_types.default.return_value = volume_type

        default_volume_type = api.cinder.volume_type_default(self.request)
        self.assertEqual(default_volume_type, volume_type)
        cinderclient.volume_types.default.assert_called_once()


class CinderApiVersionTests(test.TestCase):

    def setUp(self):
        super(CinderApiVersionTests, self).setUp()
        # The version is set when the module is loaded. Reset the
        # active version each time so that we can test with different
        # versions.
        api.cinder.VERSIONS._active = None

    def test_default_client_is_v3(self):
        client = api.cinder.cinderclient(self.request)
        self.assertIsInstance(client, cinder_client.v3.client.Client)

    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    def test_v2_setting_returns_v2_client(self):
        # FIXME(e0ne): this is a temporary workaround to bypass
        # @memoized_with_request decorator caching. We have to find a better
        # solution instead this hack.
        self.request.user.username = 'test_user_cinder_v2'
        client = api.cinder.cinderclient(self.request)
        self.assertIsInstance(client, cinder_client.v2.client.Client)

    def test_get_v2_volume_attributes(self):
        # Get a v2 volume
        volume = self.cinder_volumes.get(name="v2_volume")
        self.assertTrue(hasattr(volume._apiresource, 'name'))

        name = "A v2 test volume name"
        description = "A v2 volume description"
        setattr(volume._apiresource, 'name', name)
        setattr(volume._apiresource, 'description', description)
        self.assertEqual(name, volume.name)
        self.assertEqual(description, volume.description)

    def test_get_v2_snapshot_attributes(self):
        # Get a v2 snapshot
        snapshot = self.cinder_volume_snapshots.get(
            description="v2 volume snapshot description")
        self.assertFalse(hasattr(snapshot._apiresource, 'display_name'))

        name = "A v2 test snapshot name"
        description = "A v2 snapshot description"
        setattr(snapshot._apiresource, 'name', name)
        setattr(snapshot._apiresource, 'description', description)
        self.assertEqual(name, snapshot.name)
        self.assertEqual(description, snapshot.description)

    def test_get_v2_snapshot_metadata(self):
        # Get a v2 snapshot with metadata
        snapshot = self.cinder_volume_snapshots.get(
            description="v2 volume snapshot with metadata description")
        self.assertTrue(hasattr(snapshot._apiresource, 'metadata'))
        self.assertFalse(hasattr(snapshot._apiresource, 'display_name'))

        key_name = "snapshot_meta_key"
        key_value = "snapshot_meta_value"
        metadata_value = {key_name: key_value}
        setattr(snapshot._apiresource, 'metadata', metadata_value)
        self.assertIn(key_name, snapshot.metadata.keys())
        self.assertEqual(key_value, snapshot.metadata['snapshot_meta_key'])

    def test_get_id_for_nameless_volume(self):
        volume = self.cinder_volumes.first()
        self.assertEqual('Volume name', volume.name)
