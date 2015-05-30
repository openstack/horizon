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

from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test


class VolumeViewTests(test.BaseAdminViewTests):
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
