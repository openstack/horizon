# Copyright 2013 Mirantis Inc.
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
import six

from openstack_dashboard.contrib.trove import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:project:database_backups:index')
BACKUP_URL = reverse('horizon:project:database_backups:create')
DETAILS_URL = reverse('horizon:project:database_backups:detail', args=['id'])


class DatabasesBackupsTests(test.TestCase):
    @test.create_stubs({api.trove: ('backup_list', 'instance_get')})
    def test_index(self):
        api.trove.backup_list(IsA(http.HttpRequest))\
            .AndReturn(self.database_backups.list())

        api.trove.instance_get(IsA(http.HttpRequest),
                               IsA(str))\
            .MultipleTimes()\
            .AndReturn(self.databases.first())

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/database_backups/index.html')

    @test.create_stubs({api.trove: ('backup_list',)})
    def test_index_exception(self):
        api.trove.backup_list(IsA(http.HttpRequest))\
            .AndRaise(self.exceptions.trove)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(
            res, 'project/database_backups/index.html')
        self.assertEqual(res.status_code, 200)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.trove: ('instance_list',
                                    'backup_list',
                                    'backup_create')})
    def test_launch_backup(self):
        api.trove.instance_list(IsA(http.HttpRequest))\
            .AndReturn(self.databases.list())
        api.trove.backup_list(IsA(http.HttpRequest)) \
            .AndReturn(self.database_backups.list())

        database = self.databases.first()
        backupName = "NewBackup"
        backupDesc = "Backup Description"

        api.trove.backup_create(
            IsA(http.HttpRequest),
            backupName,
            database.id,
            backupDesc,
            "")

        self.mox.ReplayAll()

        post = {
            'name': backupName,
            'instance': database.id,
            'description': backupDesc,
            'parent': ""
        }
        res = self.client.post(BACKUP_URL, post)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.trove: ('instance_list', 'backup_list')})
    def test_launch_backup_exception(self):
        api.trove.instance_list(IsA(http.HttpRequest))\
            .AndRaise(self.exceptions.trove)
        api.trove.backup_list(IsA(http.HttpRequest)) \
            .AndReturn(self.database_backups.list())

        self.mox.ReplayAll()

        res = self.client.get(BACKUP_URL)
        self.assertMessageCount(res, error=1)
        self.assertTemplateUsed(res,
                                'project/database_backups/backup.html')

    @test.create_stubs({api.trove: ('instance_list',
                                    'backup_list',
                                    'backup_create')})
    def test_launch_backup_incr(self):
        api.trove.instance_list(IsA(http.HttpRequest)) \
            .AndReturn(self.databases.list())
        api.trove.backup_list(IsA(http.HttpRequest)) \
            .AndReturn(self.database_backups.list())

        database = self.databases.first()
        backupName = "NewBackup"
        backupDesc = "Backup Description"
        backupParent = self.database_backups.first()

        api.trove.backup_create(
            IsA(http.HttpRequest),
            backupName,
            database.id,
            backupDesc,
            backupParent.id)

        self.mox.ReplayAll()

        post = {
            'name': backupName,
            'instance': database.id,
            'description': backupDesc,
            'parent': backupParent.id,
        }
        res = self.client.post(BACKUP_URL, post)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.trove: ('backup_get', 'instance_get')})
    def test_detail_backup(self):
        api.trove.backup_get(IsA(http.HttpRequest),
                             IsA(six.text_type))\
            .AndReturn(self.database_backups.first())

        api.trove.instance_get(IsA(http.HttpRequest),
                               IsA(str))\
            .AndReturn(self.databases.first())

        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)

        self.assertTemplateUsed(res,
                                'project/database_backups/details.html')

    @test.create_stubs({api.trove: ('backup_get',)})
    def test_detail_backup_notfound(self):
        api.trove.backup_get(IsA(http.HttpRequest),
                             IsA(six.text_type))\
            .AndRaise(self.exceptions.trove)

        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.trove: ('backup_get', 'instance_get')})
    def test_detail_backup_incr(self):
        incr_backup = self.database_backups.list()[2]
        parent_backup = self.database_backups.list()[1]

        api.trove.backup_get(IsA(http.HttpRequest), IsA(six.text_type))\
            .AndReturn(incr_backup)
        api.trove.backup_get(IsA(http.HttpRequest), incr_backup.parent_id) \
            .AndReturn(parent_backup)
        api.trove.instance_get(IsA(http.HttpRequest), IsA(str))\
            .AndReturn(self.databases.list()[1])

        self.mox.ReplayAll()
        url = reverse('horizon:project:database_backups:detail',
                      args=[incr_backup.id])
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'project/database_backups/details.html')
