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
import mock

from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:cg_snapshots:index')


class CGroupSnapshotTests(test.TestCase):
    @test.create_mocks({cinder: ('volume_cg_snapshot_get',
                                 'volume_cgroup_create_from_source',)})
    def test_create_cgroup_from_snapshot(self):
        cgroup = self.cinder_consistencygroups.first()
        cg_snapshot = self.cinder_cg_snapshots.first()
        formData = {'cg_snapshot_id': cg_snapshot.id,
                    'name': 'test CG SS Create',
                    'description': 'test desc'}

        self.mock_volume_cg_snapshot_get.return_value = cg_snapshot
        self.mock_volume_cgroup_create_from_source.return_value = cgroup

        url = reverse('horizon:project:cg_snapshots:create_cgroup',
                      args=[cg_snapshot.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(
            res, reverse('horizon:project:cgroups:index'))

        self.mock_volume_cg_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), cg_snapshot.id)
        self.mock_volume_cgroup_create_from_source.assert_called_once_with(
            test.IsHttpRequest(),
            formData['name'],
            cg_snapshot_id=formData['cg_snapshot_id'],
            description=formData['description'])

    @test.create_mocks({cinder: ('volume_cg_snapshot_get',
                                 'volume_cgroup_create_from_source',)})
    def test_create_cgroup_from_snapshot_exception(self):
        cg_snapshot = self.cinder_cg_snapshots.first()
        new_cg_name = 'test CG SS Create'
        formData = {'cg_snapshot_id': cg_snapshot.id,
                    'name': new_cg_name,
                    'description': 'test desc'}

        self.mock_volume_cg_snapshot_get.return_value = cg_snapshot
        self.mock_volume_cgroup_create_from_source.side_effect = \
            self.exceptions.cinder

        url = reverse('horizon:project:cg_snapshots:create_cgroup',
                      args=[cg_snapshot.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        # There are a bunch of backslashes for formatting in the message from
        # the response, so remove them when validating the error message.
        self.assertIn('Unable to create consistency group "%s" from snapshot.'
                      % new_cg_name,
                      res.cookies.output().replace('\\', ''))
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_cg_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), cg_snapshot.id)
        self.mock_volume_cgroup_create_from_source.assert_called_once_with(
            test.IsHttpRequest(),
            formData['name'],
            cg_snapshot_id=formData['cg_snapshot_id'],
            description=formData['description'])

    @test.create_mocks({cinder: ('volume_cg_snapshot_list',
                                 'volume_cg_snapshot_delete',)})
    def test_delete_cgroup_snapshot(self):
        cg_snapshots = self.cinder_cg_snapshots.list()
        cg_snapshot = self.cinder_cg_snapshots.first()

        self.mock_volume_cg_snapshot_list.return_value = cg_snapshots
        self.mock_volume_cg_snapshot_delete.return_value = None

        form_data = {'action': 'volume_cg_snapshots__delete_cg_snapshot__%s'
                     % cg_snapshot.id}
        res = self.client.post(INDEX_URL, form_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Scheduled deletion of Snapshot: %s" % cg_snapshot.name,
                      [m.message for m in res.context['messages']])

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_volume_cg_snapshot_list, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_volume_cg_snapshot_delete.assert_called_once_with(
            test.IsHttpRequest(), cg_snapshot.id)

    @test.create_mocks({cinder: ('volume_cg_snapshot_list',
                                 'volume_cg_snapshot_delete',)})
    def test_delete_cgroup_snapshot_exception(self):
        cg_snapshots = self.cinder_cg_snapshots.list()
        cg_snapshot = self.cinder_cg_snapshots.first()

        self.mock_volume_cg_snapshot_list.return_value = cg_snapshots
        self.mock_volume_cg_snapshot_delete.side_effect = \
            self.exceptions.cinder

        form_data = {'action': 'volume_cg_snapshots__delete_cg_snapshot__%s'
                     % cg_snapshot.id}
        res = self.client.post(INDEX_URL, form_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Unable to delete snapshot: %s" % cg_snapshot.name,
                      [m.message for m in res.context['messages']])

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_volume_cg_snapshot_list, 2,
            mock.call(test.IsHttpRequest()))
        self.mock_volume_cg_snapshot_delete.assert_called_once_with(
            test.IsHttpRequest(), cg_snapshot.id)

    @test.create_mocks({cinder: ('volume_cg_snapshot_get',
                                 'volume_cgroup_get',
                                 'volume_type_get',
                                 'volume_list',)})
    def test_detail_view(self):
        cg_snapshot = self.cinder_cg_snapshots.first()
        cgroup = self.cinder_consistencygroups.first()
        volume_type = self.cinder_volume_types.first()
        volumes = self.cinder_volumes.list()

        self.mock_volume_cg_snapshot_get.return_value = cg_snapshot
        self.mock_volume_cgroup_get.return_value = cgroup
        self.mock_volume_type_get.return_value = volume_type
        self.mock_volume_list.return_value = volumes

        url = reverse(
            'horizon:project:cg_snapshots:cg_snapshot_detail',
            args=[cg_snapshot.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 200)

        self.mock_volume_cg_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), cg_snapshot.id)
        self.mock_volume_cgroup_get.assert_called_once_with(
            test.IsHttpRequest(), cgroup.id)
        self.mock_volume_type_get.assert_called_once_with(
            test.IsHttpRequest(), volume_type.id)
        search_opts = {'consistencygroup_id': cgroup.id}
        self.mock_volume_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=search_opts)

    @test.create_mocks({cinder: ('volume_cg_snapshot_get',)})
    def test_detail_view_with_exception(self):
        cg_snapshot = self.cinder_cg_snapshots.first()

        self.mock_volume_cg_snapshot_get.side_effect = self.exceptions.cinder

        url = reverse(
            'horizon:project:cg_snapshots:cg_snapshot_detail',
            args=[cg_snapshot.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_cg_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), cg_snapshot.id)
