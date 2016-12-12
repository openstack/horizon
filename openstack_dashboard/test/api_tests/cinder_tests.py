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

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class CinderApiTests(test.APITestCase):

    def test_volume_list(self):
        search_opts = {'all_tenants': 1}
        detailed = True
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()
        cinderclient = self.stub_cinderclient()
        cinderclient.volumes = self.mox.CreateMockAnything()
        cinderclient.volumes.list(search_opts=search_opts,).AndReturn(volumes)
        cinderclient.transfers = self.mox.CreateMockAnything()
        cinderclient.transfers.list(
            detailed=detailed,
            search_opts=search_opts,).AndReturn(volume_transfers)
        self.mox.ReplayAll()

        api_volumes = api.cinder.volume_list(self.request,
                                             search_opts=search_opts)
        self.assertEqual(len(volumes), len(api_volumes))

    def test_volume_list_paged(self):
        search_opts = {'all_tenants': 1}
        detailed = True
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()
        cinderclient = self.stub_cinderclient()
        cinderclient.volumes = self.mox.CreateMockAnything()
        cinderclient.volumes.list(search_opts=search_opts,).AndReturn(volumes)
        cinderclient.transfers = self.mox.CreateMockAnything()
        cinderclient.transfers.list(
            detailed=detailed,
            search_opts=search_opts,).AndReturn(volume_transfers)
        self.mox.ReplayAll()

        api_volumes, has_more, has_prev = api.cinder.volume_list_paged(
            self.request, search_opts=search_opts)
        self.assertEqual(len(volumes), len(api_volumes))
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    def test_volume_list_paginate_first_page(self):
        api.cinder.VERSIONS._active = None
        page_size = settings.API_RESULT_PAGE_SIZE
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()

        search_opts = {'all_tenants': 1}
        mox_volumes = volumes[:page_size + 1]
        expected_volumes = mox_volumes[:-1]

        cinderclient = self.stub_cinderclient()
        cinderclient.volumes = self.mox.CreateMockAnything()
        cinderclient.volumes.list(search_opts=search_opts, limit=page_size + 1,
                                  sort='created_at:desc', marker=None).\
            AndReturn(mox_volumes)
        cinderclient.transfers = self.mox.CreateMockAnything()
        cinderclient.transfers.list(
            detailed=True,
            search_opts=search_opts,).AndReturn(volume_transfers)
        self.mox.ReplayAll()

        api_volumes, more_data, prev_data = api.cinder.volume_list_paged(
            self.request, search_opts=search_opts, paginate=True)
        self.assertEqual(len(expected_volumes), len(api_volumes))
        self.assertTrue(more_data)
        self.assertFalse(prev_data)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    def test_volume_list_paginate_second_page(self):
        api.cinder.VERSIONS._active = None
        page_size = settings.API_RESULT_PAGE_SIZE
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()

        search_opts = {'all_tenants': 1}
        mox_volumes = volumes[page_size:page_size * 2 + 1]
        expected_volumes = mox_volumes[:-1]
        marker = expected_volumes[0].id

        cinderclient = self.stub_cinderclient()
        cinderclient.volumes = self.mox.CreateMockAnything()
        cinderclient.volumes.list(search_opts=search_opts, limit=page_size + 1,
                                  sort='created_at:desc', marker=marker).\
            AndReturn(mox_volumes)
        cinderclient.transfers = self.mox.CreateMockAnything()
        cinderclient.transfers.list(
            detailed=True,
            search_opts=search_opts,).AndReturn(volume_transfers)
        self.mox.ReplayAll()

        api_volumes, more_data, prev_data = api.cinder.volume_list_paged(
            self.request, search_opts=search_opts, marker=marker,
            paginate=True)
        self.assertEqual(len(expected_volumes), len(api_volumes))
        self.assertTrue(more_data)
        self.assertTrue(prev_data)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    def test_volume_list_paginate_last_page(self):
        api.cinder.VERSIONS._active = None
        page_size = settings.API_RESULT_PAGE_SIZE
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()

        search_opts = {'all_tenants': 1}
        mox_volumes = volumes[-1 * page_size:]
        expected_volumes = mox_volumes
        marker = expected_volumes[0].id

        cinderclient = self.stub_cinderclient()
        cinderclient.volumes = self.mox.CreateMockAnything()
        cinderclient.volumes.list(search_opts=search_opts, limit=page_size + 1,
                                  sort='created_at:desc', marker=marker).\
            AndReturn(mox_volumes)
        cinderclient.transfers = self.mox.CreateMockAnything()
        cinderclient.transfers.list(
            detailed=True,
            search_opts=search_opts,).AndReturn(volume_transfers)
        self.mox.ReplayAll()

        api_volumes, more_data, prev_data = api.cinder.volume_list_paged(
            self.request, search_opts=search_opts, marker=marker,
            paginate=True)
        self.assertEqual(len(expected_volumes), len(api_volumes))
        self.assertFalse(more_data)
        self.assertTrue(prev_data)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    def test_volume_list_paginate_back_from_some_page(self):
        api.cinder.VERSIONS._active = None
        page_size = settings.API_RESULT_PAGE_SIZE
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()

        search_opts = {'all_tenants': 1}
        mox_volumes = volumes[page_size:page_size * 2 + 1]
        expected_volumes = mox_volumes[:-1]
        marker = expected_volumes[0].id

        cinderclient = self.stub_cinderclient()
        cinderclient.volumes = self.mox.CreateMockAnything()
        cinderclient.volumes.list(search_opts=search_opts, limit=page_size + 1,
                                  sort='created_at:asc', marker=marker).\
            AndReturn(mox_volumes)
        cinderclient.transfers = self.mox.CreateMockAnything()
        cinderclient.transfers.list(
            detailed=True,
            search_opts=search_opts,).AndReturn(volume_transfers)
        self.mox.ReplayAll()

        api_volumes, more_data, prev_data = api.cinder.volume_list_paged(
            self.request, search_opts=search_opts, sort_dir="asc",
            marker=marker, paginate=True)
        self.assertEqual(len(expected_volumes), len(api_volumes))
        self.assertTrue(more_data)
        self.assertTrue(prev_data)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    def test_volume_list_paginate_back_to_first_page(self):
        api.cinder.VERSIONS._active = None
        page_size = settings.API_RESULT_PAGE_SIZE
        volumes = self.cinder_volumes.list()
        volume_transfers = self.cinder_volume_transfers.list()

        search_opts = {'all_tenants': 1}
        mox_volumes = volumes[:page_size]
        expected_volumes = mox_volumes
        marker = expected_volumes[0].id

        cinderclient = self.stub_cinderclient()
        cinderclient.volumes = self.mox.CreateMockAnything()
        cinderclient.volumes.list(search_opts=search_opts, limit=page_size + 1,
                                  sort='created_at:asc', marker=marker).\
            AndReturn(mox_volumes)
        cinderclient.transfers = self.mox.CreateMockAnything()
        cinderclient.transfers.list(
            detailed=True,
            search_opts=search_opts,).AndReturn(volume_transfers)
        self.mox.ReplayAll()

        api_volumes, more_data, prev_data = api.cinder.volume_list_paged(
            self.request, search_opts=search_opts, sort_dir="asc",
            marker=marker, paginate=True)
        self.assertEqual(len(expected_volumes), len(api_volumes))
        self.assertTrue(more_data)
        self.assertFalse(prev_data)

    def test_volume_snapshot_list(self):
        search_opts = {'all_tenants': 1}
        volume_snapshots = self.cinder_volume_snapshots.list()
        cinderclient = self.stub_cinderclient()
        cinderclient.volume_snapshots = self.mox.CreateMockAnything()
        cinderclient.volume_snapshots.list(search_opts=search_opts).\
            AndReturn(volume_snapshots)
        self.mox.ReplayAll()

        api.cinder.volume_snapshot_list(self.request, search_opts=search_opts)

    def test_volume_snapshot_list_no_volume_configured(self):
        # remove volume from service catalog
        catalog = self.service_catalog
        for service in catalog:
            if service["type"] == "volume":
                self.service_catalog.remove(service)
        search_opts = {'all_tenants': 1}
        volume_snapshots = self.cinder_volume_snapshots.list()

        cinderclient = self.stub_cinderclient()
        cinderclient.volume_snapshots = self.mox.CreateMockAnything()
        cinderclient.volume_snapshots.list(search_opts=search_opts).\
            AndReturn(volume_snapshots)
        self.mox.ReplayAll()

        api.cinder.volume_snapshot_list(self.request, search_opts=search_opts)

    def test_volume_type_list_with_qos_associations(self):
        volume_types = self.cinder_volume_types.list()
        # Due to test data limitations, we can only run this test using
        # one qos spec, which is associated with one volume type.
        # If we use multiple qos specs, the test data will always
        # return the same associated volume type, which is invalid
        # and prevented by the UI.
        qos_specs_full = self.cinder_qos_specs.list()
        qos_specs_only_one = [qos_specs_full[0]]
        associations = self.cinder_qos_spec_associations.list()

        cinderclient = self.stub_cinderclient()
        cinderclient.volume_types = self.mox.CreateMockAnything()
        cinderclient.volume_types.list().AndReturn(volume_types)
        cinderclient.qos_specs = self.mox.CreateMockAnything()
        cinderclient.qos_specs.list().AndReturn(qos_specs_only_one)
        cinderclient.qos_specs.get_associations = self.mox.CreateMockAnything()
        cinderclient.qos_specs.get_associations(qos_specs_only_one[0].id).\
            AndReturn(associations)
        self.mox.ReplayAll()

        assoc_vol_types = \
            api.cinder.volume_type_list_with_qos_associations(self.request)
        associate_spec = assoc_vol_types[0].associated_qos_spec
        self.assertEqual(associate_spec, qos_specs_only_one[0].name)

    def test_volume_type_get_with_qos_association(self):
        volume_type = self.cinder_volume_types.first()
        qos_specs_full = self.cinder_qos_specs.list()
        qos_specs_only_one = [qos_specs_full[0]]
        associations = self.cinder_qos_spec_associations.list()

        cinderclient = self.stub_cinderclient()
        cinderclient.volume_types = self.mox.CreateMockAnything()
        cinderclient.volume_types.get(volume_type.id).AndReturn(volume_type)
        cinderclient.qos_specs = self.mox.CreateMockAnything()
        cinderclient.qos_specs.list().AndReturn(qos_specs_only_one)
        cinderclient.qos_specs.get_associations = self.mox.CreateMockAnything()
        cinderclient.qos_specs.get_associations(qos_specs_only_one[0].id).\
            AndReturn(associations)
        self.mox.ReplayAll()

        assoc_vol_type = \
            api.cinder.volume_type_get_with_qos_association(self.request,
                                                            volume_type.id)
        associate_spec = assoc_vol_type.associated_qos_spec
        self.assertEqual(associate_spec, qos_specs_only_one[0].name)

    def test_absolute_limits_with_negative_values(self):
        values = {"maxTotalVolumes": -1, "totalVolumesUsed": -1}
        expected_results = {"maxTotalVolumes": float("inf"),
                            "totalVolumesUsed": 0}

        limits = self.mox.CreateMockAnything()
        limits.absolute = []
        for key, val in values.items():
            limit = self.mox.CreateMockAnything()
            limit.name = key
            limit.value = val
            limits.absolute.append(limit)

        cinderclient = self.stub_cinderclient()
        cinderclient.limits = self.mox.CreateMockAnything()
        cinderclient.limits.get().AndReturn(limits)
        self.mox.ReplayAll()

        ret_val = api.cinder.tenant_absolute_limits(self.request)
        for key in expected_results.keys():
            self.assertEqual(expected_results[key], ret_val[key])

    def test_pool_list(self):
        pools = self.cinder_pools.list()
        cinderclient = self.stub_cinderclient()
        cinderclient.pools = self.mox.CreateMockAnything()
        cinderclient.pools.list(detailed=True).AndReturn(pools)
        self.mox.ReplayAll()

        # No assertions are necessary. Verification is handled by mox.
        api.cinder.pool_list(self.request, detailed=True)

    def test_volume_type_default(self):
        volume_type = self.cinder_volume_types.first()
        cinderclient = self.stub_cinderclient()
        cinderclient.volume_types = self.mox.CreateMockAnything()
        cinderclient.volume_types.default().AndReturn(volume_type)
        self.mox.ReplayAll()

        default_volume_type = api.cinder.volume_type_default(self.request)
        self.assertEqual(default_volume_type, volume_type)

    def test_cgroup_list(self):
        cgroups = self.cinder_consistencygroups.list()
        cinderclient = self.stub_cinderclient()
        cinderclient.consistencygroups = self.mox.CreateMockAnything()
        cinderclient.consistencygroups.list(search_opts=None).\
            AndReturn(cgroups)
        self.mox.ReplayAll()
        api_cgroups = api.cinder.volume_cgroup_list(self.request)
        self.assertEqual(len(cgroups), len(api_cgroups))

    def test_cgroup_get(self):
        cgroup = self.cinder_consistencygroups.first()
        cinderclient = self.stub_cinderclient()
        cinderclient.consistencygroups = self.mox.CreateMockAnything()
        cinderclient.consistencygroups.get(cgroup.id).AndReturn(cgroup)
        self.mox.ReplayAll()
        api_cgroup = api.cinder.volume_cgroup_get(self.request, cgroup.id)
        self.assertEqual(api_cgroup.name, cgroup.name)
        self.assertEqual(api_cgroup.description, cgroup.description)
        self.assertEqual(api_cgroup.volume_types, cgroup.volume_types)

    def test_cgroup_list_with_vol_type_names(self):
        cgroups = self.cinder_consistencygroups.list()
        volume_types_list = self.cinder_volume_types.list()
        cinderclient = self.stub_cinderclient()
        cinderclient.consistencygroups = self.mox.CreateMockAnything()
        cinderclient.consistencygroups.list(search_opts=None).\
            AndReturn(cgroups)
        cinderclient.volume_types = self.mox.CreateMockAnything()
        cinderclient.volume_types.list().AndReturn(volume_types_list)
        self.mox.ReplayAll()
        api_cgroups = api.cinder.volume_cgroup_list_with_vol_type_names(
            self.request)
        self.assertEqual(len(cgroups), len(api_cgroups))
        for i in range(len(api_cgroups[0].volume_type_names)):
            self.assertEqual(volume_types_list[i].name,
                             api_cgroups[0].volume_type_names[i])

    def test_cgsnapshot_list(self):
        cgsnapshots = self.cinder_cg_snapshots.list()
        cinderclient = self.stub_cinderclient()
        cinderclient.cgsnapshots = self.mox.CreateMockAnything()
        cinderclient.cgsnapshots.list(search_opts=None).\
            AndReturn(cgsnapshots)
        self.mox.ReplayAll()
        api_cgsnapshots = api.cinder.volume_cg_snapshot_list(self.request)
        self.assertEqual(len(cgsnapshots), len(api_cgsnapshots))

    def test_cgsnapshot_get(self):
        cgsnapshot = self.cinder_cg_snapshots.first()
        cinderclient = self.stub_cinderclient()
        cinderclient.cgsnapshots = self.mox.CreateMockAnything()
        cinderclient.cgsnapshots.get(cgsnapshot.id).AndReturn(cgsnapshot)
        self.mox.ReplayAll()
        api_cgsnapshot = api.cinder.volume_cg_snapshot_get(self.request,
                                                           cgsnapshot.id)
        self.assertEqual(api_cgsnapshot.name, cgsnapshot.name)
        self.assertEqual(api_cgsnapshot.description, cgsnapshot.description)
        self.assertEqual(api_cgsnapshot.consistencygroup_id,
                         cgsnapshot.consistencygroup_id)


