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
from openstack_dashboard.dashboards.admin.volumes.volumes import forms
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

    @test.create_stubs({cinder: ('volume_manage',
                                 'volume_type_list',
                                 'availability_zone_list',
                                 'extension_supported')})
    def test_manage_volume(self):
        metadata = {'key': u'k1',
                    'value': u'v1'}
        formData = {'host': 'host-1',
                    'identifier': 'vol-1',
                    'id_type': u'source-name',
                    'name': 'name-1',
                    'description': 'manage a volume',
                    'volume_type': 'vol_type_1',
                    'availability_zone': 'nova',
                    'metadata': metadata['key'] + '=' + metadata['value'],
                    'bootable': False}
        cinder.volume_type_list(
            IsA(http.HttpRequest)).\
            AndReturn(self.volume_types.list())
        cinder.availability_zone_list(
            IsA(http.HttpRequest)).\
            AndReturn(self.availability_zones.list())
        cinder.extension_supported(
            IsA(http.HttpRequest),
            'AvailabilityZones').\
            AndReturn(True)
        cinder.volume_manage(
            IsA(http.HttpRequest),
            host=formData['host'],
            identifier=formData['identifier'],
            id_type=formData['id_type'],
            name=formData['name'],
            description=formData['description'],
            volume_type=formData['volume_type'],
            availability_zone=formData['availability_zone'],
            metadata={metadata['key']: metadata['value']},
            bootable=formData['bootable'])
        self.mox.ReplayAll()
        res = self.client.post(
            reverse('horizon:admin:volumes:volumes:manage'),
            formData)
        self.assertNoFormErrors(res)

    def test_manage_volume_extra_specs(self):
        # these should pass
        forms.validate_metadata("key1=val1")
        forms.validate_metadata("key1=val1,key2=val2")
        forms.validate_metadata("key1=val1,key2=val2,key3=val3")
        forms.validate_metadata("key1=")

        # these should throw a validation error
        self.assertRaises(forms.ValidationError,
                          forms.validate_metadata, "key1==val1")
        self.assertRaises(forms.ValidationError,
                          forms.validate_metadata, "key1=val1,")
        self.assertRaises(forms.ValidationError,
                          forms.validate_metadata, "=val1")
        self.assertRaises(forms.ValidationError,
                          forms.validate_metadata, ",")
        self.assertRaises(forms.ValidationError,
                          forms.validate_metadata, "  ")

    @test.create_stubs({cinder: ('volume_unmanage',
                                 'volume_get')})
    def test_unmanage_volume(self):
        # important - need to get the v2 cinder volume which has host data
        volume_list = \
            filter(lambda x: x.name == 'v2_volume', self.cinder_volumes.list())
        volume = volume_list[0]
        formData = {'volume_name': volume.name,
                    'host_name': 'host@backend-name#pool',
                    'volume_id': volume.id}

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        cinder.volume_unmanage(IsA(http.HttpRequest), volume.id).\
            AndReturn(volume)
        self.mox.ReplayAll()
        res = self.client.post(
            reverse('horizon:admin:volumes:volumes:unmanage',
                    args=(volume.id,)),
            formData)
        self.assertNoFormErrors(res)

    @test.create_stubs({cinder: ('volume_type_list_with_qos_associations',
                                 'qos_spec_list',
                                 'extension_supported',
                                 'volume_encryption_type_list')})
    def test_volume_types_tab(self):
        encryption_list = (self.cinder_volume_encryption_types.list()[0],
                           self.cinder_volume_encryption_types.list()[1])
        cinder.volume_type_list_with_qos_associations(
            IsA(http.HttpRequest)).\
            AndReturn(self.volume_types.list())
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
