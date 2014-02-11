# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Mirantis Inc.
# Copyright 2013 Rackspace Hosting.
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

from troveclient import common


INDEX_URL = reverse('horizon:project:databases:index')
LAUNCH_URL = reverse('horizon:project:databases:launch')
DETAILS_URL = reverse('horizon:project:databases:detail', args=['id'])


class DatabaseTests(test.TestCase):
    @test.create_stubs(
        {api.trove: ('instance_list', 'flavor_list')})
    def test_index(self):
        # Mock database instances
        databases = common.Paginated(self.databases.list())
        api.trove.instance_list(IsA(http.HttpRequest), marker=None)\
            .AndReturn(databases)
        # Mock flavors
        api.trove.flavor_list(IsA(http.HttpRequest))\
            .AndReturn(self.flavors.list())

        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/databases/index.html')
        # Check the Host column displaying ip or hostname
        self.assertContains(res, '10.0.0.3')
        self.assertContains(res, 'trove.instance-2.com')

    @test.create_stubs(
        {api.trove: ('instance_list', 'flavor_list')})
    def test_index_flavor_exception(self):
        # Mock database instances
        databases = common.Paginated(self.databases.list())
        api.trove.instance_list(IsA(http.HttpRequest), marker=None)\
            .AndReturn(databases)
        # Mock flavors
        api.trove.flavor_list(IsA(http.HttpRequest))\
            .AndRaise(self.exceptions.trove)

        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/databases/index.html')
        self.assertMessageCount(res, error=1)

    @test.create_stubs(
        {api.trove: ('instance_list',)})
    def test_index_list_exception(self):
        # Mock database instances
        api.trove.instance_list(IsA(http.HttpRequest), marker=None)\
            .AndRaise(self.exceptions.trove)

        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/databases/index.html')
        self.assertMessageCount(res, error=1)

    @test.create_stubs(
        {api.trove: ('instance_list', 'flavor_list')})
    def test_index_pagination(self):
        # Mock database instances
        databases = self.databases.list()
        last_record = databases[-1]
        databases = common.Paginated(databases,
            next_marker="foo")
        api.trove.instance_list(IsA(http.HttpRequest), marker=None)\
            .AndReturn(databases)
        # Mock flavors
        api.trove.flavor_list(IsA(http.HttpRequest))\
            .AndReturn(self.flavors.list())

        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/databases/index.html')
        self.assertContains(
            res, 'marker=' + last_record.id)

    @test.create_stubs(
        {api.trove: ('instance_list', 'flavor_list')})
    def test_index_flavor_list_exception(self):
        #Mocking instances
        databases = common.Paginated(self.databases.list())
        api.trove.instance_list(IsA(http.HttpRequest), marker=None)\
            .AndReturn(databases)
        #Mocking flavor list with raising an exception
        api.trove.flavor_list(IsA(http.HttpRequest))\
            .AndRaise(self.exceptions.trove)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/databases/index.html')
        self.assertMessageCount(res, error=1)

    @test.create_stubs({
        api.trove: ('flavor_list', 'backup_list',)})
    def test_launch_instance(self):
        api.trove.flavor_list(IsA(http.HttpRequest))\
            .AndReturn(self.flavors.list())
        api.trove.backup_list(IsA(http.HttpRequest))\
            .AndReturn(self.database_backups.list())

        self.mox.ReplayAll()
        res = self.client.get(LAUNCH_URL)
        self.assertTemplateUsed(res, 'project/databases/launch.html')

    @test.create_stubs({
        api.trove: ('flavor_list', 'backup_list', 'instance_create',)})
    def test_create_simple_instance(self):
        api.trove.flavor_list(IsA(http.HttpRequest))\
            .AndReturn(self.flavors.list())
        api.trove.backup_list(IsA(http.HttpRequest))\
            .AndReturn(self.database_backups.list())

        # Actual create database call
        api.trove.instance_create(
            IsA(http.HttpRequest),
            IsA(unicode),
            IsA(int),
            IsA(unicode),
            databases=None,
            restore_point=None,
            users=None).AndReturn(self.databases.first())

        self.mox.ReplayAll()
        post = {
            'name': "MyDB",
            'volume': '1',
            'flavor': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        }

        res = self.client.post(LAUNCH_URL, post)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({
        api.trove: ('flavor_list', 'backup_list', 'instance_create',)})
    def test_create_simple_instance_exception(self):
        trove_exception = self.exceptions.nova
        api.trove.flavor_list(IsA(http.HttpRequest))\
            .AndReturn(self.flavors.list())
        api.trove.backup_list(IsA(http.HttpRequest))\
            .AndReturn(self.database_backups.list())

        # Actual create database call
        api.trove.instance_create(
            IsA(http.HttpRequest),
            IsA(unicode),
            IsA(int),
            IsA(unicode),
            databases=None,
            restore_point=None,
            users=None).AndRaise(trove_exception)

        self.mox.ReplayAll()
        post = {
            'name': "MyDB",
            'volume': '1',
            'flavor': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        }

        res = self.client.post(LAUNCH_URL, post)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs(
        {api.trove: ('instance_get', 'flavor_get',)})
    def _test_details(self, database, with_designate=False):
        api.trove.instance_get(IsA(http.HttpRequest), IsA(unicode))\
            .AndReturn(database)
        api.trove.flavor_get(IsA(http.HttpRequest), IsA(str))\
            .AndReturn(self.flavors.first())

        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res, 'project/databases/detail.html')
        if with_designate:
            self.assertContains(res, database.hostname)
        else:
            self.assertContains(res, database.ip[0])

    def test_details_with_ip(self):
        database = self.databases.first()
        self._test_details(database, with_designate=False)

    def test_details_with_hostname(self):
        database = self.databases.list()[1]
        self._test_details(database, with_designate=True)
