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


INDEX_URL = reverse('horizon:project:volume_groups:index')
VOLUME_GROUPS_SNAP_INDEX_URL = urlunquote(reverse(
    'horizon:project:vg_snapshots:index'))


class VolumeGroupTests(test.TestCase):
    @test.create_mocks({cinder: [
        'extension_supported',
        'availability_zone_list',
        'volume_type_list',
        'group_type_list',
        'group_create',
    ]})
    def test_create_group(self):
        group = self.cinder_groups.first()
        volume_types = self.cinder_volume_types.list()
        volume_type_id = self.cinder_volume_types.first().id
        selected_types = [volume_type_id]
        az = self.cinder_availability_zones.first().zoneName

        formData = {
            'volume_types': '1',
            'name': 'test VG',
            'description': 'test desc',
            'availability_zone': az,
            'group_type': group.group_type,
            'add_vtypes_to_group_role_member': selected_types,
        }

        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_volume_type_list.return_value = volume_types
        self.mock_group_type_list.return_value = self.cinder_group_types.list()
        self.mock_group_create.return_value = group

        url = reverse('horizon:project:volume_groups:create')
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_availability_zone_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_group_type_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_group_create.assert_called_once_with(
            test.IsHttpRequest(),
            formData['name'],
            formData['group_type'],
            selected_types,
            description=formData['description'],
            availability_zone=formData['availability_zone'])

    @test.create_mocks({cinder: [
        'extension_supported',
        'availability_zone_list',
        'volume_type_list',
        'group_type_list',
        'group_create',
    ]})
    def test_create_group_exception(self):
        group = self.cinder_groups.first()
        volume_types = self.cinder_volume_types.list()
        volume_type_id = self.cinder_volume_types.first().id
        selected_types = [volume_type_id]
        az = self.cinder_availability_zones.first().zoneName
        formData = {
            'volume_types': '1',
            'name': 'test VG',
            'description': 'test desc',
            'availability_zone': az,
            'group_type': group.group_type,
            'add_vtypes_to_group_role_member': selected_types,
        }

        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_volume_type_list.return_value = volume_types
        self.mock_group_type_list.return_value = self.cinder_group_types.list()
        self.mock_group_create.side_effect = self.exceptions.cinder

        url = reverse('horizon:project:volume_groups:create')
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertIn("Unable to create group.",
                      res.cookies.output())

        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_availability_zone_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_group_type_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_group_create.assert_called_once_with(
            test.IsHttpRequest(),
            formData['name'],
            formData['group_type'],
            selected_types,
            description=formData['description'],
            availability_zone=formData['availability_zone'])

    @test.create_mocks({cinder: ['group_get', 'group_delete']})
    def test_delete_group(self):
        group = self.cinder_groups.first()

        self.mock_group_get.return_value = group
        self.mock_group_delete.return_value = None

        url = reverse('horizon:project:volume_groups:delete',
                      args=[group.id])
        res = self.client.post(url)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_get.assert_called_once_with(test.IsHttpRequest(),
                                                    group.id)
        self.mock_group_delete.assert_called_once_with(test.IsHttpRequest(),
                                                       group.id,
                                                       delete_volumes=False)

    @test.create_mocks({cinder: ['group_get', 'group_delete']})
    def test_delete_group_delete_volumes_flag(self):
        group = self.cinder_groups.first()
        formData = {'delete_volumes': True}

        self.mock_group_get.return_value = group
        self.mock_group_delete.return_value = None

        url = reverse('horizon:project:volume_groups:delete',
                      args=[group.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_get.assert_called_once_with(test.IsHttpRequest(),
                                                    group.id)
        self.mock_group_delete.assert_called_once_with(test.IsHttpRequest(),
                                                       group.id,
                                                       delete_volumes=True)

    @test.create_mocks({cinder: ['group_get', 'group_delete']})
    def test_delete_group_exception(self):
        group = self.cinder_groups.first()
        formData = {'delete_volumes': False}

        self.mock_group_get.return_value = group
        self.mock_group_delete.side_effect = self.exceptions.cinder

        url = reverse('horizon:project:volume_groups:delete',
                      args=[group.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_get.assert_called_once_with(test.IsHttpRequest(),
                                                    group.id)
        self.mock_group_delete.assert_called_once_with(test.IsHttpRequest(),
                                                       group.id,
                                                       delete_volumes=False)

    def test_update_group_add_vol(self):
        self._test_update_group_add_remove_vol(add=True)

    def test_update_group_remove_vol(self):
        self._test_update_group_add_remove_vol(add=False)

    @test.create_mocks({cinder: ['volume_list',
                                 'volume_type_list',
                                 'group_get',
                                 'group_update']})
    def _test_update_group_add_remove_vol(self, add=True):
        group = self.cinder_groups.first()
        volume_types = self.cinder_volume_types.list()
        volumes = (self.cinder_volumes.list() +
                   self.cinder_group_volumes.list())

        group_voltype_names = [t.name for t in volume_types
                               if t.id in group.volume_types]
        compat_volumes = [v for v in volumes
                          if v.volume_type in group_voltype_names]
        compat_volume_ids = [v.id for v in compat_volumes]
        assigned_volume_ids = [v.id for v in compat_volumes
                               if getattr(v, 'group_id', None)]
        add_volume_ids = [v.id for v in compat_volumes
                          if v.id not in assigned_volume_ids]

        new_volums = compat_volume_ids if add else []
        formData = {
            'default_add_volumes_to_group_role': 'member',
            'add_volumes_to_group_role_member': new_volums,
        }

        self.mock_volume_list.return_value = volumes
        self.mock_volume_type_list.return_value = volume_types
        self.mock_group_get.return_value = group
        self.mock_group_update.return_value = group

        url = reverse('horizon:project:volume_groups:manage',
                      args=[group.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_volume_list, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_group_get.assert_called_once_with(
            test.IsHttpRequest(), group.id)
        if add:
            self.mock_group_update.assert_called_once_with(
                test.IsHttpRequest(), group.id,
                add_volumes=add_volume_ids,
                remove_volumes=[])
        else:
            self.mock_group_update.assert_called_once_with(
                test.IsHttpRequest(), group.id,
                add_volumes=[],
                remove_volumes=assigned_volume_ids)

    @test.create_mocks({cinder: ['group_get', 'group_update']})
    def test_update_group_name_and_description(self):
        group = self.cinder_groups.first()
        formData = {'name': 'test VG-new',
                    'description': 'test desc-new'}

        self.mock_group_get.return_value = group
        self.mock_group_update.return_value = group

        url = reverse('horizon:project:volume_groups:update',
                      args=[group.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_get.assert_called_once_with(
            test.IsHttpRequest(), group.id)
        self.mock_group_update.assert_called_once_with(
            test.IsHttpRequest(), group.id,
            formData['name'],
            formData['description'])

    @test.create_mocks({cinder: ['group_get', 'group_update']})
    def test_update_group_with_exception(self):
        group = self.cinder_groups.first()
        formData = {'name': 'test VG-new',
                    'description': 'test desc-new'}

        self.mock_group_get.return_value = group
        self.mock_group_update.side_effect = self.exceptions.cinder

        url = reverse('horizon:project:volume_groups:update',
                      args=[group.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_get.assert_called_once_with(
            test.IsHttpRequest(), group.id)
        self.mock_group_update.assert_called_once_with(
            test.IsHttpRequest(), group.id,
            formData['name'],
            formData['description'])

    @test.create_mocks({cinder: ['group_get']})
    def test_detail_view_with_exception(self):
        group = self.cinder_groups.first()

        self.mock_group_get.side_effect = self.exceptions.cinder

        url = reverse('horizon:project:volume_groups:detail',
                      args=[group.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_get.assert_called_once_with(
            test.IsHttpRequest(), group.id)

    @test.create_mocks({cinder: ['group_snapshot_create']})
    def test_create_snapshot(self):
        group = self.cinder_groups.first()
        group_snapshot = self.cinder_group_snapshots.first()
        formData = {'name': 'test VG Snapshot',
                    'description': 'test desc'}

        self.mock_group_snapshot_create.return_value = group_snapshot

        url = reverse('horizon:project:volume_groups:create_snapshot',
                      args=[group.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, VOLUME_GROUPS_SNAP_INDEX_URL)

        self.mock_group_snapshot_create.assert_called_once_with(
            test.IsHttpRequest(),
            group.id,
            formData['name'],
            formData['description'])

    @test.create_mocks({cinder: ['group_get', 'group_create_from_source']})
    def test_create_clone(self):
        group = self.cinder_groups.first()
        formData = {
            'group_source': group.id,
            'name': 'test VG Clone',
            'description': 'test desc',
        }
        self.mock_group_get.return_value = group
        self.mock_group_create_from_source.return_value = group

        url = reverse('horizon:project:volume_groups:clone_group',
                      args=[group.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_group_get.assert_called_once_with(
            test.IsHttpRequest(), group.id)
        self.mock_group_create_from_source.assert_called_once_with(
            test.IsHttpRequest(),
            formData['name'],
            source_group_id=group.id,
            description=formData['description'])
