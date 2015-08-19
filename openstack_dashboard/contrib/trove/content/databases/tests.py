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

import logging

import django
from django.core.urlresolvers import reverse
from django import http
from django.utils import unittest

from mox3.mox import IsA  # noqa
import six

from horizon import exceptions
from openstack_dashboard import api as dash_api
from openstack_dashboard.contrib.trove import api
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
        last_record = databases[1]
        databases = common.Paginated(databases, next_marker="foo")
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
        # Mocking instances.
        databases = common.Paginated(self.databases.list())
        api.trove.instance_list(
            IsA(http.HttpRequest),
            marker=None,
        ).AndReturn(databases)
        # Mocking flavor list with raising an exception.
        api.trove.flavor_list(
            IsA(http.HttpRequest),
        ).AndRaise(self.exceptions.trove)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/databases/index.html')
        self.assertMessageCount(res, error=1)

    @test.create_stubs({
        api.trove: ('flavor_list', 'backup_list',
                    'datastore_list', 'datastore_version_list',
                    'instance_list'),
        dash_api.neutron: ('network_list',)})
    def test_launch_instance(self):
        api.trove.flavor_list(IsA(http.HttpRequest)).AndReturn(
            self.flavors.list())
        api.trove.backup_list(IsA(http.HttpRequest)).AndReturn(
            self.database_backups.list())
        api.trove.instance_list(IsA(http.HttpRequest)).AndReturn(
            self.databases.list())
        # Mock datastores
        api.trove.datastore_list(IsA(http.HttpRequest)).AndReturn(
            self.datastores.list())
        # Mock datastore versions
        api.trove.datastore_version_list(IsA(http.HttpRequest), IsA(str)).\
            AndReturn(self.datastore_versions.list())

        dash_api.neutron.network_list(IsA(http.HttpRequest),
                                      tenant_id=self.tenant.id,
                                      shared=False).AndReturn(
                                          self.networks.list()[:1])

        dash_api.neutron.network_list(IsA(http.HttpRequest),
                                      shared=True).AndReturn(
                                          self.networks.list()[1:])

        self.mox.ReplayAll()
        res = self.client.get(LAUNCH_URL)
        self.assertTemplateUsed(res, 'project/databases/launch.html')

    # django 1.7 and later does not handle the thrown Http302
    # exception well enough.
    # TODO(mrunge): re-check when django-1.8 is stable
    @unittest.skipIf(django.VERSION >= (1, 7, 0),
                     'Currently skipped with Django >= 1.7')
    @test.create_stubs({api.trove: ('flavor_list',)})
    def test_launch_instance_exception_on_flavors(self):
        trove_exception = self.exceptions.nova
        api.trove.flavor_list(IsA(http.HttpRequest)).AndRaise(trove_exception)
        self.mox.ReplayAll()

        toSuppress = ["openstack_dashboard.dashboards.project.databases."
                      "workflows.create_instance",
                      "horizon.workflows.base"]

        # Suppress expected log messages in the test output
        loggers = []
        for cls in toSuppress:
            logger = logging.getLogger(cls)
            loggers.append((logger, logger.getEffectiveLevel()))
            logger.setLevel(logging.CRITICAL)

        try:
            with self.assertRaises(exceptions.Http302):
                self.client.get(LAUNCH_URL)

        finally:
            # Restore the previous log levels
            for (log, level) in loggers:
                log.setLevel(level)

    @test.create_stubs({
        api.trove: ('flavor_list', 'backup_list', 'instance_create',
                    'datastore_list', 'datastore_version_list',
                    'instance_list'),
        dash_api.neutron: ('network_list',)})
    def test_create_simple_instance(self):
        api.trove.flavor_list(IsA(http.HttpRequest)).AndReturn(
            self.flavors.list())

        api.trove.backup_list(IsA(http.HttpRequest)).AndReturn(
            self.database_backups.list())

        api.trove.instance_list(IsA(http.HttpRequest)).AndReturn(
            self.databases.list())

        # Mock datastores
        api.trove.datastore_list(IsA(http.HttpRequest))\
            .AndReturn(self.datastores.list())

        # Mock datastore versions
        api.trove.datastore_version_list(IsA(http.HttpRequest), IsA(str))\
            .AndReturn(self.datastore_versions.list())

        dash_api.neutron.network_list(IsA(http.HttpRequest),
                                      tenant_id=self.tenant.id,
                                      shared=False).AndReturn(
                                          self.networks.list()[:1])

        dash_api.neutron.network_list(IsA(http.HttpRequest),
                                      shared=True).AndReturn(
                                          self.networks.list()[1:])

        nics = [{"net-id": self.networks.first().id, "v4-fixed-ip": ''}]

        # Actual create database call
        api.trove.instance_create(
            IsA(http.HttpRequest),
            IsA(six.text_type),
            IsA(int),
            IsA(six.text_type),
            databases=None,
            datastore=IsA(six.text_type),
            datastore_version=IsA(six.text_type),
            restore_point=None,
            replica_of=None,
            users=None,
            nics=nics).AndReturn(self.databases.first())

        self.mox.ReplayAll()
        post = {
            'name': "MyDB",
            'volume': '1',
            'flavor': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            'network': self.networks.first().id,
            'datastore': 'mysql,5.5',
        }

        res = self.client.post(LAUNCH_URL, post)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({
        api.trove: ('flavor_list', 'backup_list', 'instance_create',
                    'datastore_list', 'datastore_version_list',
                    'instance_list'),
        dash_api.neutron: ('network_list',)})
    def test_create_simple_instance_exception(self):
        trove_exception = self.exceptions.nova
        api.trove.flavor_list(IsA(http.HttpRequest)).AndReturn(
            self.flavors.list())

        api.trove.backup_list(IsA(http.HttpRequest)).AndReturn(
            self.database_backups.list())

        api.trove.instance_list(IsA(http.HttpRequest)).AndReturn(
            self.databases.list())

        # Mock datastores
        api.trove.datastore_list(IsA(http.HttpRequest))\
            .AndReturn(self.datastores.list())

        # Mock datastore versions
        api.trove.datastore_version_list(IsA(http.HttpRequest), IsA(str))\
            .AndReturn(self.datastore_versions.list())

        dash_api.neutron.network_list(IsA(http.HttpRequest),
                                      tenant_id=self.tenant.id,
                                      shared=False).AndReturn(
                                          self.networks.list()[:1])

        dash_api.neutron.network_list(IsA(http.HttpRequest),
                                      shared=True).AndReturn(
                                          self.networks.list()[1:])

        nics = [{"net-id": self.networks.first().id, "v4-fixed-ip": ''}]

        # Actual create database call
        api.trove.instance_create(
            IsA(http.HttpRequest),
            IsA(six.text_type),
            IsA(int),
            IsA(six.text_type),
            databases=None,
            datastore=IsA(six.text_type),
            datastore_version=IsA(six.text_type),
            restore_point=None,
            replica_of=None,
            users=None,
            nics=nics).AndRaise(trove_exception)

        self.mox.ReplayAll()
        post = {
            'name': "MyDB",
            'volume': '1',
            'flavor': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            'network': self.networks.first().id,
            'datastore': 'mysql,5.5',
        }

        res = self.client.post(LAUNCH_URL, post)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs(
        {api.trove: ('instance_get', 'flavor_get',)})
    def _test_details(self, database, with_designate=False):
        api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))\
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

    @test.create_stubs(
        {api.trove: ('instance_get', 'flavor_get', 'users_list',
                     'user_list_access', 'user_delete')})
    def test_user_delete(self):
        database = self.databases.first()
        user = self.database_users.first()
        user_db = self.database_user_dbs.first()

        database_id = database.id
        # Instead of using the user's ID, the api uses the user's name. BOOO!
        user_id = user.name

        # views.py: DetailView.get_data
        api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))\
            .AndReturn(database)
        api.trove.flavor_get(IsA(http.HttpRequest), IsA(str))\
            .AndReturn(self.flavors.first())

        # tabs.py: UserTab.get_user_data
        api.trove.users_list(IsA(http.HttpRequest),
                             database_id).AndReturn([user])
        api.trove.user_list_access(IsA(http.HttpRequest),
                                   database_id,
                                   user_id).AndReturn([user_db])

        # tables.py: DeleteUser.delete
        api.trove.user_delete(IsA(http.HttpRequest),
                              database_id,
                              user_id).AndReturn(None)

        self.mox.ReplayAll()

        details_url = reverse('horizon:project:databases:detail',
                              args=[database_id])
        url = details_url + '?tab=instance_details__users_tab'
        action_string = u"users__delete__%s" % user_id
        form_data = {'action': action_string}
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({
        api.trove: ('instance_get', 'instance_resize_volume')})
    def test_resize_volume(self):
        database = self.databases.first()
        database_id = database.id
        database_size = database.volume.get('size')

        # views.py: DetailView.get_data
        api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))\
            .AndReturn(database)

        # forms.py: ResizeVolumeForm.handle
        api.trove.instance_resize_volume(IsA(http.HttpRequest),
                                         database_id,
                                         IsA(int)).AndReturn(None)

        self.mox.ReplayAll()
        url = reverse('horizon:project:databases:resize_volume',
                      args=[database_id])
        post = {
            'instance_id': database_id,
            'orig_size': database_size,
            'new_size': database_size + 1,
        }
        res = self.client.post(url, post)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.trove: ('instance_get', )})
    def test_resize_volume_bad_value(self):
        database = self.databases.first()
        database_id = database.id
        database_size = database.volume.get('size')

        # views.py: DetailView.get_data
        api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))\
            .AndReturn(database)

        self.mox.ReplayAll()
        url = reverse('horizon:project:databases:resize_volume',
                      args=[database_id])
        post = {
            'instance_id': database_id,
            'orig_size': database_size,
            'new_size': database_size,
        }
        res = self.client.post(url, post)
        self.assertContains(
            res, "New size for volume must be greater than current size.")

    @test.create_stubs(
        {api.trove: ('instance_get',
                     'flavor_list')})
    def test_resize_instance_get(self):
        database = self.databases.first()

        # views.py: DetailView.get_data
        api.trove.instance_get(IsA(http.HttpRequest), database.id)\
            .AndReturn(database)
        api.trove.flavor_list(IsA(http.HttpRequest)).\
            AndReturn(self.database_flavors.list())

        self.mox.ReplayAll()
        url = reverse('horizon:project:databases:resize_instance',
                      args=[database.id])

        res = self.client.get(url)
        self.assertTemplateUsed(res, 'project/databases/resize_instance.html')
        option = '<option value="%s">%s</option>'
        for flavor in self.database_flavors.list():
            if flavor.id == database.flavor['id']:
                self.assertNotContains(res, option % (flavor.id, flavor.name))
            else:
                self.assertContains(res, option % (flavor.id, flavor.name))

    @test.create_stubs(
        {api.trove: ('instance_get',
                     'flavor_list',
                     'instance_resize')})
    def test_resize_instance(self):
        database = self.databases.first()

        # views.py: DetailView.get_data
        api.trove.instance_get(IsA(http.HttpRequest), database.id)\
            .AndReturn(database)
        api.trove.flavor_list(IsA(http.HttpRequest)).\
            AndReturn(self.database_flavors.list())

        old_flavor = self.database_flavors.list()[0]
        new_flavor = self.database_flavors.list()[1]

        api.trove.instance_resize(IsA(http.HttpRequest),
                                  database.id,
                                  new_flavor.id).AndReturn(None)

        self.mox.ReplayAll()
        url = reverse('horizon:project:databases:resize_instance',
                      args=[database.id])
        post = {
            'instance_id': database.id,
            'old_flavor_name': old_flavor.name,
            'old_flavor_id': old_flavor.id,
            'new_flavor': new_flavor.id
        }
        res = self.client.post(url, post)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({
        api.trove: ('flavor_list', 'backup_list', 'instance_create',
                    'datastore_list', 'datastore_version_list',
                    'instance_list', 'instance_get'),
        dash_api.neutron: ('network_list',)})
    def test_create_replica_instance(self):
        api.trove.flavor_list(IsA(http.HttpRequest)).AndReturn(
            self.flavors.list())

        api.trove.backup_list(IsA(http.HttpRequest)).AndReturn(
            self.database_backups.list())

        api.trove.instance_list(IsA(http.HttpRequest)).AndReturn(
            self.databases.list())

        api.trove.datastore_list(IsA(http.HttpRequest))\
            .AndReturn(self.datastores.list())

        api.trove.datastore_version_list(IsA(http.HttpRequest),
                                         IsA(str))\
            .AndReturn(self.datastore_versions.list())

        dash_api.neutron.network_list(IsA(http.HttpRequest),
                                      tenant_id=self.tenant.id,
                                      shared=False).\
            AndReturn(self.networks.list()[:1])

        dash_api.neutron.network_list(IsA(http.HttpRequest),
                                      shared=True).\
            AndReturn(self.networks.list()[1:])

        nics = [{"net-id": self.networks.first().id, "v4-fixed-ip": ''}]

        api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))\
            .AndReturn(self.databases.first())

        # Actual create database call
        api.trove.instance_create(
            IsA(http.HttpRequest),
            IsA(six.text_type),
            IsA(int),
            IsA(six.text_type),
            databases=None,
            datastore=IsA(six.text_type),
            datastore_version=IsA(six.text_type),
            restore_point=None,
            replica_of=self.databases.first().id,
            users=None,
            nics=nics).AndReturn(self.databases.first())

        self.mox.ReplayAll()
        post = {
            'name': "MyDB",
            'volume': '1',
            'flavor': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            'network': self.networks.first().id,
            'datastore': 'mysql,5.5',
            'initial_state': 'master',
            'master': self.databases.first().id
        }

        res = self.client.post(LAUNCH_URL, post)
        self.assertRedirectsNoFollow(res, INDEX_URL)
