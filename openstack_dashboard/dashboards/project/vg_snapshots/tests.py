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


INDEX_URL = reverse('horizon:project:vg_snapshots:index')


class GroupSnapshotTests(test.TestCase):
    @mock.patch.object(cinder, 'group_snapshot_get')
    @mock.patch.object(cinder, 'group_create_from_source')
    def test_create_group_from_snapshot(self,
                                        mock_group_create_from_source,
                                        mock_group_snapshot_get):
        group = self.cinder_groups.first()
        vg_snapshot = self.cinder_group_snapshots.first()
        formData = {'vg_snapshot_id': vg_snapshot.id,
                    'name': 'test VG SS Create',
                    'description': 'test desc'}

        mock_group_snapshot_get.return_value = vg_snapshot
        mock_group_create_from_source.return_value = group

        url = reverse('horizon:project:vg_snapshots:create_group',
                      args=[vg_snapshot.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(
            res, reverse('horizon:project:volume_groups:index'))

        mock_group_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), vg_snapshot.id)
        mock_group_create_from_source.assert_called_once_with(
            test.IsHttpRequest(),
            formData['name'],
            group_snapshot_id=formData['vg_snapshot_id'],
            description=formData['description'])

    @mock.patch.object(cinder, 'group_snapshot_get')
    @mock.patch.object(cinder, 'group_create_from_source')
    def test_create_group_from_snapshot_exception(
            self,
            mock_group_create_from_source,
            mock_group_snapshot_get):
        vg_snapshot = self.cinder_group_snapshots.first()
        new_cg_name = 'test VG SS Create'
        formData = {'vg_snapshot_id': vg_snapshot.id,
                    'name': new_cg_name,
                    'description': 'test desc'}

        mock_group_snapshot_get.return_value = vg_snapshot
        mock_group_create_from_source.side_effect = \
            self.exceptions.cinder

        url = reverse('horizon:project:vg_snapshots:create_group',
                      args=[vg_snapshot.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        # There are a bunch of backslashes for formatting in the message from
        # the response, so remove them when validating the error message.
        self.assertIn('Unable to create group "%s" from snapshot.'
                      % new_cg_name,
                      res.cookies.output().replace('\\', ''))
        self.assertRedirectsNoFollow(res, INDEX_URL)

        mock_group_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), vg_snapshot.id)
        mock_group_create_from_source.assert_called_once_with(
            test.IsHttpRequest(),
            formData['name'],
            group_snapshot_id=formData['vg_snapshot_id'],
            description=formData['description'])

    @mock.patch.object(cinder, 'group_snapshot_list')
    @mock.patch.object(cinder, 'group_snapshot_delete')
    @mock.patch.object(cinder, 'group_list')
    def test_delete_group_snapshot(self,
                                   mock_group_list,
                                   mock_group_snapshot_delete,
                                   mock_group_snapshot_list):
        vg_snapshots = self.cinder_group_snapshots.list()
        vg_snapshot = self.cinder_group_snapshots.first()

        mock_group_snapshot_list.return_value = vg_snapshots
        mock_group_snapshot_delete.return_value = None
        mock_group_list.return_value = self.cinder_groups.list()

        form_data = {'action': 'volume_vg_snapshots__delete_vg_snapshot__%s'
                     % vg_snapshot.id}
        res = self.client.post(INDEX_URL, form_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Scheduled deletion of Snapshot: %s" % vg_snapshot.name,
                      [m.message for m in res.context['messages']])

        self.assert_mock_multiple_calls_with_same_arguments(
            mock_group_snapshot_list, 2,
            mock.call(test.IsHttpRequest()))
        mock_group_snapshot_delete.assert_called_once_with(
            test.IsHttpRequest(), vg_snapshot.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            mock_group_list, 2,
            mock.call(test.IsHttpRequest()))

    @mock.patch.object(cinder, 'group_snapshot_list')
    @mock.patch.object(cinder, 'group_snapshot_delete')
    @mock.patch.object(cinder, 'group_list')
    def test_delete_group_snapshot_exception(self,
                                             mock_group_list,
                                             mock_group_snapshot_delete,
                                             mock_group_snapshot_list):
        vg_snapshots = self.cinder_group_snapshots.list()
        vg_snapshot = self.cinder_group_snapshots.first()

        mock_group_snapshot_list.return_value = vg_snapshots
        mock_group_snapshot_delete.side_effect = self.exceptions.cinder
        mock_group_list.return_value = self.cinder_groups.list()

        form_data = {'action': 'volume_vg_snapshots__delete_vg_snapshot__%s'
                     % vg_snapshot.id}
        res = self.client.post(INDEX_URL, form_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Unable to delete snapshot: %s" % vg_snapshot.name,
                      [m.message for m in res.context['messages']])

        self.assert_mock_multiple_calls_with_same_arguments(
            mock_group_snapshot_list, 2,
            mock.call(test.IsHttpRequest()))
        mock_group_snapshot_delete.assert_called_once_with(
            test.IsHttpRequest(), vg_snapshot.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            mock_group_list, 2,
            mock.call(test.IsHttpRequest()))

    @mock.patch.object(cinder, 'group_snapshot_get')
    @mock.patch.object(cinder, 'group_get')
    @mock.patch.object(cinder, 'volume_type_get')
    @mock.patch.object(cinder, 'volume_list')
    def test_detail_view(self,
                         mock_volume_list,
                         mock_volume_type_get,
                         mock_group_get,
                         mock_group_snapshot_get):
        vg_snapshot = self.cinder_group_snapshots.first()
        group = self.cinder_groups.first()
        volume_type = self.cinder_volume_types.first()
        volumes = self.cinder_volumes.list()

        mock_group_snapshot_get.return_value = vg_snapshot
        mock_group_get.return_value = group
        mock_volume_type_get.return_value = volume_type
        mock_volume_list.return_value = volumes

        url = reverse(
            'horizon:project:vg_snapshots:detail',
            args=[vg_snapshot.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 200)

        mock_group_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), vg_snapshot.id)
        mock_group_get.assert_called_once_with(
            test.IsHttpRequest(), group.id)
        mock_volume_type_get.assert_called_once_with(
            test.IsHttpRequest(), volume_type.id)
        search_opts = {'group_id': group.id}
        mock_volume_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=search_opts)

    @mock.patch.object(cinder, 'group_snapshot_get')
    def test_detail_view_with_exception(self, mock_group_snapshot_get):
        vg_snapshot = self.cinder_group_snapshots.first()

        mock_group_snapshot_get.side_effect = self.exceptions.cinder

        url = reverse(
            'horizon:project:vg_snapshots:detail',
            args=[vg_snapshot.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        mock_group_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), vg_snapshot.id)
