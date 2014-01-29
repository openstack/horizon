# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.test.utils import override_settings

import cinderclient as cinder_client

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class CinderApiTests(test.APITestCase):
    def test_volume_list(self):
        search_opts = {'all_tenants': 1}
        volumes = self.cinder_volumes.list()
        cinderclient = self.stub_cinderclient()
        cinderclient.volumes = self.mox.CreateMockAnything()
        cinderclient.volumes.list(search_opts=search_opts,).AndReturn(volumes)
        self.mox.ReplayAll()

        # No assertions are necessary. Verification is handled by mox.
        api.cinder.volume_list(self.request, search_opts=search_opts)

    def test_volume_snapshot_list(self):
        volume_snapshots = self.cinder_volume_snapshots.list()
        cinderclient = self.stub_cinderclient()
        cinderclient.volume_snapshots = self.mox.CreateMockAnything()
        cinderclient.volume_snapshots.list().AndReturn(volume_snapshots)
        self.mox.ReplayAll()

        api.cinder.volume_snapshot_list(self.request)

    def test_volume_snapshot_list_no_volume_configured(self):
        # remove volume from service catalog
        catalog = self.service_catalog
        for service in catalog:
            if service["type"] == "volume":
                self.service_catalog.remove(service)
        volume_snapshots = self.cinder_volume_snapshots.list()

        cinderclient = self.stub_cinderclient()
        cinderclient.volume_snapshots = self.mox.CreateMockAnything()
        cinderclient.volume_snapshots.list().AndReturn(volume_snapshots)
        self.mox.ReplayAll()

        api.cinder.volume_snapshot_list(self.request)


class CinderApiVersionTests(test.TestCase):

    def setUp(self):
        super(CinderApiVersionTests, self).setUp()
        # The version is set when the module is loaded. Reset the
        # active version each time so that we can test with different
        # versions.
        api.cinder.VERSIONS._active = None

    def test_default_client_is_v1(self):
        client = api.cinder.cinderclient(self.request)
        self.assertIsInstance(client, cinder_client.v1.client.Client)

    @override_settings(OPENSTACK_API_VERSIONS={'volume': 1})
    def test_v1_setting_returns_v1_client(self):
        client = api.cinder.cinderclient(self.request)
        self.assertIsInstance(client, cinder_client.v1.client.Client)

    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
    def test_v2_setting_returns_v2_client(self):
        client = api.cinder.cinderclient(self.request)
        self.assertIsInstance(client, cinder_client.v2.client.Client)

    def test_get_v1_volume_attributes(self):
        # Get a v1 volume
        volume = self.cinder_volumes.first()
        self.assertTrue(hasattr(volume._apiresource, 'display_name'))
        self.assertFalse(hasattr(volume._apiresource, 'name'))

        name = "A test volume name"
        description = "A volume description"
        setattr(volume._apiresource, 'display_name', name)
        setattr(volume._apiresource, 'display_description', description)
        self.assertEqual(volume.name, name)
        self.assertEqual(volume.description, description)

    def test_get_v2_volume_attributes(self):
        # Get a v2 volume
        volume = self.cinder_volumes.get(name="v2_volume")
        self.assertTrue(hasattr(volume._apiresource, 'name'))
        self.assertFalse(hasattr(volume._apiresource, 'display_name'))

        name = "A v2 test volume name"
        description = "A v2 volume description"
        setattr(volume._apiresource, 'name', name)
        setattr(volume._apiresource, 'description', description)
        self.assertEqual(volume.name, name)
        self.assertEqual(volume.description, description)

    def test_get_v1_snapshot_attributes(self):
        # Get a v1 snapshot
        snapshot = self.cinder_volume_snapshots.first()
        self.assertFalse(hasattr(snapshot._apiresource, 'name'))

        name = "A test snapshot name"
        description = "A snapshot description"
        setattr(snapshot._apiresource, 'display_name', name)
        setattr(snapshot._apiresource, 'display_description', description)
        self.assertEqual(snapshot.name, name)
        self.assertEqual(snapshot.description, description)

    def test_get_v2_snapshot_attributes(self):
        # Get a v2 snapshot
        snapshot = self.cinder_volume_snapshots.get(
            description="v2 volume snapshot description")
        self.assertFalse(hasattr(snapshot._apiresource, 'display_name'))

        name = "A v2 test snapshot name"
        description = "A v2 snapshot description"
        setattr(snapshot._apiresource, 'name', name)
        setattr(snapshot._apiresource, 'description', description)
        self.assertEqual(snapshot.name, name)
        self.assertEqual(snapshot.description, description)

    def test_get_id_for_nameless_volume(self):
        volume = self.cinder_volumes.first()
        setattr(volume._apiresource, 'display_name', "")
        self.assertEqual(volume.name, volume.id)

    @override_settings(OPENSTACK_API_VERSIONS={'volume': 1})
    def test_adapt_dictionary_to_v1(self):
        volume = self.cinder_volumes.first()
        data = {'name': volume.name,
                'description': volume.description,
                'size': volume.size}

        ret_data = api.cinder._replace_v2_parameters(data)
        self.assertIn('display_name', ret_data.keys())
        self.assertIn('display_description', ret_data.keys())
        self.assertNotIn('name', ret_data.keys())
        self.assertNotIn('description', ret_data.keys())

    @override_settings(OPENSTACK_API_VERSIONS={'volume': 2})
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
