# Copyright 2012 Nebula, Inc.
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

from django.core.urlresolvers import reverse
from django import http
from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone
from openstack_dashboard.test import helpers as test


class VolumeTests(test.BaseAdminViewTests):
    @test.create_stubs({api.nova: ('server_list',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list'),
                        keystone: ('tenant_list',)})
    def test_index(self):
        cinder.volume_list(IsA(http.HttpRequest), search_opts={
            'all_tenants': True}).AndReturn(self.cinder_volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest), search_opts={
            'all_tenants': True}).AndReturn([])
        api.nova.server_list(IsA(http.HttpRequest), search_opts={
                             'all_tenants': True}) \
            .AndReturn([self.servers.list(), False])
        keystone.tenant_list(IsA(http.HttpRequest)) \
            .AndReturn([self.tenants.list(), False])

        self.mox.ReplayAll()
        res = self.client.get(reverse('horizon:admin:volumes:index'))

        self.assertTemplateUsed(res, 'admin/volumes/index.html')
        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, self.cinder_volumes.list())

    @test.create_stubs({cinder: ('volume_type_list_with_qos_associations',
                                 'qos_spec_list',
                                 'extension_supported',
                                 'volume_encryption_type_list')})
    def test_volume_types_tab(self):
        encryption_list = (self.cinder_volume_encryption_types.list()[0],
                           self.cinder_volume_encryption_types.list()[1])
        cinder.volume_type_list_with_qos_associations(
            IsA(http.HttpRequest)).\
            AndReturn(self.cinder_volume_types.list())
        cinder.qos_spec_list(IsA(http.HttpRequest)).\
            AndReturn(self.cinder_qos_specs.list())
        cinder.volume_encryption_type_list(IsA(http.HttpRequest))\
            .AndReturn(encryption_list)
        cinder.extension_supported(IsA(http.HttpRequest),
                                   'VolumeTypeEncryption').MultipleTimes()\
            .AndReturn(True)

        self.mox.ReplayAll()
        res = self.client.get(reverse(
            'horizon:admin:volumes:volume_types_tab'))

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(
            res, 'admin/volumes/volume_types/volume_types_tables.html')
        volume_types = res.context['volume_types_table'].data
        self.assertItemsEqual(volume_types, self.cinder_volume_types.list())
        qos_specs = res.context['qos_specs_table'].data
        self.assertItemsEqual(qos_specs, self.cinder_qos_specs.list())

    @test.create_stubs({cinder: ('volume_list',
                                 'volume_snapshot_list',),
                        keystone: ('tenant_list',)})
    def test_snapshots_tab(self):
        cinder.volume_snapshot_list(IsA(http.HttpRequest), search_opts={
            'all_tenants': True}). \
            AndReturn(self.cinder_volume_snapshots.list())
        cinder.volume_list(IsA(http.HttpRequest), search_opts={
            'all_tenants': True}).\
            AndReturn(self.cinder_volumes.list())
        keystone.tenant_list(IsA(http.HttpRequest)). \
            AndReturn([self.tenants.list(), False])

        self.mox.ReplayAll()
        res = self.client.get(reverse('horizon:admin:volumes:snapshots_tab'))

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        snapshots = res.context['volume_snapshots_table'].data
        self.assertItemsEqual(snapshots, self.cinder_volume_snapshots.list())
