# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from mox import IsA  # noqa

from openstack_dashboard import api
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

    @test.create_stubs({api.trove: ('instance_list',)})
    def test_launch_backup(self):
        api.trove.instance_list(IsA(http.HttpRequest))\
            .AndReturn([])

        self.mox.ReplayAll()

        res = self.client.get(BACKUP_URL)
        self.assertTemplateUsed(res,
            'project/database_backups/backup.html')

    @test.create_stubs({api.trove: ('instance_list',)})
    def test_launch_backup_exception(self):
        api.trove.instance_list(IsA(http.HttpRequest))\
            .AndRaise(self.exceptions.trove)

        self.mox.ReplayAll()

        res = self.client.get(BACKUP_URL)
        self.assertMessageCount(res, error=1)
        self.assertTemplateUsed(res,
            'project/database_backups/backup.html')

    @test.create_stubs({api.trove: ('backup_get', 'instance_get')})
    def test_detail_backup(self):
        api.trove.backup_get(IsA(http.HttpRequest),
                             IsA(unicode))\
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
                             IsA(unicode))\
            .AndRaise(self.exceptions.trove)

        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)

        self.assertRedirectsNoFollow(res, INDEX_URL)