class CinderApiVersionTests(test.TestCase):

    def setUp(self):
        super(CinderApiVersionTests, self).setUp()
        # The version is set when the module is loaded. Reset the
        # active version each time so that we can test with different
        # versions.
        api.cinder.VERSIONS._active = None

    def test_default_client_is_v2(self):
        client = api.cinder.cinderclient(self.request)
        self.assertIsInstance(client, cinder_client.v2.client.Client)

    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    def test_v2_setting_returns_v2_client(self):
        client = api.cinder.cinderclient(self.request)
        self.assertIsInstance(client, cinder_client.v2.client.Client)

    def test_get_v2_volume_attributes(self):
        # Get a v2 volume
        volume = self.cinder_volumes.get(name="v2_volume")
        self.assertTrue(hasattr(volume._apiresource, 'name'))
        self.assertFalse(hasattr(volume._apiresource, 'display_name'))

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
        setattr(volume._apiresource, 'display_name', "")
        self.assertEqual(volume.id, volume.name)

    def test_adapt_dictionary_to_v2(self):
        volume = self.cinder_volumes.first()
        data = {'name': volume.name,
                'description': volume.description,
                'size': volume.size}

        ret_data = api.cinder._replace_v2_parameters(data)
        self.assertIn('name', ret_data.keys())
        self.assertIn('description', ret_data.keys())
        self.assertNotIn('display_name', ret_data.keys())
        self.assertNotIn('display_description', ret_data.keys())
