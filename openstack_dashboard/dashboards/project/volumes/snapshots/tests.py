# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


INDEX_URL = reverse('horizon:project:volumes:index')
VOLUME_SNAPSHOTS_TAB_URL = reverse('horizon:project:volumes:snapshots_tab')


class VolumeSnapshotsViewTests(test.TestCase):
    @test.create_stubs({cinder: ('volume_get',),
                        quotas: ('tenant_limit_usages',)})
    def test_create_snapshot_get(self):
        volume = self.cinder_volumes.first()
        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        snapshot_used = len(self.cinder_volume_snapshots.list())
        usage_limit = {'maxTotalVolumeGigabytes': 250,
                       'gigabytesUsed': 20,
                       'snapshotsUsed': snapshot_used,
                       'maxTotalSnapshots': 6}
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
            AndReturn(usage_limit)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:'
                      'volumes:create_snapshot', args=[volume.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/volumes/volumes/'
                                'create_snapshot.html')

    @test.create_stubs({cinder: ('volume_get',
                                 'volume_snapshot_create',)})
    def test_create_snapshot_post(self):
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()

        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        cinder.volume_snapshot_create(IsA(http.HttpRequest),
                                      volume.id,
                                      snapshot.name,
                                      snapshot.description,
                                      force=False) \
            .AndReturn(snapshot)
        self.mox.ReplayAll()

        formData = {'method': 'CreateSnapshotForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'name': snapshot.name,
                    'description': snapshot.description}
        url = reverse('horizon:project:volumes:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, VOLUME_SNAPSHOTS_TAB_URL)

    @test.create_stubs({cinder: ('volume_get',
                                 'volume_snapshot_create',)})
    def test_force_create_snapshot(self):
        volume = self.cinder_volumes.get(name='my_volume')
        snapshot = self.cinder_volume_snapshots.first()

        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
            .AndReturn(volume)
        cinder.volume_snapshot_create(IsA(http.HttpRequest),
                                      volume.id,
                                      snapshot.name,
                                      snapshot.description,
                                      force=True) \
            .AndReturn(snapshot)
        self.mox.ReplayAll()

        formData = {'method': 'CreateSnapshotForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'name': snapshot.name,
                    'description': snapshot.description}
        url = reverse('horizon:project:volumes:volumes:create_snapshot',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, VOLUME_SNAPSHOTS_TAB_URL)

    @test.create_stubs({api.cinder: ('volume_snapshot_list_paged',
                                     'volume_list',
                                     'volume_backup_supported',
                                     'volume_snapshot_delete',
                                     'tenant_absolute_limits')})
    def test_delete_volume_snapshot(self):
        vol_snapshots = self.cinder_volume_snapshots.list()
        volumes = self.cinder_volumes.list()
        snapshot = self.cinder_volume_snapshots.first()

        api.cinder.volume_backup_supported(IsA(http.HttpRequest)). \
            MultipleTimes().AndReturn(True)
        api.cinder.volume_snapshot_list_paged(
            IsA(http.HttpRequest), paginate=True, marker=None,
            sort_dir='desc').AndReturn([vol_snapshots, False, False])
        api.cinder.volume_list(IsA(http.HttpRequest)). \
            AndReturn(volumes)

        api.cinder.volume_snapshot_delete(IsA(http.HttpRequest), snapshot.id)
        self.mox.ReplayAll()

        formData = {'action':
                    'volume_snapshots__delete__%s' % snapshot.id}
        res = self.client.post(VOLUME_SNAPSHOTS_TAB_URL, formData)

        self.assertRedirectsNoFollow(res, VOLUME_SNAPSHOTS_TAB_URL)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.cinder: ('volume_snapshot_get', 'volume_get')})
    def test_volume_snapshot_detail_get(self):
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()

        api.cinder.volume_get(IsA(http.HttpRequest), volume.id). \
            AndReturn(volume)
        api.cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id). \
            AndReturn(snapshot)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['snapshot'].id, snapshot.id)

    @test.create_stubs({api.cinder: ('volume_snapshot_get',)})
    def test_volume_snapshot_detail_get_with_exception(self):
        # Test to verify redirect if get volume snapshot fails
        snapshot = self.cinder_volume_snapshots.first()

        api.cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id).\
            AndRaise(self.exceptions.cinder)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.cinder: ('volume_snapshot_get', 'volume_get')})
    def test_volume_snapshot_detail_with_volume_get_exception(self):
        # Test to verify redirect if get volume fails
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()

        api.cinder.volume_get(IsA(http.HttpRequest), volume.id). \
            AndRaise(self.exceptions.cinder)
        api.cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id). \
            AndReturn(snapshot)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:snapshots:detail',
                      args=[snapshot.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({cinder: ('volume_snapshot_update',
                                 'volume_snapshot_get')})
    def test_update_snapshot(self):
        snapshot = self.cinder_volume_snapshots.first()

        cinder.volume_snapshot_get(IsA(http.HttpRequest), snapshot.id) \
            .AndReturn(snapshot)
        cinder.volume_snapshot_update(IsA(http.HttpRequest),
                                      snapshot.id,
                                      snapshot.name,
                                      snapshot.description) \
            .AndReturn(snapshot)
        self.mox.ReplayAll()

        formData = {'method': 'UpdateSnapshotForm',
                    'name': snapshot.name,
                    'description': snapshot.description}
        url = reverse(('horizon:project:volumes:snapshots:update'),
                      args=[snapshot.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)
