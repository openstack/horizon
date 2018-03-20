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

from django.urls import reverse
from django.utils.http import urlunquote
import mock

from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:cgroups:index')
VOLUME_CGROUPS_SNAP_INDEX_URL = urlunquote(reverse(
    'horizon:project:cg_snapshots:index'))


class ConsistencyGroupTests(test.TestCase):
    @test.create_mocks({cinder: ('extension_supported',
                                 'availability_zone_list',
                                 'volume_type_list',
                                 'volume_type_list_with_qos_associations',
                                 'volume_cgroup_list',
                                 'volume_cgroup_create')})
    def test_create_cgroup(self):
        cgroup = self.cinder_consistencygroups.first()
        volume_types = self.cinder_volume_types.list()
        volume_type_id = self.cinder_volume_types.first().id
        az = self.cinder_availability_zones.first().zoneName
        formData = {'volume_types': '1',
                    'name': 'test CG',
                    'description': 'test desc',
                    'availability_zone': az,
                    'add_vtypes_to_cgroup_role_member': [volume_type_id]}

        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_volume_type_list.return_value = volume_types
        self.mock_volume_type_list_with_qos_associations.return_value = \
            volume_types
        self.mock_volume_cgroup_list.return_value = \
            self.cinder_consistencygroups.list()
        self.mock_volume_cgroup_create.return_value = cgroup

        url = reverse('horizon:project:cgroups:create')
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_availability_zone_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_type_list_with_qos_associations \
            .assert_called_once_with(test.IsHttpRequest())
        self.mock_volume_cgroup_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_cgroup_create.assert_called_once_with(
            test.IsHttpRequest(),
            formData['volume_types'],
            formData['name'],
            description=formData['description'],
            availability_zone=formData['availability_zone'])

    @test.create_mocks({cinder: ('extension_supported',
                                 'availability_zone_list',
                                 'volume_type_list',
                                 'volume_type_list_with_qos_associations',
                                 'volume_cgroup_list',
                                 'volume_cgroup_create')})
    def test_create_cgroup_exception(self):
        volume_types = self.cinder_volume_types.list()
        volume_type_id = self.cinder_volume_types.first().id
        az = self.cinder_availability_zones.first().zoneName
        formData = {'volume_types': '1',
                    'name': 'test CG',
                    'description': 'test desc',
                    'availability_zone': az,
                    'add_vtypes_to_cgroup_role_member': [volume_type_id]}

        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_volume_type_list.return_value = volume_types
        self.mock_volume_type_list_with_qos_associations.return_value = \
            volume_types
        self.mock_volume_cgroup_list.return_value = \
            self.cinder_consistencygroups.list()
        self.mock_volume_cgroup_create.side_effect = self.exceptions.cinder

        url = reverse('horizon:project:cgroups:create')
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertIn("Unable to create consistency group.",
                      res.cookies.output())

        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_availability_zone_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_type_list_with_qos_associations \
            .assert_called_once_with(test.IsHttpRequest())
        self.mock_volume_cgroup_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_cgroup_create.assert_called_once_with(
            test.IsHttpRequest(),
            formData['volume_types'],
            formData['name'],
            description=formData['description'],
            availability_zone=formData['availability_zone'])

    @test.create_mocks({cinder: ('volume_cgroup_get',
                                 'volume_cgroup_delete')})
    def test_delete_cgroup(self):
        cgroup = self.cinder_consistencygroups.first()

        self.mock_volume_cgroup_get.return_value = cgroup
        self.mock_volume_cgroup_delete.return_value = None

        url = reverse('horizon:project:cgroups:delete',
                      args=[cgroup.id])
        res = self.client.post(url)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_cgroup_get.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id)
        self.mock_volume_cgroup_delete.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id, force=False)

    @test.create_mocks({cinder: ('volume_cgroup_get',
                                 'volume_cgroup_delete')})
    def test_delete_cgroup_force_flag(self):
        cgroup = self.cinder_consistencygroups.first()
        formData = {'delete_volumes': True}

        self.mock_volume_cgroup_get.return_value = cgroup
        self.mock_volume_cgroup_delete.return_value = None

        url = reverse('horizon:project:cgroups:delete',
                      args=[cgroup.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_cgroup_get.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id)
        self.mock_volume_cgroup_delete.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id, force=True)

    @test.create_mocks({cinder: ('volume_cgroup_get',
                                 'volume_cgroup_delete')})
    def test_delete_cgroup_exception(self):
        cgroup = self.cinder_consistencygroups.first()
        formData = {'delete_volumes': False}

        self.mock_volume_cgroup_get.return_value = cgroup
        self.mock_volume_cgroup_delete.side_effect = self.exceptions.cinder

        url = reverse('horizon:project:cgroups:delete',
                      args=[cgroup.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_cgroup_get.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id)
        self.mock_volume_cgroup_delete.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id, force=False)

    def test_update_cgroup_add_vol(self):
        self._test_update_cgroup_add_remove_vol(add=True)

    def test_update_cgroup_remove_vol(self):
        self._test_update_cgroup_add_remove_vol(add=False)

    @test.create_mocks({cinder: ('volume_list',
                                 'volume_type_list',
                                 'volume_cgroup_get',
                                 'volume_cgroup_update')})
    def _test_update_cgroup_add_remove_vol(self, add=True):
        cgroup = self.cinder_consistencygroups.first()
        volume_types = self.cinder_volume_types.list()
        volumes = (self.cinder_volumes.list() +
                   self.cinder_cgroup_volumes.list())

        cgroup_voltype_names = [t.name for t in volume_types
                                if t.id in cgroup.volume_types]
        compat_volumes = [v for v in volumes
                          if v.volume_type in cgroup_voltype_names]
        compat_volume_ids = [v.id for v in compat_volumes]
        assigned_volume_ids = [v.id for v in compat_volumes
                               if getattr(v, 'consistencygroup_id', None)]
        add_volume_ids = [v.id for v in compat_volumes
                          if v.id not in assigned_volume_ids]

        new_volums = compat_volume_ids if add else []
        formData = {
            'default_add_volumes_to_cgroup_role': 'member',
            'add_volumes_to_cgroup_role_member': new_volums,
        }

        self.mock_volume_list.return_value = volumes
        self.mock_volume_type_list.return_value = volume_types
        self.mock_volume_cgroup_get.return_value = cgroup
        self.mock_volume_cgroup_update.return_value = cgroup

        url = reverse('horizon:project:cgroups:manage',
                      args=[cgroup.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_volume_list, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_cgroup_get.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id)
        if add:
            self.mock_volume_cgroup_update.assert_called_once_with(
                test.IsHttpRequest(), cgroup.id,
                name=cgroup.name,
                add_vols=','.join(add_volume_ids),
                remove_vols='')
        else:
            self.mock_volume_cgroup_update.assert_called_once_with(
                test.IsHttpRequest(), cgroup.id,
                name=cgroup.name,
                add_vols='',
                remove_vols=','.join(assigned_volume_ids))

    @test.create_mocks({cinder: ('volume_cgroup_get',
                                 'volume_cgroup_update')})
    def test_update_cgroup_name_and_description(self):
        cgroup = self.cinder_consistencygroups.first()
        formData = {'volume_types': '1',
                    'name': 'test CG-new',
                    'description': 'test desc-new'}

        self.mock_volume_cgroup_get.return_value = cgroup
        self.mock_volume_cgroup_update.return_value = cgroup

        url = reverse('horizon:project:cgroups:update',
                      args=[cgroup.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_cgroup_get.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id)
        self.mock_volume_cgroup_update.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id,
            formData['name'],
            formData['description'])

    @test.create_mocks({cinder: ('volume_cgroup_get',
                                 'volume_cgroup_update')})
    def test_update_cgroup_with_exception(self):
        cgroup = self.cinder_consistencygroups.first()
        formData = {'volume_types': '1',
                    'name': 'test CG-new',
                    'description': 'test desc-new'}

        self.mock_volume_cgroup_get.return_value = cgroup
        self.mock_volume_cgroup_update.side_effect = self.exceptions.cinder

        url = reverse('horizon:project:cgroups:update',
                      args=[cgroup.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_cgroup_get.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id)
        self.mock_volume_cgroup_update.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id,
            formData['name'],
            formData['description'])

    @test.create_mocks({cinder: ('volume_cgroup_get',)})
    def test_detail_view_with_exception(self):
        cgroup = self.cinder_consistencygroups.first()

        self.mock_volume_cgroup_get.side_effect = self.exceptions.cinder

        url = reverse('horizon:project:cgroups:detail',
                      args=[cgroup.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_cgroup_get.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id)

    @test.create_mocks({cinder: ('volume_cg_snapshot_create',)})
    def test_create_snapshot(self):
        cgroup = self.cinder_consistencygroups.first()
        cg_snapshot = self.cinder_cg_snapshots.first()
        formData = {'cgroup_id': cgroup.id,
                    'name': 'test CG Snapshot',
                    'description': 'test desc'}

        self.mock_volume_cg_snapshot_create.return_value = cg_snapshot

        url = reverse('horizon:project:cgroups:create_snapshot',
                      args=[cgroup.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, VOLUME_CGROUPS_SNAP_INDEX_URL)

        self.mock_volume_cg_snapshot_create.assert_called_once_with(
            test.IsHttpRequest(),
            formData['cgroup_id'],
            formData['name'],
            formData['description'])

    @test.create_mocks({cinder: ('volume_cgroup_get',
                                 'volume_cgroup_create_from_source')})
    def test_create_clone(self):
        cgroup = self.cinder_consistencygroups.first()
        formData = {'cgroup_id': cgroup.id,
                    'name': 'test CG Clone',
                    'description': 'test desc'}
        self.mock_volume_cgroup_get.return_value = cgroup
        self.mock_volume_cgroup_create_from_source.return_value = cgroup

        url = reverse('horizon:project:cgroups:clone_cgroup',
                      args=[cgroup.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_cgroup_get.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id)
        self.mock_volume_cgroup_create_from_source.assert_called_once_with(
            test.IsHttpRequest(),
            formData['name'],
            source_cgroup_id=formData['cgroup_id'],
            description=formData['description'])
