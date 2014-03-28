# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import json
import uuid

from django.conf import settings
from django.core.urlresolvers import reverse
from django import http
from django.test import utils as test_utils
from django.utils.datastructures import SortedDict
from django.utils.http import urlencode

from mox import IgnoreArg  # noqa
from mox import IsA  # noqa

from horizon.workflows import views

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.project.instances import tables
from openstack_dashboard.dashboards.project.instances import tabs
from openstack_dashboard.dashboards.project.instances import workflows

INDEX_URL = reverse('horizon:project:instances:index')
SEC_GROUP_ROLE_PREFIX = \
    workflows.update_instance.INSTANCE_SEC_GROUP_SLUG + "_role_"


class InstanceTests(test.TestCase):
    @test.create_stubs({api.nova: ('flavor_list',
                                   'server_list',
                                   'tenant_absolute_limits',
                                   'extension_supported',),
                        api.glance: ('image_list_detailed',),
                        api.network:
                            ('floating_ip_simple_associate_supported',
                             'servers_update_addresses',),
                        })
    def test_index(self):
        servers = self.servers.list()
        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
           .MultipleTimes().AndReturn(self.limits['absolute'])
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res,
            'project/instances/index.html')
        instances = res.context['instances_table'].data

        self.assertItemsEqual(instances, self.servers.list())

    @test.create_stubs({api.nova: ('server_list',
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

    @test.create_stubs({api.nova: ('flavor_list',
                                   'server_list',
                                   'flavor_get',
                                   'tenant_absolute_limits',
                                   'extension_supported',),
                        api.glance: ('image_list_detailed',),
                        api.network:
                            ('floating_ip_simple_associate_supported',
                             'servers_update_addresses',),
                        })
    def test_index_flavor_list_exception(self):
        servers = self.servers.list()
        flavors = self.flavors.list()
        full_flavors = SortedDict([(f.id, f) for f in flavors])
        search_opts = {'marker': None, 'paginate': True}
        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndRaise(self.exceptions.nova)
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False))
        for server in servers:
            api.nova.flavor_get(IsA(http.HttpRequest), server.flavor["id"]). \
                AndReturn(full_flavors[server.flavor["id"]])
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
           .MultipleTimes().AndReturn(self.limits['absolute'])
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/instances/index.html')
        instances = res.context['instances_table'].data

        self.assertItemsEqual(instances, self.servers.list())

    @test.create_stubs({api.nova: ('flavor_list',
                                   'server_list',
                                   'flavor_get',
                                   'tenant_absolute_limits',
                                   'extension_supported',),
                        api.glance: ('image_list_detailed',),
                        api.network:
                            ('floating_ip_simple_associate_supported',
                             'servers_update_addresses',),
                        })
    def test_index_flavor_get_exception(self):
        servers = self.servers.list()
        flavors = self.flavors.list()
        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        # UUIDs generated using indexes are unlikely to match
        # any of existing flavor ids and are guaranteed to be deterministic.
        for i, server in enumerate(servers):
            server.flavor['id'] = str(uuid.UUID(int=i))

        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.flavor_list(IsA(http.HttpRequest)).AndReturn(flavors)
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False))
        for server in servers:
            api.nova.flavor_get(IsA(http.HttpRequest), server.flavor["id"]). \
                AndRaise(self.exceptions.nova)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
           .MultipleTimes().AndReturn(self.limits['absolute'])
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        instances = res.context['instances_table'].data

        self.assertTemplateUsed(res, 'project/instances/index.html')
        self.assertMessageCount(res, error=len(servers))
        self.assertItemsEqual(instances, self.servers.list())

    @test.create_stubs({api.nova: ('flavor_list',
                                   'server_list',
                                   'tenant_absolute_limits',
                                   'extension_supported',),
                        api.glance: ('image_list_detailed',),
                        api.network:
                            ('floating_ip_simple_associate_supported',
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
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
           .MultipleTimes().AndReturn(self.limits['absolute'])
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/instances/index.html')
        instances = res.context['instances_table'].data
        self.assertEqual(len(instances), len(servers))
        self.assertContains(res, "(not found)")

    @test.create_stubs({api.nova: ('server_list',
                                   'flavor_list',
                                   'server_delete',),
                        api.glance: ('image_list_detailed',),
                        api.network: ('servers_update_addresses',)})
    def test_terminate_instance(self):
        servers = self.servers.list()
        server = servers[0]

        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False))
        api.nova.server_delete(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        formData = {'action': 'instances__terminate__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_list',
                                   'flavor_list',
                                   'server_delete',),
                        api.glance: ('image_list_detailed',),
                        api.network: ('servers_update_addresses',)})
    def test_terminate_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False))
        api.nova.server_delete(IsA(http.HttpRequest), server.id) \
                          .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__terminate__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_pause',
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
            .AndReturn((self.images.list(), False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_pause(IsA(http.HttpRequest), server.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_pause',
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
            .AndReturn((self.images.list(), False))
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

    @test.create_stubs({api.nova: ('server_unpause',
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
            .AndReturn((self.images.list(), False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_unpause(IsA(http.HttpRequest), server.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_unpause',
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
            .AndReturn((self.images.list(), False))
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

    @test.create_stubs({api.nova: ('server_reboot',
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
            .AndReturn((self.images.list(), False))
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

    @test.create_stubs({api.nova: ('server_reboot',
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
            .AndReturn((self.images.list(), False))
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

    @test.create_stubs({api.nova: ('server_reboot',
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
            .AndReturn((self.images.list(), False))
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

    @test.create_stubs({api.nova: ('server_suspend',
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
            .AndReturn((self.images.list(), False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_suspend(IsA(http.HttpRequest), unicode(server.id))

        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_suspend',
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
            .AndReturn((self.images.list(), False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_suspend(IsA(http.HttpRequest), unicode(server.id)) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_resume',
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
            .AndReturn((self.images.list(), False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_resume(IsA(http.HttpRequest), unicode(server.id))

        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_resume',
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
            .AndReturn((self.images.list(), False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.server_resume(IsA(http.HttpRequest),
                               unicode(server.id)) \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ("server_get",
                                   "instance_volumes_list",
                                   "flavor_get"),
                        api.network: ("server_security_groups",
                                      "servers_update_addresses")})
    def test_instance_details_volumes(self):
        server = self.servers.first()
        volumes = [self.volumes.list()[1]]

        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.network.servers_update_addresses(IsA(http.HttpRequest),
                                             IgnoreArg())
        api.nova.instance_volumes_list(IsA(http.HttpRequest),
                                       server.id).AndReturn(volumes)
        api.nova.flavor_get(IsA(http.HttpRequest), server.flavor['id']) \
                .AndReturn(self.flavors.first())
        api.network.server_security_groups(IsA(http.HttpRequest), server.id) \
                .AndReturn(self.security_groups.first())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:detail',
                      args=[server.id])
        res = self.client.get(url)

        self.assertItemsEqual(res.context['instance'].volumes, volumes)

    @test.create_stubs({api.nova: ("server_get",
                                   "instance_volumes_list",
                                   "flavor_get"),
                        api.network: ("server_security_groups",
                                      "servers_update_addresses")})
    def test_instance_details_volume_sorting(self):
        server = self.servers.first()
        volumes = self.volumes.list()[1:3]

        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.network.servers_update_addresses(IsA(http.HttpRequest),
                                             IgnoreArg())
        api.nova.instance_volumes_list(IsA(http.HttpRequest),
                                       server.id).AndReturn(volumes)
        api.nova.flavor_get(IsA(http.HttpRequest), server.flavor['id']) \
                .AndReturn(self.flavors.first())
        api.network.server_security_groups(IsA(http.HttpRequest), server.id) \
                .AndReturn(self.security_groups.first())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:detail',
                      args=[server.id])
        res = self.client.get(url)

        self.assertItemsEqual(res.context['instance'].volumes, volumes)
        self.assertEqual(res.context['instance'].volumes[0].device,
                         "/dev/hda")
        self.assertEqual(res.context['instance'].volumes[1].device,
                         "/dev/hdk")

    @test.create_stubs({api.nova: ("server_get",
                                   "instance_volumes_list",
                                   "flavor_get"),
                        api.network: ("server_security_groups",
                                      "servers_update_addresses")})
    def test_instance_details_metadata(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.network.servers_update_addresses(IsA(http.HttpRequest),
                                             IgnoreArg())
        api.nova.instance_volumes_list(IsA(http.HttpRequest),
                                       server.id).AndReturn([])
        api.nova.flavor_get(IsA(http.HttpRequest), server.flavor['id']) \
                .AndReturn(self.flavors.first())
        api.network.server_security_groups(IsA(http.HttpRequest), server.id) \
                .AndReturn(self.security_groups.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:detail',
                      args=[server.id])
        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("overview").get_id())
        res = self.client.get(url + qs)

        self.assertContains(res, "<dd>keyName</dd>", 1)
        self.assertContains(res, "<dt>someMetaLabel</dt>", 1)
        self.assertContains(res, "<dd>someMetaData</dd>", 1)
        self.assertContains(res, "<dt>some&lt;b&gt;html&lt;/b&gt;label</dt>",
                            1)
        self.assertContains(res, "<dd>&lt;!--</dd>", 1)
        self.assertContains(res, "<dt>empty</dt>", 1)
        #TODO(david-lyle): uncomment when fixed with Django 1.6
        #self.assertContains(res, "<dd><em>N/A</em></dd>", 1)

    @test.create_stubs({api.nova: ("server_get",
                                   "instance_volumes_list",
                                   "flavor_get"),
                        api.network: ("server_security_groups",
                                      "servers_update_addresses")})
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

        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.network.servers_update_addresses(IsA(http.HttpRequest),
                                             IgnoreArg())
        api.nova.instance_volumes_list(IsA(http.HttpRequest),
                                       server.id).AndReturn([])
        api.nova.flavor_get(IsA(http.HttpRequest), server.flavor['id']) \
                .AndReturn(self.flavors.first())
        api.network.server_security_groups(IsA(http.HttpRequest), server.id) \
                .AndReturn(self.security_groups.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:detail',
                      args=[server.id])
        res = self.client.get(url)
        self.assertItemsEqual(res.context['instance'].fault, server.fault)

    @test.create_stubs({api.nova: ('server_get',)})
    def test_instance_details_exception(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id) \
                        .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:detail',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ("server_get",)})
    def test_instance_details_unauthorized(self):
        server = self.servers.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id)\
            .AndRaise(self.exceptions.nova_unauthorized)
        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:detail',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_console_output',)})
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

    @test.create_stubs({api.nova: ('server_console_output',)})
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

    def test_instance_vnc(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/vncserver'

        console_mock = self.mox.CreateMock(api.nova.VNCConsole)
        console_mock.url = CONSOLE_OUTPUT

        self.mox.StubOutWithMock(api.nova, 'server_vnc_console')
        self.mox.StubOutWithMock(api.nova, 'server_get')
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.server_vnc_console(IgnoreArg(), server.id) \
            .AndReturn(console_mock)
        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:vnc',
                      args=[server.id])
        res = self.client.get(url)
        redirect = CONSOLE_OUTPUT + '&title=%s(1)' % server.name
        self.assertRedirectsNoFollow(res, redirect)

    @test.create_stubs({api.nova: ('server_vnc_console',)})
    def test_instance_vnc_exception(self):
        server = self.servers.first()

        api.nova.server_vnc_console(IsA(http.HttpRequest), server.id) \
                        .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:vnc',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_spice(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/spiceserver'

        console_mock = self.mox.CreateMock(api.nova.SPICEConsole)
        console_mock.url = CONSOLE_OUTPUT

        self.mox.StubOutWithMock(api.nova, 'server_spice_console')
        self.mox.StubOutWithMock(api.nova, 'server_get')
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.server_spice_console(IgnoreArg(), server.id) \
            .AndReturn(console_mock)
        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:spice',
                      args=[server.id])
        res = self.client.get(url)
        redirect = CONSOLE_OUTPUT + '&title=%s(1)' % server.name
        self.assertRedirectsNoFollow(res, redirect)

    @test.create_stubs({api.nova: ('server_spice_console',)})
    def test_instance_spice_exception(self):
        server = self.servers.first()

        api.nova.server_spice_console(IsA(http.HttpRequest), server.id) \
                        .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:spice',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_rdp(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/rdpserver'

        console_mock = self.mox.CreateMock(api.nova.RDPConsole)
        console_mock.url = CONSOLE_OUTPUT

        self.mox.StubOutWithMock(api.nova, 'server_rdp_console')
        self.mox.StubOutWithMock(api.nova, 'server_get')
        api.nova.server_get(IsA(http.HttpRequest), server.id) \
            .AndReturn(server)
        api.nova.server_rdp_console(IgnoreArg(), server.id) \
            .AndReturn(console_mock)
        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:rdp',
                      args=[server.id])
        res = self.client.get(url)
        redirect = CONSOLE_OUTPUT + '&title=%s(1)' % server.name
        self.assertRedirectsNoFollow(res, redirect)

    @test.create_stubs({api.nova: ('server_rdp_console',)})
    def test_instance_rdp_exception(self):
        server = self.servers.first()

        api.nova.server_rdp_console(IsA(http.HttpRequest), server.id) \
                        .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:rdp',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_get',
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
                                       marker=None).AndReturn([[], False])

        self.mox.ReplayAll()

        formData = {'instance_id': server.id,
                    'method': 'CreateSnapshot',
                    'name': 'snapshot1'}
        url = reverse('horizon:project:images:snapshots:create',
                      args=[server.id])
        redir_url = reverse('horizon:project:images:index')
        res = self.client.post(url, formData)
        self.assertRedirects(res, redir_url)

    @test.create_stubs({api.nova: ('get_password',)})
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

    @test.create_stubs({api.nova: ('get_password',)})
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

    @test.create_stubs(instance_update_get_stubs)
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

    @test.create_stubs(instance_update_get_stubs)
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

    @test.create_stubs(instance_update_post_stubs)
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

    @test.create_stubs(instance_update_post_stubs)
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

    @test.create_stubs(instance_update_post_stubs)
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

    @test.create_stubs({api.nova: ('extension_supported',
                                   'flavor_list',
                                   'keypair_list',
                                   'tenant_absolute_limits',
                                   'availability_zone_list',),
                        api.network: ('security_group_list',),
                        cinder: ('volume_snapshot_list',
                                 'volume_list',),
                        api.neutron: ('network_list',
                                      'profile_list',),
                        api.glance: ('image_list_detailed',)})
    def test_launch_instance_get(self,
                                 expect_password_fields=True,
                                 block_device_mapping_v2=True,
                                 custom_flavor_sort=None,
                                 only_one_network=False):
        image = self.images.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
                .AndReturn(block_device_mapping_v2)
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
            .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                .AndReturn([[], False])
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
        # TODO(absubram): Remove if clause and create separate
        # test stubs for when profile_support is being used.
        # Additionally ensure those are always run even in default setting
        if api.neutron.is_port_profiles_supported():
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
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
        self.assertQuerysetEqual(workflow.steps,
                            ['<SetInstanceDetails: setinstancedetailsaction>',
                             '<SetAccessControls: setaccesscontrolsaction>',
                             '<SetNetwork: setnetworkaction>',
                             '<PostCreationStep: customizeaction>',
                             '<SetAdvanced: setadvancedaction>'])

        if custom_flavor_sort == 'id':
            # Reverse sorted by id
            sorted_flavors = (
                ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'm1.secret'),
                ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'm1.massive'),
                ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'm1.tiny'),
            )
        elif custom_flavor_sort == 'name':
            sorted_flavors = (
                ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'm1.massive'),
                ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'm1.secret'),
                ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'm1.tiny'),
            )
        elif custom_flavor_sort == test.my_custom_sort:
            sorted_flavors = (
                ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'm1.secret'),
                ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'm1.tiny'),
                ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'm1.massive'),
            )
        else:
            # Default - sorted by RAM
            sorted_flavors = (
                ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'm1.tiny'),
                ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'm1.massive'),
                ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'm1.secret'),
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

        checked_label = '<label for="id_network_0"><input checked="checked"'
        if only_one_network:
            self.assertContains(res, checked_label)
        else:
            self.assertNotContains(res, checked_label)

    @test_utils.override_settings(
        OPENSTACK_HYPERVISOR_FEATURES={'can_set_password': False})
    def test_launch_instance_get_without_password(self):
        self.test_launch_instance_get(expect_password_fields=False)

    def test_launch_instance_get_no_block_device_mapping_v2_supported(self):
        self.test_launch_instance_get(block_device_mapping_v2=False)

    @test_utils.override_settings(
        CREATE_INSTANCE_FLAVOR_SORT={
            'key': 'id',
            'reverse': True,
        })
    def test_launch_instance_get_custom_flavor_sort_by_id(self):
        self.test_launch_instance_get(custom_flavor_sort='id')

    @test_utils.override_settings(
        CREATE_INSTANCE_FLAVOR_SORT={
            'key': 'name',
            'reverse': False,
        })
    def test_launch_instance_get_custom_flavor_sort_by_name(self):
        self.test_launch_instance_get(custom_flavor_sort='name')

    @test_utils.override_settings(
        CREATE_INSTANCE_FLAVOR_SORT={
            'key': test.my_custom_sort,
            'reverse': False,
        })
    def test_launch_instance_get_custom_flavor_sort_by_callable(self):
        self.test_launch_instance_get(custom_flavor_sort=test.my_custom_sort)

    @test_utils.override_settings(
        CREATE_INSTANCE_FLAVOR_SORT={
            'key': 'no_such_column',
            'reverse': False,
        })
    def test_launch_instance_get_custom_flavor_sort_by_missing_column(self):
        self.test_launch_instance_get(custom_flavor_sort='no_such_column')

    def test_launch_instance_get_with_only_one_network(self):
        self.test_launch_instance_get(only_one_network=True)

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.neutron: ('network_list',
                                      'profile_list',
                                      'port_create',),
                        api.nova: ('extension_supported',
                                   'flavor_list',
                                   'keypair_list',
                                   'availability_zone_list',
                                   'server_create',),
                        api.network: ('security_group_list',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_launch_instance_post(self):
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
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        # TODO(absubram): Remove if clause and create separate
        # test stubs for when profile_support is being used.
        # Additionally ensure those are always run even in default setting
        if api.neutron.is_port_profiles_supported():
            policy_profiles = self.policy_profiles.list()
            policy_profile_id = self.policy_profiles.first().id
            port = self.ports.first()
            api.neutron.profile_list(
                IsA(http.HttpRequest),
                'policy').AndReturn(policy_profiles)
            api.neutron.port_create(
                IsA(http.HttpRequest),
                network_id=self.networks.first().id,
                policy_profile_id=policy_profile_id).AndReturn(port)
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn([])
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])
        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               image.id,
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [sec_group.name],
                               block_device_mapping=None,
                               block_device_mapping_v2=None,
                               nics=nics,
                               availability_zone=avail_zone.zoneName,
                               instance_count=IsA(int),
                               admin_pass=u'',
                               disk_config=u'AUTO')
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
                     'customization_script': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': sec_group.name,
                     'availability_zone': avail_zone.zoneName,
                     'volume_type': '',
                     'network': self.networks.first().id,
                     'count': 1,
                     'disk_config': 'AUTO'}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.neutron: ('network_list',
                                      'profile_list',),
                        api.nova: ('extension_supported',
                                   'flavor_list',
                                   'keypair_list',
                                   'availability_zone_list',
                                   'server_create',),
                        api.network: ('security_group_list',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_launch_instance_post_boot_from_volume(self):
        flavor = self.flavors.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        device_name = u'vda'
        volume_choice = "%s:vol" % volume.id
        block_device_mapping = {device_name: u"%s::0" % volume_choice}
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
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        # TODO(absubram): Remove if clause and create separate
        # test stubs for when profile_support is being used.
        # Additionally ensure those are always run even in default setting
        if api.neutron.is_port_profiles_supported():
            policy_profiles = self.policy_profiles.list()
            policy_profile_id = self.policy_profiles.first().id
            port = self.ports.first()
            api.neutron.profile_list(
                IsA(http.HttpRequest),
                'policy').AndReturn(policy_profiles)
            api.neutron.port_create(
                IsA(http.HttpRequest),
                network_id=self.networks.first().id,
                policy_profile_id=policy_profile_id).AndReturn(port)
            nics = [{"port-id": port.id}]
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])
        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               '',
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [sec_group.name],
                               block_device_mapping=block_device_mapping,
                               block_device_mapping_v2=None,
                               nics=nics,
                               availability_zone=avail_zone.zoneName,
                               instance_count=IsA(int),
                               admin_pass=u'',
                               disk_config=u'AUTO')
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
                .AndReturn(quota_usages)

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'volume_id',
                     'source_id': volume_choice,
                     'keypair': keypair.name,
                     'name': server.name,
                     'customization_script': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': sec_group.name,
                     'availability_zone': avail_zone.zoneName,
                     'volume_size': '1',
                     'volume_id': volume_choice,
                     'device_name': device_name,
                     'network': self.networks.first().id,
                     'count': 1,
                     'disk_config': 'AUTO'}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.neutron: ('network_list',
                                      'profile_list',
                                      'port_create'),
                        api.nova: ('server_create',
                                   'extension_supported',
                                   'flavor_list',
                                   'keypair_list',
                                   'availability_zone_list',
                                   'tenant_absolute_limits',),
                        api.network: ('security_group_list',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_launch_instance_post_no_images_available_boot_from_volume(self):
        flavor = self.flavors.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        device_name = u'vda'
        volume_choice = "%s:vol" % volume.id
        block_device_mapping = {device_name: u"%s::0" % volume_choice}
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
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])

        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        # TODO(absubram): Remove if clause and create separate
        # test stubs for when profile_support is being used.
        # Additionally ensure those are always run even in default setting
        if api.neutron.is_port_profiles_supported():
            policy_profiles = self.policy_profiles.list()
            policy_profile_id = self.policy_profiles.first().id
            port = self.ports.first()
            api.neutron.profile_list(
                IsA(http.HttpRequest),
                'policy').AndReturn(policy_profiles)
            api.neutron.port_create(
                IsA(http.HttpRequest),
                network_id=self.networks.first().id,
                policy_profile_id=policy_profile_id).AndReturn(port)
            nics = [{"port-id": port.id}]
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
                .AndReturn(quota_usages)

        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               '',
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [sec_group.name],
                               block_device_mapping=block_device_mapping,
                               block_device_mapping_v2=None,
                               nics=nics,
                               availability_zone=avail_zone.zoneName,
                               instance_count=IsA(int),
                               admin_pass=u'',
                               disk_config='MANUAL')

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'volume_id',
                     #'image_id': '',
                     'keypair': keypair.name,
                     'name': server.name,
                     'customization_script': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': sec_group.name,
                     'availability_zone': avail_zone.zoneName,
                     'network': self.networks.first().id,
                     'volume_type': 'volume_id',
                     'volume_id': volume_choice,
                     'device_name': device_name,
                     'count': 1,
                     'disk_config': 'MANUAL'}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.neutron: ('network_list',
                                      'profile_list',),
                        api.nova: ('extension_supported',
                                   'flavor_list',
                                   'keypair_list',
                                   'availability_zone_list',
                                   'tenant_absolute_limits',),
                        api.network: ('security_group_list',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_launch_instance_post_no_images_available(self):
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
                .AndReturn([[], False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                .AndReturn([[], False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        # TODO(absubram): Remove if clause and create separate
        # test stubs for when profile_support is being used.
        # Additionally ensure those are always run even in default setting
        if api.neutron.is_port_profiles_supported():
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
                .AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
                .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
                .AndReturn(self.availability_zones.list())
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn([])
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
                .AndReturn(quota_usages)

        self.mox.ReplayAll()

        form_data = {'flavor': flavor.id,
                     'source_type': 'image_id',
                     'image_id': '',
                     'keypair': keypair.name,
                     'name': server.name,
                     'customization_script': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': sec_group.name,
                     'availability_zone': avail_zone.zoneName,
                     'volume_type': '',
                     'count': 1}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertFormErrors(res, 1, "You must select an image.")
        self.assertTemplateUsed(res, views.WorkflowView.template_name)

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.neutron: ('network_list',
                                      'profile_list',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',),
                        api.network: ('security_group_list',),
                        api.nova: ('extension_supported',
                                   'flavor_list',
                                   'keypair_list',
                                   'tenant_absolute_limits',
                                   'availability_zone_list',)})
    def test_launch_flavorlist_error(self):
        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
                .AndReturn(True)
        cinder.volume_list(IsA(http.HttpRequest)) \
            .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)) \
            .AndReturn(self.volumes.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        # TODO(absubram): Remove if clause and create separate
        # test stubs for when profile_support is being used.
        # Additionally ensure those are always run even in default setting
        if api.neutron.is_port_profiles_supported():
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
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

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.neutron: ('network_list',
                                      'profile_list',
                                      'port_create',),
                        api.nova: ('extension_supported',
                                   'flavor_list',
                                   'keypair_list',
                                   'availability_zone_list',
                                   'server_create',),
                        api.network: ('security_group_list',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_launch_form_keystone_exception(self):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'userData'
        nics = [{"net-id": self.networks.first().id, "v4-fixed-ip": ''}]
        quota_usages = self.quota_usages.first()

        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
                .AndReturn(True)
        cinder.volume_snapshot_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.nova.keypair_list(IgnoreArg()).AndReturn(self.keypairs.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        api.nova.availability_zone_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.availability_zones.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        # TODO(absubram): Remove if clause and create separate
        # test stubs for when profile_support is being used.
        # Additionally ensure those are always run even in default setting
        if api.neutron.is_port_profiles_supported():
            policy_profiles = self.policy_profiles.list()
            policy_profile_id = self.policy_profiles.first().id
            port = self.ports.first()
            api.neutron.profile_list(
                IsA(http.HttpRequest),
                'policy').AndReturn(policy_profiles)
            api.neutron.port_create(
                IsA(http.HttpRequest),
                network_id=self.networks.first().id,
                policy_profile_id=policy_profile_id).AndReturn(port)
            nics = [{"port-id": port.id}]
        cinder.volume_list(IgnoreArg()).AndReturn(self.volumes.list())
        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               image.id,
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [sec_group.name],
                               block_device_mapping=None,
                               block_device_mapping_v2=None,
                               nics=nics,
                               availability_zone=avail_zone.zoneName,
                               instance_count=IsA(int),
                               admin_pass='password',
                               disk_config='AUTO') \
                      .AndRaise(self.exceptions.keystone)
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
                     'customization_script': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': sec_group.name,
                     'volume_type': '',
                     'network': self.networks.first().id,
                     'count': 1,
                     'admin_pass': 'password',
                     'confirm_admin_pass': 'password',
                     'disk_config': 'AUTO'}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.neutron: ('network_list',
                                      'profile_list',),
                        api.nova: ('extension_supported',
                                   'flavor_list',
                                   'keypair_list',
                                   'tenant_absolute_limits',
                                   'availability_zone_list',),
                        api.network: ('security_group_list',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_launch_form_instance_count_error(self):
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
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        # TODO(absubram): Remove if clause and create separate
        # test stubs for when profile_support is being used.
        # Additionally ensure those are always run even in default setting
        if api.neutron.is_port_profiles_supported():
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])

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
                     'customization_script': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': sec_group.name,
                     'volume_type': 'volume_id',
                     'volume_id': volume_choice,
                     'device_name': device_name,
                     'count': 0}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertContains(res, "greater than or equal to 1")

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.neutron: ('network_list',
                                      'profile_list',),
                        api.nova: ('extension_supported',
                                   'flavor_list',
                                   'keypair_list',
                                   'tenant_absolute_limits',
                                   'availability_zone_list',),
                        api.network: ('security_group_list',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',),
                        quotas: ('tenant_quota_usages',)})
    def _test_launch_form_instance_requirement_error(self, image, flavor):
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
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        # TODO(absubram): Remove if clause and create separate
        # test stubs for when profile_support is being used.
        # Additionally ensure those are always run even in default setting
        if api.neutron.is_port_profiles_supported():
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])

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
                     'customization_script': customization_script,
                     'project_id': self.tenants.first().id,
                     'user_id': self.user.id,
                     'groups': sec_group.name,
                     'volume_type': 'volume_id',
                     'volume_id': volume_choice,
                     'device_name': device_name,
                     'count': 1}

        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)
        msg = "The flavor &#39;%s&#39; is too small" % flavor.name
        self.assertContains(res, msg)

    def test_launch_form_instance_requirement_error_disk(self):
        flavor = self.flavors.first()
        image = self.images.first()
        image.min_ram = flavor.ram
        image.min_disk = flavor.disk + 1
        self._test_launch_form_instance_requirement_error(image, flavor)

    def test_launch_form_instance_requirement_error_ram(self):
        flavor = self.flavors.first()
        image = self.images.first()
        image.min_ram = flavor.ram + 1
        image.min_disk = flavor.disk
        self._test_launch_form_instance_requirement_error(image, flavor)

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.neutron: ('network_list',
                                      'profile_list',),
                        api.nova: ('extension_supported',
                                   'flavor_list',
                                   'keypair_list',
                                   'tenant_absolute_limits',
                                   'availability_zone_list',),
                        api.network: ('security_group_list',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',),
                        quotas: ('tenant_quota_usages',)})
    def _test_launch_form_instance_volume_size(self, image, volume_size, msg):
        flavor = self.flavors.get(name='m1.massive')
        keypair = self.keypairs.first()
        server = self.servers.first()
        sec_group = self.security_groups.first()
        avail_zone = self.availability_zones.first()
        customization_script = 'user data'
        device_name = u'vda'
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
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        # TODO(absubram): Remove if clause and create separate
        # test stubs for when profile_support is being used.
        # Additionally ensure those are always run even in default setting
        if api.neutron.is_port_profiles_supported():
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])

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
            'customization_script': customization_script,
            'project_id': self.tenants.first().id,
            'user_id': self.user.id,
            'groups': sec_group.name,
            'volume_size': volume_size,
            'device_name': device_name,
            'count': 1
        }
        url = reverse('horizon:project:instances:launch')

        res = self.client.post(url, form_data)
        self.assertContains(res, msg)

    def test_launch_form_instance_volume_size_error(self):
        image = self.images.get(name='protected_images')
        volume_size = image.min_disk / 2
        msg = ("The Volume size is too small for the &#39;%s&#39; image" %
               image.name)
        self._test_launch_form_instance_volume_size(image, volume_size, msg)

    def test_launch_form_instance_non_int_volume_size(self):
        image = self.images.get(name='protected_images')
        msg = "Enter a whole number."
        self._test_launch_form_instance_volume_size(image, 1.5, msg)

    @test.create_stubs({api.nova: ('flavor_list', 'server_list',
                                   'tenant_absolute_limits',
                                   'extension_supported',),
                        api.glance: ('image_list_detailed',),
                        api.network:
                            ('floating_ip_simple_associate_supported',
                             'servers_update_addresses',),
                        })
    def test_launch_button_disabled_when_quota_exceeded(self):
        servers = self.servers.list()
        limits = self.limits['absolute']
        limits['totalInstancesUsed'] = limits['maxTotalInstances']

        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
            .MultipleTimes().AndReturn(limits)
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        launch = tables.LaunchLink()
        url = launch.get_link_url()
        classes = list(launch.get_default_classes()) + list(launch.classes)
        link_name = "%s (%s)" % (unicode(launch.verbose_name),
                                 "Quota exceeded")
        expected_string = "<a href='%s' id='instances__action_launch' " \
            "title='%s' class='%s disabled'>%s</a>" \
            % (url, link_name, " ".join(classes), link_name)

        res = self.client.get(INDEX_URL)
        self.assertContains(res, expected_string, html=True,
                            msg_prefix="The launch button is not disabled")

    @test.create_stubs({api.nova: ('flavor_list', 'server_list',
                                   'tenant_absolute_limits',
                                   'extension_supported',),
                        api.glance: ('image_list_detailed',),
                        api.network:
                            ('floating_ip_simple_associate_supported',
                             'servers_update_addresses',),
                        })
    def test_index_options_after_migrate(self):
        servers = self.servers.list()
        server = self.servers.first()
        server.status = "VERIFY_RESIZE"
        api.nova.extension_supported('AdminActions',
                                     IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(True)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .AndReturn((self.images.list(), False))
        search_opts = {'marker': None, 'paginate': True}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts) \
            .AndReturn([servers, False])
        api.network.servers_update_addresses(IsA(http.HttpRequest), servers)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest), reserved=True) \
           .MultipleTimes().AndReturn(self.limits['absolute'])
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertContains(res, "instances__confirm")
        self.assertContains(res, "instances__revert")

    @test.create_stubs({api.nova: ('extension_supported',
                                   'flavor_list',
                                   'keypair_list',
                                   'availability_zone_list',
                                   'tenant_absolute_limits',),
                        api.network: ('security_group_list',),
                        cinder: ('volume_snapshot_list',
                                 'volume_list',),
                        api.neutron: ('network_list',
                                      'profile_list'),
                        api.glance: ('image_list_detailed',)})
    def test_select_default_keypair_if_only_one(self):
        keypair = self.keypairs.first()

        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
            .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                .AndReturn([[], False])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.neutron.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        # TODO(absubram): Remove if clause and create separate
        # test stubs for when profile_support is being used.
        # Additionally ensure those are always run even in default setting
        if api.neutron.is_port_profiles_supported():
            policy_profiles = self.policy_profiles.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
        api.nova.tenant_absolute_limits(IsA(http.HttpRequest)) \
           .AndReturn(self.limits['absolute'])
        api.nova.extension_supported('BlockDeviceMappingV2Boot',
                                     IsA(http.HttpRequest)) \
                .AndReturn(True)
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

    @test.create_stubs({api.network: ('floating_ip_target_get_by_instance',
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
            .AndReturn((self.images.list(), False))
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

    @test.create_stubs({api.network: ('floating_ip_target_list_by_instance',
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
            .AndReturn((self.images.list(), False))
        api.network.floating_ip_target_list_by_instance(
            IsA(http.HttpRequest),
            server.id).AndReturn([server.id, ])
        api.network.tenant_floating_ip_list(
            IsA(http.HttpRequest)).AndReturn([fip])
        api.network.floating_ip_disassociate(
            IsA(http.HttpRequest), fip.id, server.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__disassociate__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_get',
                                   'flavor_list',
                                   'tenant_absolute_limits')})
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

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:resize', args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

    @test.create_stubs({api.nova: ('server_get',
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

    @test.create_stubs({api.nova: ('server_get',
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

    def _instance_resize_post(self, server_id, flavor_id, disk_config):
        formData = {'flavor': flavor_id,
                    'default_role': 'member',
                    'disk_config': disk_config}
        url = reverse('horizon:project:instances:resize',
                      args=[server_id])
        return self.client.post(url, formData)

    instance_resize_post_stubs = {
        api.nova: ('server_get', 'server_resize',
                   'flavor_list', 'flavor_get')}

    @test.create_stubs(instance_resize_post_stubs)
    def test_instance_resize_post(self):
        server = self.servers.first()
        flavor = self.flavors.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id) \
                .AndReturn(server)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.server_resize(IsA(http.HttpRequest), server.id, flavor.id,
                               'AUTO').AndReturn([])

        self.mox.ReplayAll()

        res = self._instance_resize_post(server.id, flavor.id, u'AUTO')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs(instance_resize_post_stubs)
    def test_instance_resize_post_api_exception(self):
        server = self.servers.first()
        flavor = self.flavors.first()

        api.nova.server_get(IsA(http.HttpRequest), server.id) \
                .AndReturn(server)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.server_resize(IsA(http.HttpRequest), server.id, flavor.id,
                               'AUTO') \
            .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        res = self._instance_resize_post(server.id, flavor.id, 'AUTO')
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_rebuild_instance_get(self, expect_password_fields=True):
        server = self.servers.first()
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
            .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
            .AndReturn([[], False])

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:rebuild', args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/instances/rebuild.html')

        password_field_label = 'Rebuild Password'
        if expect_password_fields:
            self.assertContains(res, password_field_label)
        else:
            self.assertNotContains(res, password_field_label)

    @test_utils.override_settings(
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
        api.nova: ('server_rebuild',),
        api.glance: ('image_list_detailed',)}

    @test.create_stubs(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_with_password(self):
        server = self.servers.first()
        image = self.images.first()
        password = u'testpass'

        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
            .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
            .AndReturn([[], False])
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

    @test.create_stubs(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_with_password_equals_none(self):
        server = self.servers.first()
        image = self.images.first()

        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
            .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
            .AndReturn([[], False])
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

    @test.create_stubs(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_password_do_not_match(self):
        server = self.servers.first()
        image = self.images.first()
        pass1 = u'somepass'
        pass2 = u'notsomepass'

        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
            .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
            .AndReturn([[], False])

        self.mox.ReplayAll()
        res = self._instance_rebuild_post(server.id, image.id,
                                          password=pass1,
                                          confirm_password=pass2,
                                          disk_config='MANUAL')

        self.assertContains(res, "Passwords do not match.")

    @test.create_stubs(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_with_empty_string(self):
        server = self.servers.first()
        image = self.images.first()

        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
            .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
            .AndReturn([[], False])
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

    @test.create_stubs(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_api_exception(self):
        server = self.servers.first()
        image = self.images.first()
        password = u'testpass'

        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
            .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
            .AndReturn([[], False])
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

    @test_utils.override_settings(API_RESULT_PAGE_SIZE=2)
    @test.create_stubs({api.nova: ('flavor_list',
                                   'server_list',
                                   'tenant_absolute_limits',
                                   'extension_supported',),
                        api.glance: ('image_list_detailed',),
                        api.network:
                            ('floating_ip_simple_associate_supported',
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
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(self.flavors.list())
        api.glance.image_list_detailed(IgnoreArg()) \
            .MultipleTimes().AndReturn((self.images.list(), False))

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
        api.network.floating_ip_simple_associate_supported(
            IsA(http.HttpRequest)).MultipleTimes().AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/instances/index.html')
        # get first page with 2 items
        self.assertEqual(len(res.context['instances_table'].data), page_size)

        # update INDEX_URL with marker object
        next_page_url = "?".join([reverse('horizon:project:instances:index'),
                    "=".join([tables.InstancesTable._meta.pagination_param,
                              servers[page_size - 1].id])])
        form_action = 'action="%s"' % next_page_url

        res = self.client.get(next_page_url)
        # get next page with remaining items (item 3)
        self.assertEqual(len(res.context['instances_table'].data), 1)
        # ensure that marker object exists in form action
        self.assertContains(res, form_action, count=1)

    @test_utils.override_settings(API_RESULT_PAGE_SIZE=2)
    @test.create_stubs({api.nova: ('server_list',
                                   'flavor_list',
                                   'server_delete',),
                        api.glance: ('image_list_detailed',),
                        api.network: ('servers_update_addresses',)})
    def test_terminate_instance_with_pagination(self):
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
            .AndReturn((self.images.list(), False))
        api.nova.server_delete(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        # update INDEX_URL with marker object
        next_page_url = "?".join([reverse('horizon:project:instances:index'),
                    "=".join([tables.InstancesTable._meta.pagination_param,
                              servers[page_size - 1].id])])
        formData = {'action': 'instances__terminate__%s' % server.id}
        res = self.client.post(next_page_url, formData)

        self.assertRedirectsNoFollow(res, next_page_url)
        self.assertMessageCount(success=1)


class InstanceAjaxTests(test.TestCase):
    @test.create_stubs({api.nova: ("server_get",
                                   "flavor_get",
                                   "extension_supported"),
                        api.neutron: ("is_extension_supported",)})
    def test_row_update(self):
        server = self.servers.first()
        instance_id = server.id
        flavor_id = server.flavor["id"]
        flavors = self.flavors.list()
        full_flavors = SortedDict([(f.id, f) for f in flavors])

        api.nova.extension_supported('AdminActions', IsA(http.HttpRequest))\
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

    @test.create_stubs({api.nova: ("server_get",
                                   "flavor_get",
                                   "extension_supported"),
                        api.neutron: ("is_extension_supported",)})
    def test_row_update_instance_error(self):
        server = self.servers.first()
        instance_id = server.id
        flavor_id = server.flavor["id"]
        flavors = self.flavors.list()
        full_flavors = SortedDict([(f.id, f) for f in flavors])

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
