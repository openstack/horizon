# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from collections import OrderedDict
import json
import logging
import sys

import django
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME  # noqa
from django.core.urlresolvers import reverse
from django.forms import widgets
from django import http
import django.test
from django.utils.http import urlencode
from mox3.mox import IgnoreArg  # noqa
from mox3.mox import IsA  # noqa
import six

from horizon import exceptions
from horizon import forms
from horizon.workflows import views
from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.dashboards.project.instances import console
from openstack_dashboard.dashboards.project.instances import tables
from openstack_dashboard.dashboards.project.instances import tabs
from openstack_dashboard.dashboards.project.instances import workflows
from openstack_dashboard.test import helpers
from openstack_dashboard.usage import quotas


INDEX_URL = reverse('horizon:project:instances:index')
SEC_GROUP_ROLE_PREFIX = \
    workflows.update_instance.INSTANCE_SEC_GROUP_SLUG + "_role_"
AVAILABLE = api.cinder.VOLUME_STATE_AVAILABLE
VOLUME_SEARCH_OPTS = dict(status=AVAILABLE, bootable=True)
SNAPSHOT_SEARCH_OPTS = dict(status=AVAILABLE)


class InstanceTests(helpers.TestCase):
    @helpers.create_stubs({
        api.nova: (
            'flavor_list',
            'server_list',
            'tenant_absolute_limits',
            'extension_supported',
        ),
        api.glance: ('image_list_detailed',),
        api.network: (
            'floating_ip_simple_associate_supported',
            'floating_ip_supported',
            'servers_update_addresses',
        ),
    })
    def _get_index(self):
        servers = self.servers.list()
        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
           .MultipleTimes().AndReturn(self.limits['absolute'])
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        return self.client.get(INDEX_URL)

    def test_index(self):

        res = self._get_index()

        self.assertTemplateUsed(res,
                                'project/instances/index.html')
        instances = res.context['instances_table'].data

        self.assertItemsEqual(instances, self.servers.list())
        self.assertNotContains(res, "Launch Instance (Quota exceeded)")

    @helpers.create_stubs({api.nova: ('server_list',
                                      'tenant_absolute_limits',)})
    def test_index_server_list_exception(self):
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndRaise(self.exceptions.nova)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
           .MultipleTimes().AndReturn(self.limits['absolute'])

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/instances/index.html')
        self.assertEqual(len(res.context['instances_table'].data), 0)
        self.assertMessageCount(res, error=1)

    @helpers.create_stubs({
        api.nova: ('flavor_list', 'server_list', 'flavor_get',
                   'tenant_absolute_limits', 'extension_supported',),
        api.glance: ('image_list_detailed',),
        api.network: ('floating_ip_simple_associate_supported',
                      'floating_ip_supported',
                      'servers_update_addresses',),
    })
    def test_index_flavor_list_exception(self):
        servers = self.servers.list()
        flavors = self.flavors.list()
        full_flavors = OrderedDict([(f.id, f) for f in flavors])
        search_opts = {'marker': None, 'paginate': True}
        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndRaise(self.exceptions.nova)
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        for server in servers:
            api.nova.flavor_get(IsA(http.HttpRequest), server.flavor["id"]). \
                AndReturn(full_flavors[server.flavor["id"]])
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
           .MultipleTimes().AndReturn(self.limits['absolute'])
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/instances/index.html')
        instances = res.context['instances_table'].data

        self.assertItemsEqual(instances, self.servers.list())

    @helpers.create_stubs({
        api.nova: ('flavor_list', 'server_list', 'tenant_absolute_limits',
                   'extension_supported',),
        api.glance: ('image_list_detailed',),
        api.network: ('floating_ip_simple_associate_supported',
                      'floating_ip_supported',
                      'servers_update_addresses',),
    })
    def test_index_with_instance_booted_from_volume(self):
        volume_server = self.servers.first()
        volume_server.image = ""
        volume_server.image_name = "(not found)"
        servers = self.servers.list()
        servers[0] = volume_server

        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
           .MultipleTimes().AndReturn(self.limits['absolute'])
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/instances/index.html')
        instances = res.context['instances_table'].data
        self.assertEqual(len(instances), len(servers))
        self.assertContains(res, "(not found)")

    def test_index_with_console_link(self):
        res = self._get_index()

        instances_table = res.context['instances_table']
        instances = res.context['instances_table'].data
        console_link_rendered = False
        for instance in instances:
            for action in instances_table.get_row_actions(instance):
                if isinstance(action, tables.ConsoleLink):
                    console_link_rendered = True
                    break
            if console_link_rendered:
                break
            self.assertTrue(console_link_rendered)

    @django.test.utils.override_settings(CONSOLE_TYPE=None)
    def test_index_without_console_link(self):
        res = self._get_index()

        instances_table = res.context['instances_table']
        instances = res.context['instances_table'].data
        for instance in instances:
            for action in instances_table.get_row_actions(instance):
                self.assertNotIsInstance(action, tables.ConsoleLink)

    @helpers.create_stubs({api.nova: ('server_list',
                                      'flavor_list',
                                      'server_delete',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_delete_instance(self):
        servers = self.servers.list()
        server = servers[0]

        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        api.nova.server_delete(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        formData = {'action': 'instances__delete__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_list',
                                      'flavor_list',
                                      'server_delete',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_delete_instance_error_state(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = 'ERROR'

        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        api.nova.server_delete(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        formData = {'action': 'instances__delete__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_list',
                                      'flavor_list',
                                      'server_delete',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_delete_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        api.nova.server_delete(IsA(http.HttpRequest), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__delete__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_pause',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_pause_instance(self):
        servers = self.servers.list()
        server = servers[0]

        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_pause(IsA(http.HttpRequest), server.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_pause',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_pause_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_pause(IsA(http.HttpRequest), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_unpause',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_unpause_instance(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "PAUSED"
        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_unpause(IsA(http.HttpRequest), server.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_unpause',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_unpause_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "PAUSED"

        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_unpause(IsA(http.HttpRequest), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_reboot',
                                      'server_list',
                                      'flavor_list',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_reboot_instance(self):
        servers = self.servers.list()
        server = servers[0]
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_reboot(IsA(http.HttpRequest), server.id,
                               soft_reboot=False)

        self.mox.ReplayAll()

        formData = {'action': 'instances__reboot__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_reboot',
                                      'server_list',
                                      'flavor_list',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_reboot_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_reboot(IsA(http.HttpRequest), server.id,
                               soft_reboot=False) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__reboot__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_reboot',
                                      'server_list',
                                      'flavor_list',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_soft_reboot_instance(self):
        servers = self.servers.list()
        server = servers[0]

        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_reboot(IsA(http.HttpRequest), server.id,
                               soft_reboot=True)

        self.mox.ReplayAll()

        formData = {'action': 'instances__soft_reboot__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_suspend',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_suspend_instance(self):
        servers = self.servers.list()
        server = servers[0]

        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_suspend(IsA(http.HttpRequest),
                                six.text_type(server.id))

        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_suspend',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_suspend_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_suspend(IsA(http.HttpRequest), six.text_type(server.id)) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_resume',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_resume_instance(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "SUSPENDED"

        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_resume(IsA(http.HttpRequest), six.text_type(server.id))

        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_resume',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_resume_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "SUSPENDED"

        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_resume(IsA(http.HttpRequest),
                               six.text_type(server.id)) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_shelve',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_shelve_instance(self):
        servers = self.servers.list()
        server = servers[0]

        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_shelve(IsA(http.HttpRequest), six.text_type(server.id))

        self.mox.ReplayAll()

        formData = {'action': 'instances__shelve__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_shelve',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_shelve_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_shelve(IsA(http.HttpRequest),
                               six.text_type(server.id)) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__shelve__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_unshelve',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_unshelve_instance(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "SHELVED_OFFLOADED"

        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_unshelve(IsA(http.HttpRequest),
                                 six.text_type(server.id))

        self.mox.ReplayAll()

        formData = {'action': 'instances__shelve__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_unshelve',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_unshelve_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "SHELVED_OFFLOADED"

        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_unshelve(IsA(http.HttpRequest),
                                 six.text_type(server.id)) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__shelve__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_lock',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_lock_instance(self):
        servers = self.servers.list()
        server = servers[0]

        api.nova.extension_supported('AdminActions', IsA(
            http.HttpRequest)).MultipleTimes().AndReturn(True)
        api.glance.image_list_detailed(IgnoreArg()).AndReturn((
            self.images.list(), False, False))
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(
            IsA(http.HttpRequest),
            search_opts=search_opts).AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_lock(IsA(http.HttpRequest), server.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__lock__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_lock',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_lock_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        api.nova.extension_supported('AdminActions', IsA(
            http.HttpRequest)).MultipleTimes().AndReturn(True)
        api.glance.image_list_detailed(IgnoreArg()).AndReturn((
            self.images.list(), False, False))
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(
            IsA(http.HttpRequest),
            search_opts=search_opts).AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_lock(IsA(http.HttpRequest), server.id).AndRaise(
            self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__lock__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_unlock',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_unlock_instance(self):
        servers = self.servers.list()
        server = servers[0]
        api.nova.extension_supported('AdminActions', IsA(
            http.HttpRequest)).MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()).AndReturn((
            self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(
            IsA(http.HttpRequest),
            search_opts=search_opts).AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_unlock(IsA(http.HttpRequest), server.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__unlock__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_unlock',
                                      'server_list',
                                      'flavor_list',
                                      'extension_supported',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_unlock_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        api.nova.extension_supported('AdminActions', IsA(
            http.HttpRequest)).MultipleTimes().AndReturn(True)
        api.glance.image_list_detailed(IgnoreArg()).AndReturn((
            self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.server_list(
            IsA(http.HttpRequest),
            search_opts=search_opts).AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_unlock(IsA(http.HttpRequest), server.id).AndRaise(
            self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__unlock__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({
        api.nova: (
            "server_get",
            "instance_volumes_list",
            "flavor_get",
            "extension_supported"
        ),
        api.network: (
            "server_security_groups",
            "servers_update_addresses",
            "floating_ip_simple_associate_supported",
            "floating_ip_supported"
        )
    })
    def _get_instance_details(self, server, qs=None,
                              flavor_return=None, volumes_return=None,
                              security_groups_return=None,
                              flavor_exception=False):

        url = reverse('horizon:project:instances:detail', args=[server.id])
        if qs:
            url += qs

        if flavor_return is None:
            flavor_return = self.flavors.first()

        if volumes_return is None:
            volumes_return = []

        if security_groups_return is None:
            security_groups_return = self.security_groups.list()

        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.network.servers_update_addresses(IsA(http.HttpRequest),
                                             IgnoreArg())
        api.nova.instance_volumes_list(IsA(http.HttpRequest),
                                       server.id).AndReturn(volumes_return)
        if flavor_exception:
            api.nova.flavor_get(IsA(http.HttpRequest), server.flavor['id']) \
                    .AndRaise(self.exceptions.nova)
        else:
            api.nova.flavor_get(IsA(http.HttpRequest), server.flavor['id']) \
                    .AndReturn(flavor_return)
        api.network.server_security_groups(IsA(http.HttpRequest), server.id) \
            .AndReturn(security_groups_return)
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('AdminActions', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        return self.client.get(url)

    def test_instance_details_volumes(self):
        server = self.servers.first()
        volumes = [self.volumes.list()[1]]
        security_groups = self.security_groups.list()

        res = self._get_instance_details(
            server, volumes_return=volumes,
            security_groups_return=security_groups)

        self.assertItemsEqual(res.context['instance'].volumes, volumes)

    def test_instance_details_volume_sorting(self):
        server = self.servers.first()
        volumes = self.volumes.list()[1:3]
        security_groups = self.security_groups.list()

        res = self._get_instance_details(
            server, volumes_return=volumes,
            security_groups_return=security_groups)

        self.assertItemsEqual(res.context['instance'].volumes, volumes)
        self.assertEqual(res.context['instance'].volumes[0].device,
                         "/dev/hda")
        self.assertEqual(res.context['instance'].volumes[1].device,
                         "/dev/hdk")

    def test_instance_details_metadata(self):
        server = self.servers.first()

        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("overview").get_id())
        res = self._get_instance_details(server, qs)

        self.assertContains(res, "<dd>keyName</dd>", 1)
        self.assertContains(res, "<dt>someMetaLabel</dt>", 1)
        self.assertContains(res, "<dd>someMetaData</dd>", 1)
        self.assertContains(res, "<dt>some&lt;b&gt;html&lt;/b&gt;label</dt>",
                            1)
        self.assertContains(res, "<dd>&lt;!--</dd>", 1)
        self.assertContains(res, "<dt>empty</dt>", 1)
        self.assertContains(res, "<dd><em>N/A</em></dd>", 1)

    def test_instance_details_fault(self):
        server = self.servers.first()

        server.status = 'ERROR'
        server.fault = {"message": "NoValidHost",
                        "code": 500,
                        "details": "No valid host was found. \n  "
                                   "File \"/mnt/stack/nova/nova/"
                                   "scheduler/filter_scheduler.py\", "
                                   "line 105, in schedule_run_instance\n    "
                                   "raise exception.NoValidHost"
                                   "(reason=\"\")\n",
                        "created": "2013-10-07T00:08:32Z"}

        res = self._get_instance_details(server)
        self.assertItemsEqual(res.context['instance'].fault, server.fault)

    @helpers.create_stubs({console: ('get_console',)})
    def test_instance_details_console_tab(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/vncserver'
        CONSOLE_TITLE = '&title=%s(%s)' % (server.name, server.id)
        CONSOLE_URL = CONSOLE_OUTPUT + CONSOLE_TITLE

        console_mock = self.mox.CreateMock(api.nova.VNCConsole)
        console_mock.url = CONSOLE_OUTPUT

        console.get_console(IgnoreArg(), 'AUTO', server) \
            .AndReturn(('VNC', CONSOLE_URL))

        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("console").get_id())
        res = self._get_instance_details(server, qs)
        self.assertIn(tabs.ConsoleTab, res.context_data['tab_group'].tabs)
        self.assertTemplateUsed(res,
                                'project/instances/_detail_console.html')
        console_tab_rendered = False
        for tab in res.context_data['tab_group'].get_loaded_tabs():
            if isinstance(tab, tabs.ConsoleTab):
                console_tab_rendered = True
                break
        self.assertTrue(console_tab_rendered)

    @django.test.utils.override_settings(CONSOLE_TYPE=None)
    def test_instance_details_console_tab_deactivated(self):
        server = self.servers.first()

        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        self.assertIsNone(tg.get_tab("console"))
        res = self._get_instance_details(server)
        self.assertTemplateNotUsed(res,
                                   'project/instances/_detail_console.html')
        for tab in res.context_data['tab_group'].get_loaded_tabs():
            self.assertNotIsInstance(tab, tabs.ConsoleTab)

    @helpers.create_stubs({api.nova: ('server_get',)})
    def test_instance_details_exception(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:detail',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ("server_get",)})
    def test_instance_details_unauthorized(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id)\
            .AndRaise(self.exceptions.nova_unauthorized)
        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:detail',
                      args=[server.id])

        # Avoid the log message in the test
        # when unauthorized exception will be logged
        logging.disable(logging.ERROR)
        res = self.client.get(url)
        logging.disable(logging.NOTSET)

        self.assertEqual(302, res.status_code)
        self.assertEqual(('Location', settings.TESTSERVER +
                          settings.LOGIN_URL + '?' +
                          REDIRECT_FIELD_NAME + '=' + url),
                         res._headers.get('location', None),)

    def test_instance_details_flavor_not_found(self):
        server = self.servers.first()
        res = self._get_instance_details(server, flavor_exception=True)
        self.assertTemplateUsed(res,
                                'project/instances/_detail_overview.html')
        self.assertContains(res, "Not available")

    @helpers.create_stubs({api.nova: ('server_console_output',)})
    def test_instance_log(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = 'output'

        api.nova.server_console_output(IsA(http.HttpRequest),
                                       server.id, tail_length=None) \
            .AndReturn(CONSOLE_OUTPUT)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:console',
                      args=[server.id])
        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("log").get_id())
        res = self.client.get(url + qs)

        self.assertNoMessages()
        self.assertIsInstance(res, http.HttpResponse)
        self.assertContains(res, CONSOLE_OUTPUT)

    @helpers.create_stubs({api.nova: ('server_console_output',)})
    def test_instance_log_exception(self):
        server = self.servers.first()

        api.nova.server_console_output(IsA(http.HttpRequest),
                                       server.id, tail_length=None) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:console',
                      args=[server.id])
        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("log").get_id())
        res = self.client.get(url + qs)

        self.assertContains(res, "Unable to get log for")

    def test_instance_log_invalid_input(self):
        server = self.servers.first()

        url = reverse('horizon:project:instances:console',
                      args=[server.id])
        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        for length in ["-5", "x"]:
            qs = "?%s=%s&length=%s" % (tg.param_name,
                                       tg.get_tab("log").get_id(),
                                       length)
            res = self.client.get(url + qs)

            self.assertContains(res, "Unable to get log for")

    def test_instance_vnc(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/vncserver'
        CONSOLE_TITLE = '&title=%s(%s)' % (server.name, server.id)
        CONSOLE_URL = CONSOLE_OUTPUT + CONSOLE_TITLE

        console_mock = self.mox.CreateMock(api.nova.VNCConsole)
        console_mock.url = CONSOLE_OUTPUT

        self.mox.StubOutWithMock(api.nova, 'server_get')
        self.mox.StubOutWithMock(console, 'get_console')
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        console.get_console(IgnoreArg(), 'VNC', server) \
            .AndReturn(('VNC', CONSOLE_URL))

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:vnc',
                      args=[server.id])
        res = self.client.get(url)
        redirect = CONSOLE_URL
        self.assertRedirectsNoFollow(res, redirect)

    def test_instance_vnc_error(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api.nova, 'server_get')
        self.mox.StubOutWithMock(console, 'get_console')
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        console.get_console(IgnoreArg(), 'VNC', server) \
            .AndRaise(exceptions.NotAvailable('console'))

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:vnc',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_spice(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/spiceserver'
        CONSOLE_TITLE = '&title=%s(%s)' % (server.name, server.id)
        CONSOLE_URL = CONSOLE_OUTPUT + CONSOLE_TITLE

        console_mock = self.mox.CreateMock(api.nova.SPICEConsole)
        console_mock.url = CONSOLE_OUTPUT

        self.mox.StubOutWithMock(console, 'get_console')
        self.mox.StubOutWithMock(api.nova, 'server_get')
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        console.get_console(IgnoreArg(), 'SPICE', server) \
            .AndReturn(('SPICE', CONSOLE_URL))

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:spice',
                      args=[server.id])
        res = self.client.get(url)
        redirect = CONSOLE_URL
        self.assertRedirectsNoFollow(res, redirect)

    def test_instance_spice_exception(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(console, 'get_console')
        self.mox.StubOutWithMock(api.nova, 'server_get')
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        console.get_console(IgnoreArg(), 'SPICE', server) \
            .AndRaise(exceptions.NotAvailable('console'))

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:spice',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_rdp(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/rdpserver'
        CONSOLE_TITLE = '&title=%s(%s)' % (server.name, server.id)
        CONSOLE_URL = CONSOLE_OUTPUT + CONSOLE_TITLE

        console_mock = self.mox.CreateMock(api.nova.RDPConsole)
        console_mock.url = CONSOLE_OUTPUT

        self.mox.StubOutWithMock(console, 'get_console')
        self.mox.StubOutWithMock(api.nova, 'server_get')
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        console.get_console(IgnoreArg(), 'RDP', server) \
            .AndReturn(('RDP', CONSOLE_URL))

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:rdp',
                      args=[server.id])
        res = self.client.get(url)
        redirect = CONSOLE_URL
        self.assertRedirectsNoFollow(res, redirect)

    def test_instance_rdp_exception(self):
        server = self.servers.first()

        self.mox.StubOutWithMock(console, 'get_console')
        self.mox.StubOutWithMock(api.nova, 'server_get')
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        console.get_console(IgnoreArg(), 'RDP', server) \
            .AndRaise(exceptions.NotAvailable('console'))

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:rdp',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_get',
                                      'snapshot_create',
                                      'server_list',
                                      'flavor_list',
                                      'server_delete'),
                           api.glance: ('image_list_detailed',)})
    def test_create_instance_snapshot(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.nova.snapshot_create(IsA(http.HttpRequest),
                                 server.id,
                                 "snapshot1").AndReturn(self.snapshots.first())

        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True) \
            .AndReturn([[], False, False])

        self.mox.ReplayAll()

        formData = {'instance_id': server.id,
                    'method': 'CreateSnapshot',
                    'name': 'snapshot1'}
        url = reverse('horizon:project:images:snapshots:create',
                      args=[server.id])
        redir_url = reverse('horizon:project:images:index')
        res = self.client.post(url, formData)
        self.assertRedirects(res, redir_url)

    @django.test.utils.override_settings(
        OPENSTACK_ENABLE_PASSWORD_RETRIEVE=False)
    def test_instances_index_retrieve_password_action_disabled(self):
        self. _test_instances_index_retrieve_password_action()

    @django.test.utils.override_settings(
        OPENSTACK_ENABLE_PASSWORD_RETRIEVE=True)
    def test_instances_index_retrieve_password_action_enabled(self):
        self._test_instances_index_retrieve_password_action()

    @helpers.create_stubs({
        api.nova: ('flavor_list', 'server_list', 'tenant_absolute_limits',
                   'extension_supported',),
        api.glance: ('image_list_detailed',),
        api.network: ('floating_ip_simple_associate_supported',
                      'floating_ip_supported',
                      'servers_update_addresses',),
    })
    def _test_instances_index_retrieve_password_action(self):
        servers = self.servers.list()
        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
           .MultipleTimes().AndReturn(self.limits['absolute'])
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()
        url = reverse('horizon:project:instances:index')
        res = self.client.get(url)
        for server in servers:
            _action_id = ''.join(["instances__row_",
                                  server.id,
                                  "__action_decryptpassword"])
            if settings.OPENSTACK_ENABLE_PASSWORD_RETRIEVE and \
                    server.status == "ACTIVE" and \
                    server.key_name is not None:
                self.assertContains(res, _action_id)
            else:
                self.assertNotContains(res, _action_id)

    @helpers.create_stubs({api.nova: ('get_password',)})
    def test_decrypt_instance_password(self):
        server = self.servers.first()
        enc_password = "azerty"
        api.nova.get_password(IsA(http.HttpRequest), server.id)\
            .AndReturn(enc_password)
        self.mox.ReplayAll()
        url = reverse('horizon:project:instances:decryptpassword',
                      args=[server.id,
                            server.key_name])
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'project/instances/decryptpassword.html')

    @helpers.create_stubs({api.nova: ('get_password',)})
    def test_decrypt_instance_get_exception(self):
        server = self.servers.first()
        keypair = self.keypairs.first()
        api.nova.get_password(IsA(http.HttpRequest), server.id)\
            .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()
        url = reverse('horizon:project:instances:decryptpassword',
                      args=[server.id,
                            keypair])
        res = self.client.get(url)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    instance_update_get_stubs = {
        api.nova: ('server_get',),
        api.network: ('security_group_list',
                      'server_security_groups',)}

    @helpers.create_stubs(instance_update_get_stubs)
    def test_instance_update_get(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        api.network.server_security_groups(IsA(http.HttpRequest),
                                           server.id).AndReturn([])

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:update', args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

    @helpers.create_stubs(instance_update_get_stubs)
    def test_instance_update_get_server_get_exception(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:update',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def _instance_update_post(self, server_id, server_name, secgroups):
        default_role_field_name = 'default_' + \
            workflows.update_instance.INSTANCE_SEC_GROUP_SLUG + '_role'
        formData = {'name': server_name,
                    default_role_field_name: 'member',
                    SEC_GROUP_ROLE_PREFIX + 'member': secgroups}
        url = reverse('horizon:project:instances:update',
                      args=[server_id])
        return self.client.post(url, formData)

    instance_update_post_stubs = {
        api.nova: ('server_get', 'server_update'),
        api.network: ('security_group_list',
                      'server_security_groups',
                      'server_update_security_groups')}

    @helpers.create_stubs(instance_update_post_stubs)
    def test_instance_update_post(self):
        server = self.servers.first()
        secgroups = self.security_groups.list()[:3]

        server_groups = [secgroups[0], secgroups[1]]
        wanted_groups = [secgroups[1].id, secgroups[2].id]

        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(secgroups)
        api.network.server_security_groups(IsA(http.HttpRequest),
                                           server.id).AndReturn(server_groups)

        api.nova.server_update(IsA(http.HttpRequest),
                               server.id,
                               server.name).AndReturn(server)
        api.network.server_update_security_groups(IsA(http.HttpRequest),
                                                  server.id,
                                                  wanted_groups)

        self.mox.ReplayAll()

        res = self._instance_update_post(server.id, server.name, wanted_groups)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs(instance_update_post_stubs)
    def test_instance_update_post_api_exception(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        api.network.server_security_groups(IsA(http.HttpRequest),
                                           server.id).AndReturn([])

        api.nova.server_update(IsA(http.HttpRequest), server.id, server.name) \
            .AndRaise(self.exceptions.nova)
        api.network.server_update_security_groups(
            IsA(http.HttpRequest), server.id, [])

        self.mox.ReplayAll()

        res = self._instance_update_post(server.id, server.name, [])
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs(instance_update_post_stubs)
    def test_instance_update_post_secgroup_api_exception(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        api.network.server_security_groups(IsA(http.HttpRequest),
                                           server.id).AndReturn([])

        api.nova.server_update(IsA(http.HttpRequest),
                               server.id,
                               server.name).AndReturn(server)
        api.network.server_update_security_groups(
            IsA(http.HttpRequest),
            server.id, []).AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        res = self._instance_update_post(server.id, server.name, [])
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'server_group_list',
                                      'tenant_absolute_limits',
                                      'availability_zone_list',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_snapshot_list',
                                    'volume_list',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_list'),
                           api.glance: ('image_list_detailed',)})
    def test_launch_instance_get(self,
                                 expect_password_fields=True,
                                 block_device_mapping_v2=True,
                                 custom_flavor_sort=None,
                                 only_one_network=False,
                                 disk_config=True,
                                 config_drive=True,
                                 config_drive_default=False,
                                 test_with_profile=False):
        image = self.images.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(block_device_mapping_v2)
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn([])
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        if only_one_network:
            api.neutron.network_list(IsA(http.HttpRequest),
                                     shared=True).AndReturn([])
        else:
            api.neutron.network_list(IsA(http.HttpRequest),
                                     shared=True) \
                .AndReturn(self.networks.list()[1:])

        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())

        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(disk_config)
        api.nova.extension_supported(
            'ConfigDrive', IsA(http.HttpRequest)).AndReturn(config_drive)
        api.nova.extension_supported(
            'ServerGroups', IsA(http.HttpRequest)).AndReturn(True)
        api.nova.server_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.server_groups.list())
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest))\
            .AndReturn(self.limits['absolute'])
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:launch')
        params = urlencode({"source_type": "image_id",
                            "source_id": image.id})
        res = self.client.get("%s?%s" % (url, params))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(res.context['workflow'].name,
                         workflows.LaunchInstance.name)
        step = workflow.get_step("setinstancedetailsaction")
        self.assertEqual(step.action.initial['image_id'], image.id)
        self.assertQuerysetEqual(
            workflow.steps,
            ['<SetInstanceDetails: setinstancedetailsaction>',
             '<SetAccessControls: setaccesscontrolsaction>',
             '<SetNetwork: setnetworkaction>',
             '<SetNetworkPorts: setnetworkportsaction>',
             '<PostCreationStep: customizeaction>',
             '<SetAdvanced: setadvancedaction>'])

        if custom_flavor_sort == 'id':
            # Reverse sorted by id
            sorted_flavors = (
                ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'm1.metadata'),
                ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'm1.secret'),
                ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'm1.massive'),
                ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'm1.tiny'),
            )
        elif custom_flavor_sort == 'name':
            sorted_flavors = (
                ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'm1.massive'),
                ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'm1.metadata'),
                ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'm1.secret'),
                ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'm1.tiny'),
            )
        elif custom_flavor_sort == helpers.my_custom_sort:
            sorted_flavors = (
                ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'm1.secret'),
                ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'm1.tiny'),
                ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'm1.massive'),
                ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'm1.metadata'),
            )
        else:
            # Default - sorted by RAM
            sorted_flavors = (
                ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'm1.tiny'),
                ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'm1.massive'),
                ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'm1.secret'),
                ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'm1.metadata'),
            )

        select_options = '\n'.join([
            '<option value="%s">%s</option>' % (f[0], f[1])
            for f in sorted_flavors
        ])
        self.assertContains(res, select_options)

        password_field_label = 'Admin Pass'
        if expect_password_fields:
            self.assertContains(res, password_field_label)
        else:
            self.assertNotContains(res, password_field_label)

        boot_from_image_field_label = 'Boot from image (creates a new volume)'
        if block_device_mapping_v2:
            self.assertContains(res, boot_from_image_field_label)
        else:
            self.assertNotContains(res, boot_from_image_field_label)

        checked_box = '<input checked="checked" id="id_network_0"'
        if only_one_network:
            self.assertContains(res, checked_box)
        else:
            self.assertNotContains(res, checked_box)

        disk_config_field_label = 'Disk Partition'
        if disk_config:
            self.assertContains(res, disk_config_field_label)
        else:
            self.assertNotContains(res, disk_config_field_label)

        config_drive_field_label = 'Configuration Drive'
        if config_drive:
            self.assertContains(res, config_drive_field_label)
        else:
            self.assertNotContains(res, config_drive_field_label)

        step = workflow.get_step("setadvancedaction")
        self.assertEqual(step.action.initial['config_drive'],
                         config_drive_default)

    @django.test.utils.override_settings(
        OPENSTACK_HYPERVISOR_FEATURES={'can_set_password': False})
    def test_launch_instance_get_without_password(self):
        self.test_launch_instance_get(expect_password_fields=False)

    @django.test.utils.override_settings(
        OPENSTACK_HYPERVISOR_FEATURES={'requires_keypair': True})
    def test_launch_instance_required_key(self):
        flavor = self.flavors.first()
        image = self.images.first()
        image.min_ram = flavor.ram
        image.min_disk = flavor.disk
        self._test_launch_form_instance_requirement_error(image, flavor,
                                                          keypair_require=True)

    @django.test.utils.override_settings(
        LAUNCH_INSTANCE_DEFAULTS={'config_drive': True})
    def test_launch_instance_get_with_config_drive_default(self):
        self.test_launch_instance_get(config_drive_default=True)

    def test_launch_instance_get_no_block_device_mapping_v2_supported(self):
        self.test_launch_instance_get(block_device_mapping_v2=False)

    def test_launch_instance_get_no_disk_config_supported(self):
        self.test_launch_instance_get(disk_config=False)

    def test_launch_instance_get_no_config_drive_supported(self):
        self.test_launch_instance_get(config_drive=False)

    @django.test.utils.override_settings(
        CREATE_INSTANCE_FLAVOR_SORT={
            'key': 'id',
            'reverse': True,
        })
    def test_launch_instance_get_custom_flavor_sort_by_id(self):
        self.test_launch_instance_get(custom_flavor_sort='id')

    @django.test.utils.override_settings(
        CREATE_INSTANCE_FLAVOR_SORT={
            'key': 'name',
            'reverse': False,
        })
    def test_launch_instance_get_custom_flavor_sort_by_name(self):
        self.test_launch_instance_get(custom_flavor_sort='name')

    @django.test.utils.override_settings(
        CREATE_INSTANCE_FLAVOR_SORT={
            'key': helpers.my_custom_sort,
            'reverse': False,
        })
    def test_launch_instance_get_custom_flavor_sort_by_callable(self):
        self.test_launch_instance_get(
            custom_flavor_sort=helpers.my_custom_sort)

    @django.test.utils.override_settings(
        CREATE_INSTANCE_FLAVOR_SORT={
            'key': 'no_such_column',
            'reverse': False,
        })
    def test_launch_instance_get_custom_flavor_sort_by_missing_column(self):
        self.test_launch_instance_get(custom_flavor_sort='no_such_column')

    def test_launch_instance_get_with_only_one_network(self):
        self.test_launch_instance_get(only_one_network=True)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_instance_get_with_profile(self):
        self.test_launch_instance_get(test_with_profile=True)

    @helpers.create_stubs({api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'server_group_list',
                                      'tenant_absolute_limits',
                                      'availability_zone_list',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_snapshot_list',
                                    'volume_list',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_list'),
                           api.glance: ('image_list_detailed',)})
    def test_launch_instance_get_bootable_volumes(self,
                                                  block_device_mapping_v2=True,
                                                  only_one_network=False,
                                                  disk_config=True,
                                                  config_drive=True,
                                                  test_with_profile=False):
        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(block_device_mapping_v2)
        volumes = [v for v in self.volumes.list()
                   if (v.status == AVAILABLE and v.bootable == 'true')]
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn(volumes)
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        if only_one_network:
            api.neutron.network_list(IsA(http.HttpRequest),
                                     shared=True).AndReturn([])
        else:
            api.neutron.network_list(IsA(http.HttpRequest),
                                     shared=True) \
                .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(disk_config)
        api.nova.extension_supported(
            'ConfigDrive', IsA(http.HttpRequest)).AndReturn(config_drive)
        api.nova.extension_supported(
            'ServerGroups', IsA(http.HttpRequest)).AndReturn(True)
        api.nova.server_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.server_groups.list())
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest))\
            .AndReturn(self.limits['absolute'])
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:launch')
        res = self.client.get(url)

        bootable_volumes = [v.id for v in self.volumes.list()
                            if (v.bootable == 'true' and
                                v.status == 'available')]

        volume_sources = (res.context_data['workflow'].steps[0].
                          action.fields['volume_id'].choices)

        volume_sources_ids = []
        for volume in volume_sources:
            self.assertTrue(volume[0].split(":vol")[0] in bootable_volumes or
                            volume[0] == '')
            if volume[0] != '':
                volume_sources_ids.append(volume[0].split(":vol")[0])

        for volume in bootable_volumes:
            self.assertTrue(volume in volume_sources_ids)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_instance_get_bootable_volumes_with_profile(self):
        self.test_launch_instance_get_bootable_volumes(test_with_profile=True)

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_create',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'availability_zone_list',
                                      'server_group_list',
                                      'server_create',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def test_launch_instance_post(self,
                                  disk_config=True,
                                  config_drive=True,
                                  test_with_profile=False,
                                  test_with_multi_nics=False):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        nics = [{"net-id": self.networks.first().id, "v4-fixed-ip": ''}]
        quota_usages = self.quota_usages.first()
        scheduler_hints = {"group": self.server_groups.first().id}

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            policy_profile_id = self.policy_profiles.first().id
            port_one = self.ports.first()
            nics = [{"port-id": port_one.id}]
            api.neutron.profile_list(
                IsA(http.HttpRequest),
                'policy').AndReturn(policy_profiles)
            api.neutron.port_create(IsA(http.HttpRequest),
                                    self.networks.first().id,
                                    policy_profile_id=policy_profile_id) \
                .AndReturn(port_one)
            if test_with_multi_nics:
                port_two = self.ports.get(name="port5")
                nics = [{"port-id": port_one.id},
                        {"port-id": port_two.id}]
                # Add a second port to test multiple nics
                api.neutron.port_create(IsA(http.HttpRequest),
                                        self.networks.get(name="net4")['id'],
                                        policy_profile_id=policy_profile_id) \
                    .AndReturn(port_two)
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(disk_config)
        api.nova.extension_supported(
            'ConfigDrive', IsA(http.HttpRequest)).AndReturn(config_drive)
        api.nova.extension_supported(
            'ServerGroups', IsA(http.HttpRequest)).AndReturn(True)
        api.nova.server_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.server_groups.list())
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn([])
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])
        if disk_config:
            disk_config_value = u'AUTO'
        else:
            disk_config_value = None
        if config_drive:
            config_drive_value = True
        else:
            config_drive_value = None
        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               image.id,
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [str(sec_group.id)],
                               block_device_mapping=None,
                               block_device_mapping_v2=None,
                               nics=nics,
                               availability_zone=avail_zone.zoneName,
                               instance_count=IsA(int),
                               admin_pass=u'',
                               disk_config=disk_config_value,
                               config_drive=config_drive_value,
                               scheduler_hints=scheduler_hints)
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
            .AndReturn(quota_usages)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'image_id',
                     'image_id': image.id,
                     'keypair': keypair.name,
                     'name': server.name,
                     'script_source': 'raw',
                     'script_data': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': str(sec_group.id),
                     'availability_zone': avail_zone.zoneName,
                     'volume_type': '',
                     'network': self.networks.first().id,
                     'count': 1,
                     'server_group': self.server_groups.first().id}
        if disk_config:
            form_data['disk_config'] = 'AUTO'
        if config_drive:
            form_data['config_drive'] = True
        if test_with_profile:
            form_data['profile'] = self.policy_profiles.first().id
            if test_with_multi_nics:
                form_data['network'] = [self.networks.first().id,
                                        self.networks.get(name="net4")['id']]
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_launch_instance_post_no_disk_config_supported(self):
        self.test_launch_instance_post(disk_config=False)

    def test_launch_instance_post_no_config_drive_supported(self):
        self.test_launch_instance_post(config_drive=False)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_instance_post_with_profile(self):
        self.test_launch_instance_post(test_with_profile=True)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_instance_post_with_profile_and_multi_nics(self):
        self.test_launch_instance_post(test_with_profile=True,
                                       test_with_multi_nics=True)

    def _test_launch_instance_post_with_profile_and_port_error(
        self,
        test_with_multi_nics=False,
    ):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        quota_usages = self.quota_usages.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
                .AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
                .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
                .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        policy_profiles = self.policy_profiles.list()
        policy_profile_id = self.policy_profiles.first().id
        port_one = self.ports.first()
        api.neutron.profile_list(
            IsA(http.HttpRequest),
            'policy').AndReturn(policy_profiles)
        if test_with_multi_nics:
            api.neutron.port_create(IsA(http.HttpRequest),
                                    self.networks.first().id,
                                    policy_profile_id=policy_profile_id) \
               .AndReturn(port_one)
            # Add a second port which has the exception to test multiple nics
            api.neutron.port_create(IsA(http.HttpRequest),
                                    self.networks.get(name="net4")['id'],
                                    policy_profile_id=policy_profile_id) \
               .AndRaise(self.exceptions.neutron)
            # Delete the first port
            api.neutron.port_delete(IsA(http.HttpRequest),
                                    port_one.id)
        else:
            api.neutron.port_create(IsA(http.HttpRequest),
                                    self.networks.first().id,
                                    policy_profile_id=policy_profile_id) \
               .AndRaise(self.exceptions.neutron)
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
                .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(False)
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
              .AndReturn([])
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
              .AndReturn([])
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
              .AndReturn(quota_usages)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'image_id',
                     'image_id': image.id,
                     'keypair': keypair.name,
                     'name': server.name,
                     'script_source': 'raw',
                     'script_data': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': str(sec_group.id),
                     'availability_zone': avail_zone.zoneName,
                     'volume_type': '',
                     'network': self.networks.first().id,
                     'count': 1,
                     'disk_config': 'AUTO',
                     'config_drive': True,
                     'profile': self.policy_profiles.first().id}
        if test_with_multi_nics:
            form_data['network'] = [self.networks.first().id,
                                    self.networks.get(name="net4")['id']]
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_create',
                                         'port_delete',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'availability_zone_list',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def test_launch_instance_post_with_profile_and_port_error(self):
        self._test_launch_instance_post_with_profile_and_port_error()

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_create',
                                         'port_delete',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'availability_zone_list',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def test_lnch_inst_post_w_profile_and_multi_nics_w_port_error(self):
        self._test_launch_instance_post_with_profile_and_port_error(
            test_with_multi_nics=True)

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_create',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'availability_zone_list',
                                      'server_create',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def test_launch_instance_post_boot_from_volume(
        self,
        test_with_profile=False,
        test_with_bdmv2=False
    ):
        flavor = self.flavors.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        device_name = u'vda'
        volume_choice = "%s:vol" % volume.id
        if test_with_bdmv2:
            volume_source_id = volume.id.split(':')[0]
            block_device_mapping = None
            block_device_mapping_2 = [
                {'device_name': u'vda',
                 'source_type': 'volume',
                 'destination_type': 'volume',
                 'delete_on_termination': False,
                 'uuid': volume_source_id,
                 'boot_index': '0',
                 'volume_size': 1
                 }
            ]
        else:
            block_device_mapping = {device_name: u"%s::False" % volume_choice}
            block_device_mapping_2 = None

        nics = [{"net-id": self.networks.first().id, "v4-fixed-ip": ''}]
        quota_usages = self.quota_usages.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(test_with_bdmv2)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            policy_profile_id = self.policy_profiles.first().id
            port = self.ports.first()
            api.neutron.profile_list(
                IsA(http.HttpRequest),
                'policy').AndReturn(policy_profiles)
            api.neutron.port_create(
                IsA(http.HttpRequest),
                self.networks.first().id,
                policy_profile_id=policy_profile_id).AndReturn(port)
            nics = [{"port-id": port.id}]
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(False)
        volumes = [v for v in self.volumes.list()
                   if (v.status == AVAILABLE and v.bootable == 'true')]
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn(volumes)
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])
        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(test_with_bdmv2)

        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               '',
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [str(sec_group.id)],
                               block_device_mapping=block_device_mapping,
                               block_device_mapping_v2=block_device_mapping_2,
                               nics=nics,
                               availability_zone=avail_zone.zoneName,
                               instance_count=IsA(int),
                               admin_pass=u'',
                               disk_config=u'AUTO',
                               config_drive=True,
                               scheduler_hints={})
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
            .AndReturn(quota_usages)

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'volume_id',
                     'source_id': volume_choice,
                     'keypair': keypair.name,
                     'name': server.name,
                     'script_source': 'raw',
                     'script_data': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': str(sec_group.id),
                     'availability_zone': avail_zone.zoneName,
                     'volume_size': '1',
                     'volume_id': volume_choice,
                     'device_name': device_name,
                     'network': self.networks.first().id,
                     'count': 1,
                     'disk_config': 'AUTO',
                     'config_drive': True}
        if test_with_profile:
            form_data['profile'] = self.policy_profiles.first().id
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_launch_instance_post_boot_from_volume_with_bdmv2(self):
        self.test_launch_instance_post_boot_from_volume(test_with_bdmv2=True)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_instance_post_boot_from_volume_with_profile(self):
        self.test_launch_instance_post_boot_from_volume(test_with_profile=True)

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_create',
                                         'port_list'),
                           api.nova: ('server_create',
                                      'extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'availability_zone_list',
                                      'server_group_list',
                                      'tenant_absolute_limits',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def test_launch_instance_post_no_images_available_boot_from_volume(
        self,
        test_with_profile=False,
    ):
        flavor = self.flavors.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        device_name = u'vda'
        volume_choice = "%s:vol" % volume.id
        block_device_mapping = {device_name: u"%s::False" % volume_choice}
        nics = [{"net-id": self.networks.first().id, "v4-fixed-ip": ''}]
        quota_usages = self.quota_usages.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            policy_profile_id = self.policy_profiles.first().id
            port = self.ports.first()
            api.neutron.profile_list(
                IsA(http.HttpRequest),
                'policy').AndReturn(policy_profiles)
            api.neutron.port_create(
                IsA(http.HttpRequest),
                self.networks.first().id,
                policy_profile_id=policy_profile_id).AndReturn(port)
            nics = [{"port-id": port.id}]
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.server_group_list(IsA(http.HttpRequest)).AndReturn([])
        volumes = [v for v in self.volumes.list()
                   if (v.status == AVAILABLE and v.bootable == 'true')]
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn(volumes)
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
            .AndReturn(quota_usages)

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(False)
        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               '',
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [str(sec_group.id)],
                               block_device_mapping=block_device_mapping,
                               block_device_mapping_v2=None,
                               nics=nics,
                               availability_zone=avail_zone.zoneName,
                               instance_count=IsA(int),
                               admin_pass=u'',
                               disk_config='MANUAL',
                               config_drive=True,
                               scheduler_hints={})

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'volume_id',
                     # 'image_id': '',
                     'keypair': keypair.name,
                     'name': server.name,
                     'script_source': 'raw',
                     'script_data': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': str(sec_group.id),
                     'availability_zone': avail_zone.zoneName,
                     'network': self.networks.first().id,
                     'volume_type': 'volume_id',
                     'volume_id': volume_choice,
                     'device_name': device_name,
                     'count': 1,
                     'disk_config': 'MANUAL',
                     'config_drive': True}
        if test_with_profile:
            form_data['profile'] = self.policy_profiles.first().id
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_lnch_inst_post_no_images_avail_boot_from_vol_with_profile(self):
        self.test_launch_instance_post_no_images_available_boot_from_volume(
            test_with_profile=True)

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'availability_zone_list',
                                      'tenant_absolute_limits',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def test_launch_instance_post_no_images_available(self,
                                                      test_with_profile=False):
        flavor = self.flavors.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        quota_usages = self.quota_usages.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
           .AndReturn(self.limits['absolute'])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
            .AndReturn([[], False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(False)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn([])
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
            .AndReturn(quota_usages)

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'image_id',
                     'image_id': '',
                     'keypair': keypair.name,
                     'name': server.name,
                     'script_source': 'raw',
                     'script_data': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': str(sec_group.id),
                     'availability_zone': avail_zone.zoneName,
                     'volume_type': '',
                     'count': 1}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertFormErrors(res, 1, "You must select an image.")
        self.assertTemplateUsed(res, views.WorkflowView.template_name)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_instance_post_no_images_available_with_profile(self):
        self.test_launch_instance_post_no_images_available(
            test_with_profile=True)

    @helpers.create_stubs({
        api.glance: ('image_list_detailed',),
        api.neutron: ('network_list',
                      'profile_list',
                      'port_create',
                      'port_list'),
        api.nova: ('extension_supported',
                   'flavor_list',
                   'keypair_list',
                   'availability_zone_list',
                   'server_group_list',
                   'server_create',),
        api.network: ('security_group_list',),
        cinder: ('volume_list',
                 'volume_snapshot_list',),
        quotas: ('tenant_quota_usages',)})
    def test_launch_instance_post_boot_from_snapshot(
            self,
            test_with_profile=False,
            test_with_bdmv2=False
    ):
        flavor = self.flavors.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        snapshot = self.cinder_volume_snapshots.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        device_name = u'vda'
        snapshot_choice = "%s:snap" % snapshot.id
        if test_with_bdmv2:
            snapshot_source_id = snapshot.id.split(':')[0]
            block_device_mapping = None
            block_device_mapping_2 = [
                {'device_name': u'vda',
                 'source_type': 'snapshot',
                 'destination_type': 'volume',
                 'delete_on_termination': 0,
                 'uuid': snapshot_source_id,
                 'boot_index': '0',
                 'volume_size': 1
                 }
            ]
        else:
            block_device_mapping = {device_name:
                                    u"%s::False" % snapshot_choice}
            block_device_mapping_2 = None

        nics = [{"net-id": self.networks.first().id, "v4-fixed-ip": ''}]
        quota_usages = self.quota_usages.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(test_with_bdmv2)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            policy_profile_id = self.policy_profiles.first().id
            port = self.ports.first()
            api.neutron.profile_list(
                IsA(http.HttpRequest),
                'policy').AndReturn(policy_profiles)
            api.neutron.port_create(
                IsA(http.HttpRequest),
                self.networks.first().id,
                policy_profile_id=policy_profile_id).AndReturn(port)
            nics = [{"port-id": port.id}]
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.server_group_list(IsA(http.HttpRequest)).AndReturn([])
        snapshots = [v for v in self.cinder_volume_snapshots.list()
                     if (v.status == AVAILABLE)]
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn([])
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn(snapshots)
        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(test_with_bdmv2)

        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               '',
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [str(sec_group.id)],
                               block_device_mapping=block_device_mapping,
                               block_device_mapping_v2=block_device_mapping_2,
                               nics=nics,
                               availability_zone=avail_zone.zoneName,
                               instance_count=IsA(int),
                               admin_pass=u'',
                               disk_config=u'AUTO',
                               config_drive=True,
                               scheduler_hints={})
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
              .AndReturn(quota_usages)

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'volume_snapshot_id',
                     'source_id': snapshot_choice,
                     'keypair': keypair.name,
                     'name': server.name,
                     'script_source': 'raw',
                     'script_data': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': str(sec_group.id),
                     'availability_zone': avail_zone.zoneName,
                     'volume_size': '1',
                     'volume_snapshot_id': snapshot_choice,
                     'device_name': device_name,
                     'network': self.networks.first().id,
                     'count': 1,
                     'disk_config': 'AUTO',
                     'config_drive': True}
        if test_with_profile:
            form_data['profile'] = self.policy_profiles.first().id
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_launch_instance_post_boot_from_snapshot_with_bdmv2(self):
        self.test_launch_instance_post_boot_from_snapshot(test_with_bdmv2=True)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_instance_post_boot_from_snapshot_with_profile(self):
        self.test_launch_instance_post_boot_from_snapshot(
            test_with_profile=True)

    @helpers.create_stubs({
        api.glance: ('image_list_detailed',),
        api.neutron: ('network_list',
                      'profile_list',
                      'port_create',
                      'port_list',
                      'is_port_profiles_supported'),
        api.nova: ('extension_supported',
                   'flavor_list',
                   'keypair_list',
                   'availability_zone_list',
                   'server_create',
                   'tenant_absolute_limits'),
        api.network: ('security_group_list',),
        cinder: ('volume_list',
                 'volume_snapshot_list',),
        quotas: ('tenant_quota_usages',)})
    def test_launch_instance_post_boot_from_snapshot_error(
        self,
        test_with_profile=False,
    ):
        flavor = self.flavors.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        avail_zone = self.availability_zones.first()
        quota_usages = self.quota_usages.first()

        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
            .AndReturn([[], False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])

        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
            .AndReturn(quota_usages)

        api.neutron.is_port_profiles_supported()\
            .MultipleTimes().AndReturn(test_with_profile)
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)

        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(self.limits['absolute'])
        self.mox.ReplayAll()

        bad_snapshot_id = 'a-bogus-id'

        form_data = {'flavor': flavor.id,
                     'source_type': 'instance_snapshot_id',
                     'instance_snapshot_id': bad_snapshot_id,
                     'keypair': keypair.name,
                     'name': server.name,
                     'script_source': 'raw',
                     'availability_zone': avail_zone.zoneName,
                     'network': self.networks.first().id,
                     'volume_id': '',
                     'volume_snapshot_id': '',
                     'image_id': '',
                     'device_name': 'vda',
                     'count': 1,
                     'profile': '',
                     'customization_script': ''}

        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertFormErrors(res, 3, "You must select a snapshot.")

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_list'),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           api.network: ('security_group_list',),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'tenant_absolute_limits',
                                      'availability_zone_list',)})
    def test_launch_flavorlist_error(self,
                                     test_with_profile=False):
        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn([])
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(False)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
            .AndReturn(self.limits['absolute'])
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndRaise(self.exceptions.nova)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndRaise(self.exceptions.nova)
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:launch')
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_flavorlist_error_with_profile(self):
        self.test_launch_flavorlist_error(test_with_profile=True)

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_create',
                                         'port_delete',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'availability_zone_list',
                                      'server_group_list',
                                      'server_create',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def test_launch_form_keystone_exception(self,
                                            test_with_profile=False):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        nics = [{"net-id": self.networks.first().id, "v4-fixed-ip": ''}]
        quota_usages = self.quota_usages.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        volumes = [v for v in self.volumes.list()
                   if (v.status == AVAILABLE and v.bootable == 'true')]
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn(volumes)
        volumes = [v for v in self.volumes.list()
                   if (v.status == AVAILABLE)]
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn(volumes)
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.nova.keypair_list(IgnoreArg()).AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            policy_profile_id = self.policy_profiles.first().id
            port = self.ports.first()
            api.neutron.profile_list(
                IsA(http.HttpRequest),
                'policy').AndReturn(policy_profiles)
            api.neutron.port_create(
                IsA(http.HttpRequest),
                self.networks.first().id,
                policy_profile_id=policy_profile_id).AndReturn(port)
            nics = [{"port-id": port.id}]
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(False)
        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               image.id,
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [str(sec_group.id)],
                               block_device_mapping=None,
                               block_device_mapping_v2=None,
                               nics=nics,
                               availability_zone=avail_zone.zoneName,
                               instance_count=IsA(int),
                               admin_pass='password',
                               disk_config='AUTO',
                               config_drive=False,
                               scheduler_hints={}) \
            .AndRaise(self.exceptions.keystone)
        if test_with_profile:
            api.neutron.port_delete(IsA(http.HttpRequest), port.id)
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
            .AndReturn(quota_usages)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'image_id',
                     'source_id': image.id,
                     'volume_size': '1',
                     'image_id': image.id,
                     'availability_zone': avail_zone.zoneName,
                     'keypair': keypair.name,
                     'name': server.name,
                     'script_source': 'raw',
                     'script_data': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': str(sec_group.id),
                     'volume_type': '',
                     'network': self.networks.first().id,
                     'count': 1,
                     'admin_pass': 'password',
                     'confirm_admin_pass': 'password',
                     'disk_config': 'AUTO',
                     'config_drive': False}
        if test_with_profile:
            form_data['profile'] = self.policy_profiles.first().id
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_form_keystone_exception_with_profile(self):
        self.test_launch_form_keystone_exception(test_with_profile=True)

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'tenant_absolute_limits',
                                      'availability_zone_list',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def test_launch_form_instance_count_error(self,
                                              test_with_profile=False):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        device_name = u'vda'
        volume_choice = "%s:vol" % volume.id
        quota_usages = self.quota_usages.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])

        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(False)
        volumes = [v for v in self.volumes.list()
                   if (v.status == AVAILABLE and v.bootable == 'true')]
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn(volumes)
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])

        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
           .AndReturn(self.limits['absolute'])
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
            .AndReturn(quota_usages)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'image_id',
                     'image_id': image.id,
                     'availability_zone': avail_zone.zoneName,
                     'keypair': keypair.name,
                     'name': server.name,
                     'script_source': 'raw',
                     'script_data': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': str(sec_group.id),
                     'volume_type': 'volume_id',
                     'volume_id': volume_choice,
                     'device_name': device_name,
                     'count': 0}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertContains(res, "greater than or equal to 1")

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'server_group_list',
                                      'tenant_absolute_limits',
                                      'availability_zone_list',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def _test_launch_form_count_error(self, resource,
                                      avail, test_with_profile=False):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        device_name = u'vda'
        volume_choice = "%s:vol" % volume.id
        quota_usages = self.quota_usages.first()
        if resource == 'both':
            quota_usages['cores']['available'] = avail
            quota_usages['ram']['available'] = 512
        else:
            quota_usages[resource]['available'] = avail

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.server_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.server_groups.list())
        volumes = [v for v in self.volumes.list()
                   if (v.status == AVAILABLE and v.bootable == 'true')]
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn(volumes)
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])

        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
           .AndReturn(self.limits['absolute'])
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
            .AndReturn(quota_usages)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'image_id',
                     'image_id': image.id,
                     'availability_zone': avail_zone.zoneName,
                     'keypair': keypair.name,
                     'name': server.name,
                     'script_source': 'raw',
                     'script_data': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': str(sec_group.id),
                     'volume_type': 'volume_id',
                     'volume_id': volume_choice,
                     'device_name': device_name,
                     'count': 2}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        if resource == 'ram':
            msg = ("The following requested resource(s) exceed quota(s): "
                   "RAM(Available: %s" % avail)
        if resource == 'cores':
            msg = ("The following requested resource(s) exceed quota(s): "
                   "Cores(Available: %s" % avail)
        if resource == 'both':
            msg = ("The following requested resource(s) exceed quota(s): "
                   "Cores(Available: %(avail)s, Requested: 2), RAM(Available: "
                   "512, Requested: 1024)" % {'avail': avail})
        self.assertContains(res, msg)

    def test_launch_form_cores_count_error(self):
        self._test_launch_form_count_error('cores', 1, test_with_profile=False)

    def test_launch_form_ram_count_error(self):
        self._test_launch_form_count_error('ram', 512, test_with_profile=False)

    def test_launch_form_ram_cores_count_error(self):
        self._test_launch_form_count_error('both', 1, test_with_profile=False)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_form_instance_count_error_with_profile(self):
        self.test_launch_form_instance_count_error(test_with_profile=True)

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'tenant_absolute_limits',
                                      'availability_zone_list',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def _test_launch_form_instance_requirement_error(self, image, flavor,
                                                     test_with_profile=False,
                                                     keypair_require=False):
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        device_name = u'vda'
        volume_choice = "%s:vol" % volume.id
        quota_usages = self.quota_usages.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(False)
        volumes = [v for v in self.volumes.list()
                   if (v.status == AVAILABLE and v.bootable == 'true')]
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn(volumes)
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])

        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
           .AndReturn(self.limits['absolute'])
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
            .AndReturn(quota_usages)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'image_id',
                     'image_id': image.id,
                     'availability_zone': avail_zone.zoneName,
                     'name': server.name,
                     'script_source': 'raw',
                     'script_data': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': str(sec_group.id),
                     'volume_type': 'volume_id',
                     'volume_id': volume_choice,
                     'device_name': device_name,
                     'count': 1}
        if not keypair_require:
            form_data['keypair'] = keypair.name

        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)
        if keypair_require:
            msg = "This field is required"
            self.assertContains(res, msg)
        else:
            msg = "The flavor &#39;%s&#39; is too small" % flavor.name
            self.assertContains(res, msg)

    def test_launch_form_instance_requirement_error_disk(
        self,
        test_with_profile=False,
    ):
        flavor = self.flavors.first()
        image = self.images.first()
        image.min_ram = flavor.ram
        image.min_disk = flavor.disk + 1
        self._test_launch_form_instance_requirement_error(image, flavor,
                                                          test_with_profile)

    def test_launch_form_instance_requirement_error_ram(
        self,
        test_with_profile=False,
    ):
        flavor = self.flavors.first()
        image = self.images.first()
        image.min_ram = flavor.ram + 1
        image.min_disk = flavor.disk
        self._test_launch_form_instance_requirement_error(image, flavor,
                                                          test_with_profile)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_form_instance_requirement_error_disk_with_profile(self):
        self.test_launch_form_instance_requirement_error_disk(
            test_with_profile=True)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_form_instance_requirement_error_ram_with_profile(self):
        self.test_launch_form_instance_requirement_error_ram(
            test_with_profile=True)

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'tenant_absolute_limits',
                                      'availability_zone_list',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def _test_launch_form_instance_show_device_name(self, device_name,
                                                    widget_class,
                                                    widget_attrs):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        volume_choice = "%s:vol" % volume.id
        quota_usages = self.quota_usages.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.flavor_list(
            IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.nova.keypair_list(
            IsA(http.HttpRequest)).AndReturn(self.keypairs.list())
        api.network.security_group_list(
            IsA(http.HttpRequest)).AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(
            IsA(http.HttpRequest)).AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True,
                     'status': 'active'}).AndReturn(
            [self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}).AndReturn([[], False, False])
        api.neutron.network_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            shared=False).AndReturn(self.networks.list()[:1])
        api.neutron.network_list(
            IsA(http.HttpRequest),
            shared=True).AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        api.nova.extension_supported(
            'DiskConfig', IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported(
            'ConfigDrive', IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported(
            'ServerGroups', IsA(http.HttpRequest)).AndReturn(False)
        volumes = [v for v in self.volumes.list()
                   if (v.status == AVAILABLE and v.bootable == 'true')]
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn(volumes)
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])
        api.nova.flavor_list(
            IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.nova.tenant_absolute_limits(
            IsA(http.HttpRequest)).AndReturn(self.limits['absolute'])
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)).AndReturn(quota_usages)
        api.nova.flavor_list(
            IsA(http.HttpRequest)).AndReturn(self.flavors.list())

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'volume_image_id',
                     'image_id': image.id,
                     'availability_zone': avail_zone.zoneName,
                     'keypair': keypair.name,
                     'name': server.name,
                     'customization_script': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': str(sec_group.id),
                     'volume_type': 'volume_id',
                     'volume_id': volume_choice,
                     'volume_size': max(
                         image.min_disk, image.size // 1024 ** 3),
                     'device_name': device_name,
                     'count': 1}

        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        widget_content = widget_class().render(**widget_attrs)
        # In django 1.4, the widget's html attributes are not always rendered
        # in the same order and checking the fully rendered widget fails.
        for widget_part in widget_content.split():
            self.assertContains(res, widget_part)

    @django.test.utils.override_settings(
        OPENSTACK_HYPERVISOR_FEATURES={'can_set_mount_point': True})
    def test_launch_form_instance_device_name_showed(self):
        self._test_launch_form_instance_show_device_name(
            u'vda', widgets.TextInput, {
                'name': 'device_name', 'value': 'vda',
                'attrs': {'id': 'id_device_name'}}
        )

    @django.test.utils.override_settings(
        OPENSTACK_HYPERVISOR_FEATURES={'can_set_mount_point': False})
    def test_launch_form_instance_device_name_hidden(self):
        self._test_launch_form_instance_show_device_name(
            u'', widgets.HiddenInput, {
                'name': 'device_name', 'value': '',
                'attrs': {'id': 'id_device_name'}}
        )

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'server_group_list',
                                      'tenant_absolute_limits',
                                      'availability_zone_list',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def _test_launch_form_instance_volume_size(self, image, volume_size, msg,
                                               test_with_profile=False,
                                               volumes=None):
        flavor = self.flavors.get(name='m1.massive')
        keypair = self.keypairs.first()
        server = self.servers.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        device_name = u'vda'
        quota_usages = self.quota_usages.first()
        quota_usages['cores']['available'] = 2000
        if volumes is not None:
            quota_usages['volumes']['available'] = volumes
        else:
            api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.server_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.server_groups.list())
        volumes = [v for v in self.volumes.list()
                   if (v.status == AVAILABLE and v.bootable == 'true')]
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn(volumes)
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])

        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
            .AndReturn(self.limits['absolute'])
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
            .AndReturn(quota_usages)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())

        self.mox.ReplayAll()

        form_data = {
            'flavor': flavor.id,
            'source_type': 'volume_image_id',
            'image_id': image.id,
            'availability_zone': avail_zone.zoneName,
            'keypair': keypair.name,
            'name': server.name,
            'script_source': 'raw',
            'script_data': customization_script,
            'project_id': self.tenants.first().id,
            'user_id': self.user.id,
            'groups': str(sec_group.id),
            'volume_size': volume_size,
            'device_name': device_name,
            'count': 1
        }
        url = reverse('horizon:project:instances:launch')

        res = self.client.post(url, form_data)
        self.assertContains(res, msg)

    def test_launch_form_instance_volume_size_error(self,
                                                    test_with_profile=False):
        image = self.images.get(name='protected_images')
        volume_size = image.min_disk // 2
        msg = ("The Volume size is too small for the &#39;%s&#39; image" %
               image.name)
        self._test_launch_form_instance_volume_size(image, volume_size, msg,
                                                    test_with_profile)

    def test_launch_form_instance_non_int_volume_size(self,
                                                      test_with_profile=False):
        image = self.images.get(name='protected_images')
        msg = "Enter a whole number."
        self._test_launch_form_instance_volume_size(image, 1.5, msg,
                                                    test_with_profile)

    def test_launch_form_instance_volume_exceed_quota(self):
        image = self.images.get(name='protected_images')
        msg = "Requested volume exceeds quota: Available: 0, Requested: 1"
        self._test_launch_form_instance_volume_size(image, image.min_disk,
                                                    msg, False, 0)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_form_instance_volume_size_error_with_profile(self):
        self.test_launch_form_instance_volume_size_error(
            test_with_profile=True)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_launch_form_instance_non_int_volume_size_with_profile(self):
        self.test_launch_form_instance_non_int_volume_size(
            test_with_profile=True)

    @helpers.create_stubs({
        api.nova: ('flavor_list', 'server_list', 'tenant_absolute_limits',
                   'extension_supported',),
        api.glance: ('image_list_detailed',),
        api.network: ('floating_ip_simple_associate_supported',
                      'floating_ip_supported',
                      'servers_update_addresses',),
    })
    def test_launch_button_attributes(self):
        servers = self.servers.list()
        limits = self.limits['absolute']
        limits['totalInstancesUsed'] = 0

        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
            .MultipleTimes().AndReturn(limits)
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        tables.LaunchLink()
        res = self.client.get(INDEX_URL)

        launch_action = self.getAndAssertTableAction(res, 'instances',
                                                     'launch-ng')

        self.assertEqual(set(['btn-launch']),
                         set(launch_action.classes))
        self.assertEqual('Launch Instance', launch_action.verbose_name)
        self.assertEqual((('compute', 'compute:create'),),
                         launch_action.policy_rules)

    @helpers.create_stubs({
        api.nova: ('flavor_list', 'server_list', 'tenant_absolute_limits',
                   'extension_supported',),
        api.glance: ('image_list_detailed',),
        api.network: ('floating_ip_simple_associate_supported',
                      'floating_ip_supported',
                      'servers_update_addresses',),
    })
    def test_launch_button_disabled_when_quota_exceeded(self):
        servers = self.servers.list()
        limits = self.limits['absolute']
        limits['totalInstancesUsed'] = limits['maxTotalInstances']

        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
            .MultipleTimes().AndReturn(limits)
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        tables.LaunchLink()
        res = self.client.get(INDEX_URL)

        launch_action = self.getAndAssertTableAction(
            res, 'instances', 'launch-ng')

        self.assertTrue('disabled' in launch_action.classes,
                        'The launch button should be disabled')
        self.assertEqual('Launch Instance (Quota exceeded)',
                         six.text_type(launch_action.verbose_name))

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'availability_zone_list',
                                      'server_group_list',
                                      'tenant_absolute_limits',
                                      'server_create',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def test_launch_with_empty_device_name_allowed(self):
        flavor = self.flavors.get(name='m1.massive')
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        nics = [{'net-id': self.networks.first().id, 'v4-fixed-ip': ''}]
        device_name = u''
        quota_usages = self.quota_usages.first()
        quota_usages['cores']['available'] = 2000
        device_mapping_v2 = [{'device_name': None,  # device_name must be None
                              'source_type': 'image',
                              'destination_type': 'volume',
                              'delete_on_termination': False,
                              'uuid': image.id,
                              'boot_index': '0',
                              'volume_size': image.size}]

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.server_group_list(IsA(http.HttpRequest)).AndReturn([])
        volumes = [v for v in self.volumes.list()
                   if (v.status == AVAILABLE and v.bootable == 'true')]
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn(volumes)
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])

        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
            .AndReturn(quota_usages)

        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               '',
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [str(sec_group.id)],
                               block_device_mapping=None,
                               block_device_mapping_v2=device_mapping_v2,
                               nics=nics,
                               availability_zone=avail_zone.zoneName,
                               instance_count=IsA(int),
                               admin_pass=u'',
                               config_drive=False,
                               disk_config=u'',
                               scheduler_hints={})

        self.mox.ReplayAll()

        form_data = {
            'flavor': flavor.id,
            'source_type': 'volume_image_id',
            'image_id': image.id,
            'availability_zone': avail_zone.zoneName,
            'keypair': keypair.name,
            'name': server.name,
            'script_source': 'raw',
            'script_data': customization_script,
            'project_id': self.tenants.first().id,
            'user_id': self.user.id,
            'groups': str(sec_group.id),
            'volume_size': image.size,
            'device_name': device_name,
            'network': self.networks.first().id,
            'count': 1
        }
        url = reverse('horizon:project:instances:launch')

        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)

    @helpers.create_stubs({
        api.nova: ('flavor_list', 'server_list', 'tenant_absolute_limits',
                   'extension_supported',),
        api.glance: ('image_list_detailed',),
        api.network: ('floating_ip_simple_associate_supported',
                      'floating_ip_supported',
                      'servers_update_addresses',),
    })
    def test_index_options_after_migrate(self):
        servers = self.servers.list()
        server = self.servers.first()
        server.status = "VERIFY_RESIZE"
        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
           .MultipleTimes().AndReturn(self.limits['absolute'])
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertContains(res, "instances__confirm")
        self.assertContains(res, "instances__revert")

    @helpers.create_stubs({api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'availability_zone_list',
                                      'tenant_absolute_limits',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_snapshot_list',
                                    'volume_list',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_list'),
                           api.glance: ('image_list_detailed',)})
    def test_select_default_keypair_if_only_one(self,
                                                test_with_profile=False):
        keypair = self.keypairs.first()

        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn([])
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn([])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        if test_with_profile:
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
           .AndReturn(self.limits['absolute'])
        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(False)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
            .AndReturn([keypair])
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:launch')
        res = self.client.get(url)
        self.assertContains(
            res, "<option selected='selected' value='%(key)s'>"
                 "%(key)s</option>" % {'key': keypair.name},
            html=True,
            msg_prefix="The default key pair was not selected.")

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    def test_select_default_keypair_if_only_one_with_profile(self):
        self.test_select_default_keypair_if_only_one(test_with_profile=True)

    @helpers.create_stubs({api.network: ('floating_ip_target_get_by_instance',
                                         'tenant_floating_ip_allocate',
                                         'floating_ip_associate',
                                         'servers_update_addresses',),
                           api.glance: ('image_list_detailed',),
                           api.nova: ('server_list',
                                      'flavor_list')})
    def test_associate_floating_ip(self):
        servers = self.servers.list()
        server = servers[0]
        fip = self.q_floating_ips.first()

        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        api.network.floating_ip_target_get_by_instance(
            IsA(http.HttpRequest),
            server.id).AndReturn(server.id)
        api.network.tenant_floating_ip_allocate(
            IsA(http.HttpRequest)).AndReturn(fip)
        api.network.floating_ip_associate(
            IsA(http.HttpRequest), fip.id, server.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__associate-simple__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.network: ('floating_ip_target_list_by_instance',
                                         'tenant_floating_ip_list',
                                         'floating_ip_disassociate',
                                         'servers_update_addresses',),
                           api.glance: ('image_list_detailed',),
                           api.nova: ('server_list',
                                      'flavor_list')})
    def test_disassociate_floating_ip(self):
        servers = self.servers.list()
        server = servers[0]
        fip = self.q_floating_ips.first()
        fip.port_id = server.id

        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        api.network.floating_ip_target_list_by_instance(
            IsA(http.HttpRequest),
            server.id).AndReturn([server.id, ])
        api.network.tenant_floating_ip_list(
            IsA(http.HttpRequest)).AndReturn([fip])
        api.network.floating_ip_disassociate(
            IsA(http.HttpRequest), fip.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__disassociate__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_get',
                                      'flavor_list',
                                      'tenant_absolute_limits',
                                      'extension_supported')})
    def test_instance_resize_get(self):
        server = self.servers.first()
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
           .AndReturn(self.limits['absolute'])
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(False)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:resize', args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        config_drive_field_label = 'Configuration Drive'
        self.assertNotContains(res, config_drive_field_label)

        option = '<option value="%s">%s</option>'
        for flavor in self.flavors.list():
            if flavor.id == server.flavor['id']:
                self.assertNotContains(res, option % (flavor.id, flavor.name))
            else:
                self.assertContains(res, option % (flavor.id, flavor.name))

    @helpers.create_stubs({api.nova: ('server_get',
                                      'flavor_list',)})
    def test_instance_resize_get_server_get_exception(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:resize',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_get',
                                      'flavor_list',)})
    def test_instance_resize_get_flavor_list_exception(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:resize',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.nova: ('server_get',
                                      'flavor_list',
                                      'flavor_get',
                                      'tenant_absolute_limits',
                                      'extension_supported')})
    def test_instance_resize_get_current_flavor_not_found(self):
        server = self.servers.first()
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        api.nova.flavor_get(IsA(http.HttpRequest), server.flavor['id']) \
            .AndRaise(self.exceptions.nova)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
           .AndReturn(self.limits['absolute'])
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(False)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:resize', args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

    def _instance_resize_post(self, server_id, flavor_id, disk_config):
        formData = {'flavor': flavor_id,
                    'default_role': 'member',
                    'disk_config': disk_config}
        url = reverse('horizon:project:instances:resize',
                      args=[server_id])
        return self.client.post(url, formData)

    instance_resize_post_stubs = {
        api.nova: ('server_get', 'server_resize',
                   'flavor_list', 'flavor_get',
                   'extension_supported')}

    @helpers.create_stubs(instance_resize_post_stubs)
    def test_instance_resize_post(self):
        server = self.servers.first()
        flavors = [flavor for flavor in self.flavors.list()
                   if flavor.id != server.flavor['id']]
        flavor = flavors[0]

        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(False)
        api.nova.server_resize(IsA(http.HttpRequest), server.id, flavor.id,
                               'AUTO').AndReturn([])

        self.mox.ReplayAll()

        res = self._instance_resize_post(server.id, flavor.id, u'AUTO')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs(instance_resize_post_stubs)
    def test_instance_resize_post_api_exception(self):
        server = self.servers.first()
        flavors = [flavor for flavor in self.flavors.list()
                   if flavor.id != server.flavor['id']]
        flavor = flavors[0]

        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(False)
        api.nova.server_resize(IsA(http.HttpRequest), server.id, flavor.id,
                               'AUTO') \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        res = self._instance_resize_post(server.id, flavor.id, 'AUTO')
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.nova: ('extension_supported',)})
    def test_rebuild_instance_get(self, expect_password_fields=True):
        server = self.servers.first()
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:rebuild', args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/instances/rebuild.html')

        password_field_label = 'Rebuild Password'
        if expect_password_fields:
            self.assertContains(res, password_field_label)
        else:
            self.assertNotContains(res, password_field_label)

    @django.test.utils.override_settings(
        OPENSTACK_HYPERVISOR_FEATURES={'can_set_password': False})
    def test_rebuild_instance_get_without_set_password(self):
        self.test_rebuild_instance_get(expect_password_fields=False)

    def _instance_rebuild_post(self, server_id, image_id,
                               password=None, confirm_password=None,
                               disk_config=None):
        form_data = {'instance_id': server_id,
                     'image': image_id,
                     'disk_config': disk_config}
        if password is not None:
            form_data.update(password=password)
        if confirm_password is not None:
            form_data.update(confirm_password=confirm_password)
        url = reverse('horizon:project:instances:rebuild',
                      args=[server_id])
        return self.client.post(url, form_data)

    instance_rebuild_post_stubs = {
        api.nova: ('server_rebuild',
                   'extension_supported'),
        api.glance: ('image_list_detailed',)}

    @helpers.create_stubs(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_with_password(self):
        server = self.servers.first()
        image = self.images.first()
        password = u'testpass'

        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.server_rebuild(IsA(http.HttpRequest),
                                server.id,
                                image.id,
                                password,
                                'AUTO').AndReturn([])

        self.mox.ReplayAll()

        res = self._instance_rebuild_post(server.id, image.id,
                                          password=password,
                                          confirm_password=password,
                                          disk_config='AUTO')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_with_password_equals_none(self):
        server = self.servers.first()
        image = self.images.first()

        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.server_rebuild(IsA(http.HttpRequest),
                                server.id,
                                image.id,
                                None,
                                'AUTO') \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        res = self._instance_rebuild_post(server.id, image.id,
                                          password=None,
                                          confirm_password=None,
                                          disk_config='AUTO')
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_password_do_not_match(self):
        server = self.servers.first()
        image = self.images.first()
        pass1 = u'somepass'
        pass2 = u'notsomepass'

        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)

        self.mox.ReplayAll()
        res = self._instance_rebuild_post(server.id, image.id,
                                          password=pass1,
                                          confirm_password=pass2,
                                          disk_config='MANUAL')

        self.assertEqual(res.context['form'].errors['__all__'],
                         ["Passwords do not match."])

    @helpers.create_stubs(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_with_empty_string(self):
        server = self.servers.first()
        image = self.images.first()

        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.server_rebuild(IsA(http.HttpRequest),
                                server.id,
                                image.id,
                                None,
                                'AUTO').AndReturn([])

        self.mox.ReplayAll()

        res = self._instance_rebuild_post(server.id, image.id,
                                          password=u'',
                                          confirm_password=u'',
                                          disk_config=u'AUTO')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_api_exception(self):
        server = self.servers.first()
        image = self.images.first()
        password = u'testpass'

        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.server_rebuild(IsA(http.HttpRequest),
                                server.id,
                                image.id,
                                password,
                                'AUTO') \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        res = self._instance_rebuild_post(server.id, image.id,
                                          password=password,
                                          confirm_password=password,
                                          disk_config='AUTO')
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @django.test.utils.override_settings(API_RESULT_PAGE_SIZE=2)
    @helpers.create_stubs({
        api.nova: ('flavor_list', 'server_list', 'tenant_absolute_limits',
                   'extension_supported',),
        api.glance: ('image_list_detailed',),
        api.network: ('floating_ip_simple_associate_supported',
                      'floating_ip_supported',
                      'servers_update_addresses',),
    })
    def test_index_form_action_with_pagination(self):
        """The form action on the next page should have marker
           object from the previous page last element.
        """
        page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 2)
        servers = self.servers.list()[:3]

        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .MultipleTimes().AndReturn((self.images.list(), False, False))

        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers[:page_size], True])
        api.network.servers_update_addresses(
            IsA(http.HttpRequest), servers[:page_size])
        api.nova.server_list(IsA(http.HttpRequest), search_opts={
            'marker': servers[page_size - 1].id, 'paginate': True}) \
            .AndReturn([servers[page_size:], False])
        api.network.servers_update_addresses(
            IsA(http.HttpRequest), servers[page_size:])

        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
           .MultipleTimes().AndReturn(self.limits['absolute'])
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/instances/index.html')
        # get first page with 2 items
        self.assertEqual(len(res.context['instances_table'].data), page_size)

        # update INDEX_URL with marker object
        params = "=".join([tables.InstancesTable._meta.pagination_param,
                           servers[page_size - 1].id])
        next_page_url = "?".join([reverse('horizon:project:instances:index'),
                                  params])
        form_action = 'action="%s"' % next_page_url

        res = self.client.get(next_page_url)
        # get next page with remaining items (item 3)
        self.assertEqual(len(res.context['instances_table'].data), 1)
        # ensure that marker object exists in form action
        self.assertContains(res, form_action, count=1)

    @django.test.utils.override_settings(API_RESULT_PAGE_SIZE=2)
    @helpers.create_stubs({api.nova: ('server_list',
                                      'flavor_list',
                                      'server_delete',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',)})
    def test_delete_instance_with_pagination(self):
        """Instance should be deleted from
           the next page.
        """
        page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 2)
        servers = self.servers.list()[:3]
        server = servers[-1]

        search_opts = {'marker': servers[page_size - 1].id, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers[page_size:], False])
        api.network.servers_update_addresses(IsA(http.HttpRequest),
                                             servers[page_size:])
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False, False))
        api.nova.server_delete(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        # update INDEX_URL with marker object
        params = "=".join([tables.InstancesTable._meta.pagination_param,
                           servers[page_size - 1].id])
        next_page_url = "?".join([reverse('horizon:project:instances:index'),
                                  params])
        formData = {'action': 'instances__delete__%s' % server.id}
        res = self.client.post(next_page_url, formData)

        self.assertRedirectsNoFollow(res, next_page_url)
        self.assertMessageCount(success=1)

    class SimpleFile(object):
        def __init__(self, name, data, size):
            self.name = name
            self.data = data
            self._size = size

        def read(self):
            return self.data

    def test_clean_file_upload_form_oversize_data(self):
        t = workflows.create_instance.CustomizeAction(self.request, {})
        upload_str = 'user data'
        files = {'script_upload':
                 self.SimpleFile('script_name',
                                 upload_str,
                                 (16 * 1024) + 1)}

        self.assertRaises(
            forms.ValidationError,
            t.clean_uploaded_files,
            'script',
            files)

    def test_clean_file_upload_form_invalid_data(self):
        t = workflows.create_instance.CustomizeAction(self.request, {})
        upload_str = b'\x81'
        files = {'script_upload':
                 self.SimpleFile('script_name',
                                 upload_str,
                                 sys.getsizeof(upload_str))}

        self.assertRaises(
            forms.ValidationError,
            t.clean_uploaded_files,
            'script',
            files)

    def test_clean_file_upload_form_valid_data(self):
        t = workflows.create_instance.CustomizeAction(self.request, {})
        precleaned = 'user data'
        upload_str = 'user data'
        files = {'script_upload':
                 self.SimpleFile('script_name',
                                 upload_str,
                                 sys.getsizeof(upload_str))}

        cleaned = t.clean_uploaded_files('script', files)

        self.assertEqual(
            cleaned,
            precleaned)


class InstanceAjaxTests(helpers.TestCase):
    @helpers.create_stubs({api.nova: ("server_get",
                                      "flavor_get",
                                      "extension_supported"),
                           api.network: ('servers_update_addresses',),
                           api.neutron: ("is_extension_supported",)})
    def test_row_update(self):
        server = self.servers.first()
        instance_id = server.id
        flavor_id = server.flavor["id"]
        flavors = self.flavors.list()
        full_flavors = OrderedDict([(f.id, f) for f in flavors])

        api.nova.extension_supported('AdminActions', IsA(http.HttpRequest))\
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'security-group')\
            .MultipleTimes().AndReturn(True)
        api.nova.server_get(IsA(http.HttpRequest), instance_id)\
            .AndReturn(server)
        api.nova.flavor_get(IsA(http.HttpRequest), flavor_id)\
            .AndReturn(full_flavors[flavor_id])

        self.mox.ReplayAll()

        params = {'action': 'row_update',
                  'table': 'instances',
                  'obj_id': instance_id,
                  }
        res = self.client.get('?'.join((INDEX_URL, urlencode(params))),
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(res, server.name)

    @helpers.create_stubs({api.nova: ("server_get",
                                      "flavor_get",
                                      "extension_supported"),
                           api.neutron: ("is_extension_supported",),
                           api.network: ('servers_update_addresses',)})
    def test_row_update_instance_error(self):
        server = self.servers.first()
        instance_id = server.id
        flavor_id = server.flavor["id"]
        flavors = self.flavors.list()
        full_flavors = OrderedDict([(f.id, f) for f in flavors])

        server.status = 'ERROR'
        server.fault = {"message": "NoValidHost",
                        "code": 500,
                        "details": "No valid host was found. \n  "
                                   "File \"/mnt/stack/nova/nova/"
                                   "scheduler/filter_scheduler.py\", "
                                   "line 105, in schedule_run_instance\n    "
                                   "raise exception.NoValidHost"
                                   "(reason=\"\")\n",
                        "created": "2013-10-07T00:08:32Z"}

        api.nova.extension_supported('AdminActions', IsA(http.HttpRequest))\
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'security-group')\
            .MultipleTimes().AndReturn(True)
        api.nova.server_get(IsA(http.HttpRequest), instance_id)\
            .AndReturn(server)
        api.nova.flavor_get(IsA(http.HttpRequest), flavor_id)\
            .AndReturn(full_flavors[flavor_id])

        self.mox.ReplayAll()

        params = {'action': 'row_update',
                  'table': 'instances',
                  'obj_id': instance_id,
                  }
        res = self.client.get('?'.join((INDEX_URL, urlencode(params))),
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(res, server.name)
        self.assertTrue(res.has_header('X-Horizon-Messages'))
        messages = json.loads(res['X-Horizon-Messages'])
        self.assertEqual(len(messages), 1)
        # (Pdb) messages
        # [[u'error', u'Failed to launch instance "server_1": \
        # There is not enough capacity for this flavor in the \
        # selected availability zone. Try again later or select \
        # a different availability zone.', u'']]
        self.assertEqual(messages[0][0], 'error')
        self.assertTrue(messages[0][1].startswith('Failed'))

    @helpers.create_stubs({api.nova: ("server_get",
                                      "flavor_get",
                                      "extension_supported"),
                           api.neutron: ("is_extension_supported",
                                         "servers_update_addresses",)})
    def test_row_update_flavor_not_found(self):
        server = self.servers.first()
        instance_id = server.id

        api.nova.extension_supported('AdminActions', IsA(http.HttpRequest))\
            .MultipleTimes().AndReturn(True)
        api.nova.extension_supported('Shelve', IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'security-group')\
            .MultipleTimes().AndReturn(True)
        api.nova.server_get(IsA(http.HttpRequest), instance_id)\
            .AndReturn(server)
        api.nova.flavor_get(IsA(http.HttpRequest), server.flavor["id"])\
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        params = {'action': 'row_update',
                  'table': 'instances',
                  'obj_id': instance_id,
                  }
        res = self.client.get('?'.join((INDEX_URL, urlencode(params))),
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(res, server.name)
        self.assertContains(res, "Not available")


class ConsoleManagerTests(helpers.TestCase):

    def setup_consoles(self):
        # Need to refresh with mocks or will fail since mox do not detect
        # the api_call() as mocked.
        console.CONSOLES = OrderedDict([
            ('VNC', api.nova.server_vnc_console),
            ('SPICE', api.nova.server_spice_console),
            ('RDP', api.nova.server_rdp_console),
            ('SERIAL', api.nova.server_serial_console)])

    def _get_console_vnc(self, server):
        console_mock = self.mox.CreateMock(api.nova.VNCConsole)
        console_mock.url = '/VNC'

        self.mox.StubOutWithMock(api.nova, 'server_vnc_console')
        api.nova.server_vnc_console(IgnoreArg(), server.id) \
            .AndReturn(console_mock)

        self.mox.ReplayAll()
        self.setup_consoles()

    def test_get_console_vnc(self):
        server = self.servers.first()
        self._get_console_vnc(server)
        url = '/VNC&title=%s(%s)' % (server.name, server.id)
        data = console.get_console(self.request, 'VNC', server)[1]
        self.assertEqual(data, url)

    def _get_console_spice(self, server):
        console_mock = self.mox.CreateMock(api.nova.SPICEConsole)
        console_mock.url = '/SPICE'

        self.mox.StubOutWithMock(api.nova, 'server_spice_console')
        api.nova.server_spice_console(IgnoreArg(), server.id) \
            .AndReturn(console_mock)

        self.mox.ReplayAll()
        self.setup_consoles()

    def test_get_console_spice(self):
        server = self.servers.first()
        self._get_console_spice(server)
        url = '/SPICE&title=%s(%s)' % (server.name, server.id)
        data = console.get_console(self.request, 'SPICE', server)[1]
        self.assertEqual(data, url)

    def _get_console_rdp(self, server):
        console_mock = self.mox.CreateMock(api.nova.RDPConsole)
        console_mock.url = '/RDP'

        self.mox.StubOutWithMock(api.nova, 'server_rdp_console')
        api.nova.server_rdp_console(IgnoreArg(), server.id) \
            .AndReturn(console_mock)

        self.mox.ReplayAll()
        self.setup_consoles()

    def test_get_console_rdp(self):
        server = self.servers.first()
        self._get_console_rdp(server)
        url = '/RDP&title=%s(%s)' % (server.name, server.id)
        data = console.get_console(self.request, 'RDP', server)[1]
        self.assertEqual(data, url)

    def _get_console_serial(self, server):
        console_mock = self.mox.CreateMock(api.nova.SerialConsole)
        console_mock.url = '/SERIAL'

        self.mox.StubOutWithMock(api.nova, 'server_serial_console')
        api.nova.server_serial_console(IgnoreArg(), server.id) \
            .AndReturn(console_mock)

        self.mox.ReplayAll()
        self.setup_consoles()

    def test_get_console_serial(self):
        server = self.servers.first()
        self._get_console_serial(server)
        url = '/SERIAL'
        data = console.get_console(self.request, 'SERIAL', server)[1]
        self.assertEqual(data, url)

    def test_get_console_auto_iterate_available(self):
        server = self.servers.first()

        console_mock = self.mox.CreateMock(api.nova.RDPConsole)
        console_mock.url = '/RDP'

        self.mox.StubOutWithMock(api.nova, 'server_vnc_console')
        api.nova.server_vnc_console(IgnoreArg(), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.StubOutWithMock(api.nova, 'server_spice_console')
        api.nova.server_spice_console(IgnoreArg(), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.StubOutWithMock(api.nova, 'server_rdp_console')
        api.nova.server_rdp_console(IgnoreArg(), server.id) \
            .AndReturn(console_mock)

        self.mox.ReplayAll()
        self.setup_consoles()

        url = '/RDP&title=%s(%s)' % (server.name, server.id)
        data = console.get_console(self.request, 'AUTO', server)[1]
        self.assertEqual(data, url)

    def test_get_console_auto_iterate_serial_available(self):
        server = self.servers.first()

        console_mock = self.mox.CreateMock(api.nova.SerialConsole)
        console_mock.url = '/SERIAL'

        self.mox.StubOutWithMock(api.nova, 'server_vnc_console')
        api.nova.server_vnc_console(IgnoreArg(), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.StubOutWithMock(api.nova, 'server_spice_console')
        api.nova.server_spice_console(IgnoreArg(), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.StubOutWithMock(api.nova, 'server_rdp_console')
        api.nova.server_rdp_console(IgnoreArg(), server.id) \
            .AndRaise(self.exceptions.nova)

        self.mox.StubOutWithMock(api.nova, 'server_serial_console')
        api.nova.server_serial_console(IgnoreArg(), server.id) \
            .AndReturn(console_mock)

        self.mox.ReplayAll()
        self.setup_consoles()

        url = '/SERIAL'
        data = console.get_console(self.request, 'AUTO', server)[1]
        self.assertEqual(data, url)

    def test_invalid_console_type_raise_value_error(self):
        self.assertRaises(exceptions.NotAvailable,
                          console.get_console, None, 'FAKE', None)

    @helpers.create_stubs({api.neutron: ('network_list_for_tenant',)})
    def test_interface_attach_get(self):
        server = self.servers.first()
        api.neutron.network_list_for_tenant(IsA(http.HttpRequest),
                                            self.tenant.id) \
            .AndReturn(self.networks.list()[:1])

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:attach_interface',
                      args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res,
                                'project/instances/attach_interface.html')

    @helpers.create_stubs({api.neutron: ('network_list_for_tenant',),
                           api.nova: ('interface_attach',)})
    def test_interface_attach_post(self):
        server = self.servers.first()
        network = api.neutron.network_list_for_tenant(IsA(http.HttpRequest),
                                                      self.tenant.id) \
            .AndReturn(self.networks.list()[:1])
        api.nova.interface_attach(IsA(http.HttpRequest), server.id,
                                  net_id=network[0].id)

        self.mox.ReplayAll()

        form_data = {'instance_id': server.id,
                     'network': network[0].id}

        url = reverse('horizon:project:instances:attach_interface',
                      args=[server.id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.create_stubs({api.neutron: ('port_list',)})
    def test_interface_detach_get(self):
        server = self.servers.first()
        api.neutron.port_list(IsA(http.HttpRequest),
                              device_id=server.id)\
            .AndReturn([self.ports.first()])

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:detach_interface',
                      args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res,
                                'project/instances/detach_interface.html')

    @helpers.create_stubs({api.neutron: ('port_list',),
                           api.nova: ('interface_detach',)})
    def test_interface_detach_post(self):
        server = self.servers.first()
        port = self.ports.first()
        api.neutron.port_list(IsA(http.HttpRequest),
                              device_id=server.id)\
            .AndReturn([port])
        api.nova.interface_detach(IsA(http.HttpRequest), server.id, port.id)

        self.mox.ReplayAll()

        form_data = {'instance_id': server.id,
                     'port': port.id}

        url = reverse('horizon:project:instances:detach_interface',
                      args=[server.id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @helpers.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'profile_support': 'cisco'})
    @helpers.create_stubs({api.glance: ('image_list_detailed',),
                           api.neutron: ('network_list',
                                         'profile_list',
                                         'port_create',
                                         'port_delete',
                                         'port_list'),
                           api.nova: ('extension_supported',
                                      'flavor_list',
                                      'keypair_list',
                                      'availability_zone_list',
                                      'server_group_list',
                                      'server_create',),
                           api.network: ('security_group_list',),
                           cinder: ('volume_list',
                                    'volume_snapshot_list',),
                           quotas: ('tenant_quota_usages',)})
    def test_port_cleanup_called_on_failed_vm_launch(self):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        quota_usages = self.quota_usages.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        volumes = [v for v in self.volumes.list() if (v.status == AVAILABLE
                                                      and v.bootable ==
                                                      'true')]
        cinder.volume_list(IsA(http.HttpRequest),
                           search_opts=VOLUME_SEARCH_OPTS) \
            .AndReturn(volumes)
        volumes = [v for v in self.volumes.list() if (v.status == AVAILABLE)]
        cinder.volume_snapshot_list(IsA(http.HttpRequest),
                                    search_opts=SNAPSHOT_SEARCH_OPTS) \
            .AndReturn(volumes)
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.nova.keypair_list(IgnoreArg()).AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([self.images.list(), False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([[], False, False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
            .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
            .AndReturn(self.networks.list()[1:])
        for net in self.networks.list():
            api.neutron.port_list(IsA(http.HttpRequest),
                                  network_id=net.id) \
                .AndReturn(self.ports.list())
        policy_profiles = self.policy_profiles.list()
        policy_profile_id = self.policy_profiles.first().id
        port = self.ports.first()
        api.neutron.profile_list(
            IsA(http.HttpRequest), 'policy').AndReturn(policy_profiles)
        api.neutron.port_create(
            IsA(http.HttpRequest),
            self.networks.first().id,
            policy_profile_id=policy_profile_id).AndReturn(port)
        nics = [{"port-id": port.id}]
        api.nova.extension_supported('DiskConfig',
                                     IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.nova.extension_supported('ConfigDrive',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.extension_supported('ServerGroups',
                                     IsA(http.HttpRequest)).AndReturn(True)
        api.nova.server_group_list(IsA(http.HttpRequest)).AndReturn([])
        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               image.id,
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [str(sec_group.id)],
                               block_device_mapping=None,
                               block_device_mapping_v2=None,
                               nics=nics,
                               availability_zone=avail_zone.zoneName,
                               instance_count=IsA(int),
                               admin_pass='password',
                               disk_config='AUTO',
                               config_drive=False,
                               scheduler_hints={}) \
            .AndRaise(self.exceptions.neutron)
        api.neutron.port_delete(IsA(http.HttpRequest), port.id)
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
            .AndReturn(quota_usages)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'image_id',
                     'source_id': image.id,
                     'volume_size': '1',
                     'image_id': image.id,
                     'availability_zone': avail_zone.zoneName,
                     'keypair': keypair.name,
                     'name': server.name,
                     'script_source': 'raw',
                     'script_data': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': [str(sec_group.id)],
                     'volume_type': '',
                     'network': self.networks.first().id,
                     'count': 1,
                     'admin_pass': 'password',
                     'confirm_admin_pass': 'password',
                     'disk_config': 'AUTO',
                     'config_drive': False,
                     'profile': self.policy_profiles.first().id}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)
