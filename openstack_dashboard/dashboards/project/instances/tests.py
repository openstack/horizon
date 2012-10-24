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

from django import http
from django.core.urlresolvers import reverse
from django.utils.http import urlencode
from django.utils.datastructures import SortedDict

from mox import IsA, IgnoreArg

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas
from .tabs import InstanceDetailTabs
from .workflows import LaunchInstance


INDEX_URL = reverse('horizon:project:instances:index')


class InstanceTests(test.TestCase):
    @test.create_stubs({api: ('flavor_list', 'server_list',)})
    def test_index(self):
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())

        self.mox.ReplayAll()

        res = self.client.get(
            reverse('horizon:project:instances:index'))

        self.assertTemplateUsed(res,
            'project/instances/index.html')
        instances = res.context['instances_table'].data

        self.assertItemsEqual(instances, self.servers.list())

    @test.create_stubs({api: ('server_list',)})
    def test_index_server_list_exception(self):
        api.server_list(IsA(http.HttpRequest)).AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:instances:index'))

        self.assertTemplateUsed(res, 'project/instances/index.html')
        self.assertEqual(len(res.context['instances_table'].data), 0)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api: ('flavor_list', 'server_list', 'flavor_get',)})
    def test_index_flavor_list_exception(self):
        servers = self.servers.list()
        flavors = self.flavors.list()
        full_flavors = SortedDict([(f.id, f) for f in flavors])

        api.server_list(IsA(http.HttpRequest)).AndReturn(servers)
        api.flavor_list(IsA(http.HttpRequest)).AndRaise(self.exceptions.nova)
        for server in servers:
            api.flavor_get(IsA(http.HttpRequest), server.flavor["id"]). \
                                AndReturn(full_flavors[server.flavor["id"]])

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:instances:index'))

        self.assertTemplateUsed(res, 'project/instances/index.html')
        instances = res.context['instances_table'].data

        self.assertItemsEqual(instances, self.servers.list())

    @test.create_stubs({api: ('flavor_list', 'server_list', 'flavor_get',)})
    def test_index_flavor_get_exception(self):
        servers = self.servers.list()
        flavors = self.flavors.list()
        max_id = max([int(flavor.id) for flavor in flavors])
        for server in servers:
            max_id += 1
            server.flavor["id"] = max_id

        api.server_list(IsA(http.HttpRequest)).AndReturn(servers)
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(flavors)
        for server in servers:
            api.flavor_get(IsA(http.HttpRequest), server.flavor["id"]). \
                                AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:instances:index'))

        instances = res.context['instances_table'].data

        self.assertTemplateUsed(res, 'project/instances/index.html')
        self.assertMessageCount(res, error=len(servers))
        self.assertItemsEqual(instances, self.servers.list())

    @test.create_stubs({api: ('server_list',
                              'flavor_list',
                              'server_delete',)})
    def test_terminate_instance(self):
        server = self.servers.first()

        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.server_delete(IsA(http.HttpRequest), server.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__terminate__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_list',
                              'flavor_list',
                              'server_delete',)})
    def test_terminate_instance_exception(self):
        server = self.servers.first()

        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.server_delete(IsA(http.HttpRequest), server.id) \
                          .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__terminate__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_pause',
                              'server_list',
                              'flavor_list',)})
    def test_pause_instance(self):
        server = self.servers.first()

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_pause(IsA(http.HttpRequest), server.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_pause',
                              'server_list',
                              'flavor_list',)})
    def test_pause_instance_exception(self):
        server = self.servers.first()

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_pause(IsA(http.HttpRequest), server.id) \
                        .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_unpause',
                              'server_list',
                              'flavor_list',)})
    def test_unpause_instance(self):
        server = self.servers.first()
        server.status = "PAUSED"

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_unpause(IsA(http.HttpRequest), server.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_unpause',
                              'server_list',
                              'flavor_list',)})
    def test_unpause_instance_exception(self):
        server = self.servers.first()
        server.status = "PAUSED"

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_unpause(IsA(http.HttpRequest), server.id) \
                          .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_reboot',
                              'server_list',
                              'flavor_list',)})
    def test_reboot_instance(self):
        server = self.servers.first()

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_reboot(IsA(http.HttpRequest), server.id)

        self.mox.ReplayAll()

        formData = {'action': 'instances__reboot__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_reboot',
                              'server_list',
                              'flavor_list',)})
    def test_reboot_instance_exception(self):
        server = self.servers.first()

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_reboot(IsA(http.HttpRequest), server.id) \
                        .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__reboot__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_suspend',
                              'server_list',
                              'flavor_list',)})
    def test_suspend_instance(self):
        server = self.servers.first()

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_suspend(IsA(http.HttpRequest), unicode(server.id))

        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_suspend',
                              'server_list',
                              'flavor_list',)})
    def test_suspend_instance_exception(self):
        server = self.servers.first()

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_suspend(IsA(http.HttpRequest),
                          unicode(server.id)).AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_resume',
                              'server_list',
                              'flavor_list',)})
    def test_resume_instance(self):
        server = self.servers.first()
        server.status = "SUSPENDED"

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_resume(IsA(http.HttpRequest), unicode(server.id))

        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_resume',
                              'server_list',
                              'flavor_list',)})
    def test_resume_instance_exception(self):
        server = self.servers.first()
        server.status = "SUSPENDED"

        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_resume(IsA(http.HttpRequest),
                          unicode(server.id)).AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ("server_get",
                              "instance_volumes_list",
                              "flavor_get",
                              "server_security_groups")})
    def test_instance_details_volumes(self):
        server = self.servers.first()
        volumes = [self.volumes.list()[1]]

        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.instance_volumes_list(IsA(http.HttpRequest),
                                  server.id).AndReturn(volumes)
        api.flavor_get(IsA(http.HttpRequest),
                       server.flavor['id']).AndReturn(self.flavors.first())
        api.server_security_groups(IsA(http.HttpRequest),
                       server.id).AndReturn(self.security_groups.first())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:detail',
                      args=[server.id])
        res = self.client.get(url)

        self.assertItemsEqual(res.context['instance'].volumes, volumes)

    @test.create_stubs({api: ("server_get",
                              "instance_volumes_list",
                              "flavor_get",
                              "server_security_groups")})
    def test_instance_details_volume_sorting(self):
        server = self.servers.first()
        volumes = self.volumes.list()[1:3]

        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.instance_volumes_list(IsA(http.HttpRequest),
                                  server.id).AndReturn(volumes)
        api.flavor_get(IsA(http.HttpRequest),
                       server.flavor['id']).AndReturn(self.flavors.first())
        api.server_security_groups(IsA(http.HttpRequest),
                       server.id).AndReturn(self.security_groups.first())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:detail',
                      args=[server.id])
        res = self.client.get(url)

        self.assertItemsEqual(res.context['instance'].volumes, volumes)
        self.assertEquals(res.context['instance'].volumes[0].device,
                          "/dev/hda")
        self.assertEquals(res.context['instance'].volumes[1].device,
                          "/dev/hdk")

    @test.create_stubs({api: ("server_get",
                              "instance_volumes_list",
                              "flavor_get",
                              "server_security_groups",)})
    def test_instance_details_metadata(self):
        server = self.servers.first()

        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.instance_volumes_list(IsA(http.HttpRequest),
                                  server.id).AndReturn([])
        api.flavor_get(IsA(http.HttpRequest),
                       server.flavor['id']).AndReturn(self.flavors.first())
        api.server_security_groups(IsA(http.HttpRequest),
                       server.id).AndReturn(self.security_groups.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:detail',
                      args=[server.id])
        tg = InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("overview").get_id())
        res = self.client.get(url + qs)

        self.assertContains(res, "<dd>keyName</dd>", 1)
        self.assertContains(res, "<dt>someMetaLabel</dt>", 1)
        self.assertContains(res, "<dd>someMetaData</dd>", 1)
        self.assertContains(res, "<dt>some&lt;b&gt;html&lt;/b&gt;label</dt>",
                            1)
        self.assertContains(res, "<dd>&lt;!--</dd>", 1)
        self.assertContains(res, "<dt>empty</dt>", 1)
        self.assertContains(res, "<dd><em>N/A</em></dd>", 1)

    @test.create_stubs({api: ('server_console_output',)})
    def test_instance_log(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = 'output'

        api.server_console_output(IsA(http.HttpRequest),
                                  server.id, tail_length=None) \
                                  .AndReturn(CONSOLE_OUTPUT)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:console',
                      args=[server.id])
        tg = InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("log").get_id())
        res = self.client.get(url + qs)

        self.assertNoMessages()
        self.assertIsInstance(res, http.HttpResponse)
        self.assertContains(res, CONSOLE_OUTPUT)

    @test.create_stubs({api: ('server_console_output',)})
    def test_instance_log_exception(self):
        server = self.servers.first()

        api.server_console_output(IsA(http.HttpRequest),
                                  server.id, tail_length=None) \
                                .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:console',
                      args=[server.id])
        tg = InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("log").get_id())
        res = self.client.get(url + qs)

        self.assertContains(res, "Unable to get log for")

    def test_instance_vnc(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/vncserver'

        console_mock = self.mox.CreateMock(api.VNCConsole)
        console_mock.url = CONSOLE_OUTPUT

        self.mox.StubOutWithMock(api, 'server_vnc_console')
        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.server_vnc_console(IgnoreArg(), server.id).AndReturn(console_mock)
        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:vnc',
                      args=[server.id])
        res = self.client.get(url)
        redirect = CONSOLE_OUTPUT + '&title=%s(1)' % server.name
        self.assertRedirectsNoFollow(res, redirect)

    @test.create_stubs({api: ('server_vnc_console',)})
    def test_instance_vnc_exception(self):
        server = self.servers.first()

        api.server_vnc_console(IsA(http.HttpRequest), server.id) \
                        .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:vnc',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_get',
                              'snapshot_create',
                              'snapshot_list_detailed',
                              'image_list_detailed',
                              'volume_snapshot_list',
                              'server_list',
                              'flavor_list',
                              'server_delete',)})
    def test_create_instance_snapshot(self):
        server = self.servers.first()

        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.snapshot_create(IsA(http.HttpRequest),
                            server.id,
                            "snapshot1").AndReturn(self.snapshots.first())

        api.snapshot_list_detailed(IsA(http.HttpRequest),
                                   marker=None).AndReturn([[], False])
        api.image_list_detailed(IsA(http.HttpRequest),
                                marker=None).AndReturn([[], False])
        api.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])

        self.mox.ReplayAll()

        formData = {'instance_id': server.id,
                    'method': 'CreateSnapshot',
                    'name': 'snapshot1'}
        url = reverse('horizon:project:images_and_snapshots:snapshots:create',
                      args=[server.id])
        redir_url = reverse('horizon:project:images_and_snapshots:index')
        res = self.client.post(url, formData)
        self.assertRedirects(res, redir_url)

    @test.create_stubs({api: ('server_get',)})
    def test_instance_update_get(self):
        server = self.servers.first()

        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:update', args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/instances/update.html')

    @test.create_stubs({api: ('server_get',)})
    def test_instance_update_get_server_get_exception(self):
        server = self.servers.first()

        api.server_get(IsA(http.HttpRequest), server.id) \
                        .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:update',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_get', 'server_update')})
    def test_instance_update_post(self):
        server = self.servers.first()

        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.server_update(IsA(http.HttpRequest),
                          server.id,
                          server.name).AndReturn(server)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateInstance',
                    'instance': server.id,
                    'name': server.name,
                    'tenant_id': self.tenant.id}
        url = reverse('horizon:project:instances:update',
                      args=[server.id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ('server_get', 'server_update')})
    def test_instance_update_post_api_exception(self):
        server = self.servers.first()

        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.server_update(IsA(http.HttpRequest), server.id, server.name) \
                          .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateInstance',
                    'instance': server.id,
                    'name': server.name,
                    'tenant_id': self.tenant.id}
        url = reverse('horizon:project:instances:update',
                      args=[server.id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('flavor_list',
                                   'keypair_list',
                                   'security_group_list',),
                        cinder: ('volume_snapshot_list',
                                 'volume_list',),
                        quotas: ('tenant_quota_usages',),
                        api.quantum: ('network_list',),
                        api.glance: ('image_list_detailed',)})
    def test_launch_instance_get(self):
        quota_usages = self.quota_usages.first()
        image = self.images.first()

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
        api.quantum.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
                .AndReturn(quota_usages)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
                .AndReturn(self.keypairs.list())
        api.nova.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:launch')
        params = urlencode({"source_type": "image_id",
                            "source_id": image.id})
        res = self.client.get("%s?%s" % (url, params))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res,
                        'project/instances/launch.html')
        self.assertEqual(res.context['workflow'].name, LaunchInstance.name)
        step = workflow.get_step("setinstancedetailsaction")
        self.assertEqual(step.action.initial['image_id'], image.id)
        self.assertQuerysetEqual(workflow.steps,
                            ['<SetInstanceDetails: setinstancedetailsaction>',
                             '<SetAccessControls: setaccesscontrolsaction>',
                             '<SetNetwork: setnetworkaction>',
                             '<VolumeOptions: volumeoptionsaction>',
                             '<PostCreationStep: customizeaction>'])

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.quantum: ('network_list',),
                        quotas: ('tenant_quota_usages',),
                        api.nova: ('flavor_list',
                                   'keypair_list',
                                   'security_group_list',
                                   'server_create',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',)})
    def test_launch_instance_post(self):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        customization_script = 'user data'
        device_name = u'vda'
        volume_choice = "%s:vol" % volume.id
        block_device_mapping = {device_name: u"%s::0" % volume_choice}
        nics = [{"net-id": self.networks.first().id, "v4-fixed-ip": ''}]

        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
                .AndReturn(self.keypairs.list())
        api.nova.security_group_list(IsA(http.HttpRequest)) \
                .AndReturn(self.security_groups.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])
        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               image.id,
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [sec_group.name],
                               block_device_mapping,
                               nics=nics,
                               instance_count=IsA(int))

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
                     'volume_type': 'volume_id',
                     'volume_id': volume_choice,
                     'device_name': device_name,
                     'network': self.networks.first().id,
                     'count': 1}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.quantum: ('network_list',),
                        quotas: ('tenant_quota_usages',),
                        api.nova: ('flavor_list',
                                   'keypair_list',
                                   'security_group_list',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',)})
    def test_launch_instance_post_no_images_available(self):
        flavor = self.flavors.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        customization_script = 'user data'
        device_name = u'vda'
        volume_choice = "%s:vol" % volume.id

        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn({})
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                .AndReturn([[], False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                .AndReturn([[], False])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
                .AndReturn(self.keypairs.list())
        api.nova.security_group_list(IsA(http.HttpRequest)) \
                .AndReturn(self.security_groups.list())
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])

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
                     'volume_type': 'volume_id',
                     'volume_id': volume_choice,
                     'device_name': device_name,
                     'count': 1}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertFormErrors(res, 1, 'There are no image sources available; '
                                      'you must first create an image before '
                                      'attempting to launch an instance.')
        self.assertTemplateUsed(res,
                        'project/instances/launch.html')

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.quantum: ('network_list',),
                        quotas: ('tenant_quota_usages',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',),
                        api.nova: ('flavor_list',
                                   'keypair_list',
                                   'security_group_list',)})
    def test_launch_flavorlist_error(self):
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
        api.quantum.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
                .AndReturn(self.quota_usages.first())
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndRaise(self.exceptions.nova)
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndRaise(self.exceptions.nova)
        api.nova.keypair_list(IsA(http.HttpRequest)) \
                .AndReturn(self.keypairs.list())
        api.nova.security_group_list(IsA(http.HttpRequest)) \
                .AndReturn(self.security_groups.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:instances:launch')
        res = self.client.get(url)

        self.assertTemplateUsed(res,
                        'project/instances/launch.html')

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.quantum: ('network_list',),
                        api.nova: ('flavor_list',
                                   'keypair_list',
                                   'security_group_list',
                                   'server_create',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',)})
    def test_launch_form_keystone_exception(self):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        sec_group = self.security_groups.first()
        customization_script = 'userData'
        nics = [{"net-id": self.networks.first().id, "v4-fixed-ip": ''}]

        cinder.volume_snapshot_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.nova.keypair_list(IgnoreArg()).AndReturn(self.keypairs.list())
        api.nova.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        cinder.volume_list(IgnoreArg()).AndReturn(self.volumes.list())
        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               image.id,
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [sec_group.name],
                               None,
                               nics=nics,
                               instance_count=IsA(int)) \
                      .AndRaise(self.exceptions.keystone)

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
                     'volume_type': '',
                     'network': self.networks.first().id,
                     'count': 1}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.quantum: ('network_list',),
                        quotas: ('tenant_quota_usages',),
                        api.nova: ('flavor_list',
                                   'keypair_list',
                                   'security_group_list',),
                        cinder: ('volume_list',
                                 'volume_snapshot_list',)})
    def test_launch_form_instance_count_error(self):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        volume = self.volumes.first()
        sec_group = self.security_groups.first()
        customization_script = 'user data'
        device_name = u'vda'
        volume_choice = "%s:vol" % volume.id

        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
                .AndReturn(self.keypairs.list())
        api.nova.security_group_list(IsA(http.HttpRequest)) \
                .AndReturn(self.security_groups.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 tenant_id=self.tenant.id,
                                 shared=False) \
                .AndReturn(self.networks.list()[:1])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 shared=True) \
                .AndReturn(self.networks.list()[1:])
        cinder.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])

        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)) \
                .AndReturn(self.quota_usages.first())

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
                     'volume_type': 'volume_id',
                     'volume_id': volume_choice,
                     'device_name': device_name,
                     'count': 0}
        url = reverse('horizon:project:instances:launch')
        res = self.client.post(url, form_data)

        self.assertContains(res, "greater than or equal to 1")
