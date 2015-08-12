# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.core.urlresolvers import reverse
from django import http
from django.utils.http import urlencode
from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:volumes:index')
VOLUME_BACKUPS_TAB_URL = reverse('horizon:project:volumes:backups_tab')


class VolumeBackupsViewTests(test.TestCase):

    @test.create_stubs({api.cinder: ('volume_backup_create',)})
    def test_create_backup_post(self):
        volume = self.volumes.first()
        backup = self.cinder_volume_backups.first()

        api.cinder.volume_backup_create(IsA(http.HttpRequest),
                                        volume.id,
                                        backup.container_name,
                                        backup.name,
                                        backup.description) \
            .AndReturn(backup)
        self.mox.ReplayAll()

        formData = {'method': 'CreateBackupForm',
                    'tenant_id': self.tenant.id,
                    'volume_id': volume.id,
                    'container_name': backup.container_name,
                    'name': backup.name,
                    'description': backup.description}
        url = reverse('horizon:project:volumes:volumes:create_backup',
                      args=[volume.id])
        res = self.client.post(url, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=0, warning=0)
        self.assertRedirectsNoFollow(res, VOLUME_BACKUPS_TAB_URL)

    @test.create_stubs({api.cinder: ('volume_list',
                                     'volume_backup_supported',
                                     'volume_backup_list',
                                     'volume_backup_delete')})
    def test_delete_volume_backup(self):
        vol_backups = self.cinder_volume_backups.list()
        volumes = self.cinder_volumes.list()
        backup = self.cinder_volume_backups.first()

        api.cinder.volume_backup_supported(IsA(http.HttpRequest)). \
            MultipleTimes().AndReturn(True)
        api.cinder.volume_backup_list(IsA(http.HttpRequest)). \
            AndReturn(vol_backups)
        api.cinder.volume_list(IsA(http.HttpRequest)). \
            AndReturn(volumes)
        api.cinder.volume_backup_delete(IsA(http.HttpRequest), backup.id)

        api.cinder.volume_backup_list(IsA(http.HttpRequest)). \
            AndReturn(vol_backups)
        api.cinder.volume_list(IsA(http.HttpRequest)). \
            AndReturn(volumes)
        self.mox.ReplayAll()

        formData = {'action':
                    'volume_backups__delete__%s' % backup.id}
        res = self.client.post(INDEX_URL +
                               "?tab=volumes_and_snapshots__backups_tab",
                               formData, follow=True)

        self.assertIn("Scheduled deletion of Volume Backup: backup1",
                      [m.message for m in res.context['messages']])

    @test.create_stubs({api.cinder: ('volume_backup_get', 'volume_get')})
    def test_volume_backup_detail_get(self):
        backup = self.cinder_volume_backups.first()
        volume = self.cinder_volumes.get(id=backup.volume_id)

        api.cinder.volume_backup_get(IsA(http.HttpRequest), backup.id). \
            AndReturn(backup)
        api.cinder.volume_get(IsA(http.HttpRequest), backup.volume_id). \
            AndReturn(volume)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:backups:detail',
                      args=[backup.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['backup'].id, backup.id)

    @test.create_stubs({api.cinder: ('volume_backup_get',)})
    def test_volume_backup_detail_get_with_exception(self):
        # Test to verify redirect if get volume backup fails
        backup = self.cinder_volume_backups.first()

        api.cinder.volume_backup_get(IsA(http.HttpRequest), backup.id).\
            AndRaise(self.exceptions.cinder)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:backups:detail',
                      args=[backup.id])
        res = self.client.get(url)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.cinder: ('volume_backup_get', 'volume_get')})
    def test_volume_backup_detail_with_missing_volume(self):
        # Test to check page still loads even if volume is deleted
        backup = self.cinder_volume_backups.first()

        api.cinder.volume_backup_get(IsA(http.HttpRequest), backup.id). \
            AndReturn(backup)
        api.cinder.volume_get(IsA(http.HttpRequest), backup.volume_id). \
            AndRaise(self.exceptions.cinder)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:backups:detail',
                      args=[backup.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['backup'].id, backup.id)

    @test.create_stubs({api.cinder: ('volume_list',
                                     'volume_backup_restore',)})
    def test_restore_backup(self):
        backup = self.cinder_volume_backups.first()
        volumes = self.cinder_volumes.list()

        api.cinder.volume_list(IsA(http.HttpRequest)). \
            AndReturn(volumes)
        api.cinder.volume_backup_restore(IsA(http.HttpRequest),
                                         backup.id,
                                         backup.volume_id). \
            AndReturn(backup)
        self.mox.ReplayAll()

        formData = {'method': 'RestoreBackupForm',
                    'backup_id': backup.id,
                    'backup_name': backup.name,
                    'volume_id': backup.volume_id}
        url = reverse('horizon:project:volumes:backups:restore',
                      args=[backup.id])
        url += '?%s' % urlencode({'backup_name': backup.name,
                                  'volume_id': backup.volume_id})
        res = self.client.post(url, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)
