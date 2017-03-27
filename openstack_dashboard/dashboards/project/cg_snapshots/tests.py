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
from mox3.mox import IsA

from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:cg_snapshots:index')


class CGroupSnapshotTests(test.TestCase):
    @test.create_stubs({cinder: ('volume_cg_snapshot_get',
                                 'volume_cgroup_create_from_source',)})
    def test_create_cgroup_from_snapshot(self):
        cgroup = self.cinder_consistencygroups.first()
        cg_snapshot = self.cinder_cg_snapshots.first()
        formData = {'cg_snapshot_id': cg_snapshot.id,
                    'name': 'test CG SS Create',
                    'description': 'test desc'}

        cinder.volume_cg_snapshot_get(IsA(http.HttpRequest), cg_snapshot.id).\
            AndReturn(cg_snapshot)
        cinder.volume_cgroup_create_from_source(
            IsA(http.HttpRequest),
            formData['name'],
            source_cgroup_id=formData['cg_snapshot_id'],
            description=formData['description'])\
            .AndReturn(cgroup)
        self.mox.ReplayAll()

        url = reverse('horizon:project:cg_snapshots:create_cgroup',
                      args=[cg_snapshot.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({cinder: ('volume_cg_snapshot_get',
                                 'volume_cgroup_create_from_source',)})
    def test_create_cgroup_from_snapshot_exception(self):
        cg_snapshot = self.cinder_cg_snapshots.first()
        new_cg_name = 'test CG SS Create'
        formData = {'cg_snapshot_id': cg_snapshot.id,
                    'name': new_cg_name,
                    'description': 'test desc'}

        cinder.volume_cg_snapshot_get(IsA(http.HttpRequest), cg_snapshot.id).\
            AndReturn(cg_snapshot)
        cinder.volume_cgroup_create_from_source(
            IsA(http.HttpRequest),
            formData['name'],
            source_cgroup_id=formData['cg_snapshot_id'],
            description=formData['description'])\
            .AndRaise(self.exceptions.cinder)
        self.mox.ReplayAll()

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

    @test.create_stubs({cinder: ('volume_cg_snapshot_list',
                                 'volume_cg_snapshot_delete',)})
    def test_delete_cgroup_snapshot(self):
        cg_snapshots = self.cinder_cg_snapshots.list()
        cg_snapshot = self.cinder_cg_snapshots.first()

        cinder.volume_cg_snapshot_list(IsA(http.HttpRequest)).\
            AndReturn(cg_snapshots)
        cinder.volume_cg_snapshot_delete(IsA(http.HttpRequest), cg_snapshot.id)
        self.mox.ReplayAll()

        form_data = {'action': 'volume_cg_snapshots__delete_cg_snapshot__%s'
                     % cg_snapshot.id}
        res = self.client.post(INDEX_URL, form_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Scheduled deletion of Snapshot: %s" % cg_snapshot.name,
                      [m.message for m in res.context['messages']])

    @test.create_stubs({cinder: ('volume_cg_snapshot_list',
                                 'volume_cg_snapshot_delete',)})
    def test_delete_cgroup_snapshot_exception(self):
        cg_snapshots = self.cinder_cg_snapshots.list()
        cg_snapshot = self.cinder_cg_snapshots.first()

        cinder.volume_cg_snapshot_list(IsA(http.HttpRequest)).\
            AndReturn(cg_snapshots)
        cinder.volume_cg_snapshot_delete(IsA(http.HttpRequest),
                                         cg_snapshot.id).\
            AndRaise(self.exceptions.cinder)
        self.mox.ReplayAll()

        form_data = {'action': 'volume_cg_snapshots__delete_cg_snapshot__%s'
                     % cg_snapshot.id}
        res = self.client.post(INDEX_URL, form_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Unable to delete snapshot: %s" % cg_snapshot.name,
                      [m.message for m in res.context['messages']])

    @test.create_stubs({cinder: ('volume_cg_snapshot_get',
                                 'volume_cgroup_get',
                                 'volume_type_get',
                                 'volume_list',)})
    def test_detail_view(self):
        cg_snapshot = self.cinder_cg_snapshots.first()
        cgroup = self.cinder_consistencygroups.first()
        volume_type = self.cinder_volume_types.first()
        volumes = self.cinder_volumes.list()

        cinder.volume_cg_snapshot_get(IsA(http.HttpRequest), cg_snapshot.id).\
            AndReturn(cg_snapshot)
        cinder.volume_cgroup_get(IsA(http.HttpRequest), cgroup.id).\
            AndReturn(cgroup)
        cinder.volume_type_get(IsA(http.HttpRequest), volume_type.id).\
            MultipleTimes().AndReturn(volume_type)
        search_opts = {'consistencygroup_id': cgroup.id}
        cinder.volume_list(IsA(http.HttpRequest), search_opts=search_opts).\
            AndReturn(volumes)

        self.mox.ReplayAll()

        url = reverse(
            'horizon:project:cg_snapshots:cg_snapshot_detail',
            args=[cg_snapshot.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertEqual(res.status_code, 200)

    @test.create_stubs({cinder: ('volume_cg_snapshot_get',)})
    def test_detail_view_with_exception(self):
        cg_snapshot = self.cinder_cg_snapshots.first()

        cinder.volume_cg_snapshot_get(IsA(http.HttpRequest), cg_snapshot.id).\
            AndRaise(self.exceptions.cinder)

        self.mox.ReplayAll()

        url = reverse(
            'horizon:project:cg_snapshots:cg_snapshot_detail',
            args=[cg_snapshot.id])
        res = self.client.get(url)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
