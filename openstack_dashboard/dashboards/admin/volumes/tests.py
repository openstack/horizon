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
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone
from openstack_dashboard.test import helpers as test


class VolumeTests(test.BaseAdminViewTests):
    @test.create_stubs({api.nova: ('server_list',),
                        cinder: ('volume_list',),
                        keystone: ('tenant_list',)})
    def test_index(self):
        cinder.volume_list(IsA(http.HttpRequest), search_opts={
            'all_tenants': True}).AndReturn(self.cinder_volumes.list())
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

    @test.create_stubs({cinder: ('volume_reset_state',
                                 'volume_get')})
    def test_update_volume_status(self):
        volume = self.volumes.first()
        formData = {'status': 'error'}

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        cinder.volume_reset_state(IsA(http.HttpRequest),
                                  volume.id,
                                  formData['status'])
        self.mox.ReplayAll()

        res = self.client.post(
            reverse('horizon:admin:volumes:volumes:update_status',
                args=(volume.id,)),
            formData)
        self.assertNoFormErrors(res)

    @test.create_stubs({cinder: ('volume_type_list_with_qos_associations',
                                 'qos_spec_list',)})
    def test_volume_types_tab(self):
        cinder.volume_type_list_with_qos_associations(
            IsA(http.HttpRequest)).\
            AndReturn(self.volume_types.list())
        cinder.qos_spec_list(IsA(http.HttpRequest)).\
            AndReturn(self.cinder_qos_specs.list())

        self.mox.ReplayAll()
        res = self.client.get(reverse(
            'horizon:admin:volumes:volume_types_tab'))

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
            'admin/volumes/volume_types/volume_types_tables.html')
        volume_types = res.context['volume_types_table'].data
        self.assertItemsEqual(volume_types, self.volume_types.list())
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
