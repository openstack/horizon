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


from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class CinderApiTests(test.APITestCase):
    def test_volume_list(self):
        search_opts = {'all_tenants': 1}
        volumes = self.volumes.list()
        cinderclient = self.stub_cinderclient()
        cinderclient.volumes = self.mox.CreateMockAnything()
        cinderclient.volumes.list(search_opts=search_opts,).AndReturn(volumes)
        self.mox.ReplayAll()

        # No assertions are necessary. Verification is handled by mox.
        api.cinder.volume_list(self.request, search_opts=search_opts)

    def test_volume_snapshot_list(self):
        volume_snapshots = self.volume_snapshots.list()
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
        volume_snapshots = self.volume_snapshots.list()

        cinderclient = self.stub_cinderclient()
        cinderclient.volume_snapshots = self.mox.CreateMockAnything()
        cinderclient.volume_snapshots.list().AndReturn(volume_snapshots)
        self.mox.ReplayAll()

        api.cinder.volume_snapshot_list(self.request)
