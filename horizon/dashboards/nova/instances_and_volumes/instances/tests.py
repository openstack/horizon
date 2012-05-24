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
from mox import IsA, IgnoreArg
from copy import deepcopy

from horizon import api
from horizon import test
from .tabs import InstanceDetailTabs
from .workflows import LaunchInstance


INDEX_URL = reverse('horizon:nova:instances_and_volumes:index')


class InstanceViewTests(test.TestCase):
    def setUp(self):
        super(InstanceViewTests, self).setUp()
        self.now = self.override_times()

    def tearDown(self):
        super(InstanceViewTests, self).tearDown()
        self.reset_times()

    def test_terminate_instance(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'server_delete')
        self.mox.StubOutWithMock(api, 'volume_list')
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.server_delete(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        formData = {'action': 'instances__terminate__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_terminate_instance_exception(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'server_delete')
        self.mox.StubOutWithMock(api, 'volume_list')
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.server_delete(IsA(http.HttpRequest), server.id) \
                          .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        formData = {'action': 'instances__terminate__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_pause_instance(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_pause')
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_pause(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_pause_instance_exception(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'volume_list')
        self.mox.StubOutWithMock(api, 'server_pause')
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_pause(IsA(http.HttpRequest), server.id) \
                        .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_unpause_instance(self):
        server = self.servers.first()
        server.status = "PAUSED"
        self.mox.StubOutWithMock(api, 'volume_list')
        self.mox.StubOutWithMock(api, 'server_unpause')
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_unpause(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_unpause_instance_exception(self):
        server = self.servers.first()
        server.status = "PAUSED"
        self.mox.StubOutWithMock(api, 'volume_list')
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'server_unpause')
        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_unpause(IsA(http.HttpRequest), server.id) \
                          .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_reboot_instance(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_reboot')
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_reboot(IsA(http.HttpRequest), server.id)
        self.mox.ReplayAll()

        formData = {'action': 'instances__reboot__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_reboot_instance_exception(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_reboot')
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_reboot(IsA(http.HttpRequest), server.id) \
                        .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        formData = {'action': 'instances__reboot__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_suspend_instance(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_suspend')
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_suspend(IsA(http.HttpRequest), unicode(server.id))
        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_suspend_instance_exception(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_suspend')
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_suspend(IsA(http.HttpRequest),
                          unicode(server.id)).AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_resume_instance(self):
        server = self.servers.first()
        server.status = "SUSPENDED"
        self.mox.StubOutWithMock(api, 'server_resume')
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_resume(IsA(http.HttpRequest), unicode(server.id))
        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_resume_instance_exception(self):
        server = self.servers.first()
        server.status = "SUSPENDED"
        self.mox.StubOutWithMock(api, 'server_resume')
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.server_resume(IsA(http.HttpRequest),
                          unicode(server.id)).AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api: ("server_get", "volume_instance_list",
                              "flavor_get", "server_security_groups")})
    def test_instance_details_volumes(self):
        server = self.servers.first()
        volumes = deepcopy(self.volumes.list())
        volumes[0].device = "/dev/hdk"
        second_vol = deepcopy(volumes[0])
        second_vol.id = 2
        second_vol.device = "/dev/hdb"
        volumes.append(second_vol)

        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.volume_instance_list(IsA(http.HttpRequest),
                               server.id).AndReturn(volumes)
        api.flavor_get(IsA(http.HttpRequest),
                       server.flavor['id']).AndReturn(self.flavors.first())
        api.server_security_groups(IsA(http.HttpRequest),
                       server.id).AndReturn(self.security_groups.first())

        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:instances:detail',
                      args=[server.id])
        res = self.client.get(url)
        self.assertItemsEqual(res.context['instance'].volumes, volumes)
        # Test device ordering
        self.assertEquals(res.context['instance'].volumes[0].device,
                          "/dev/hdb")
        self.assertEquals(res.context['instance'].volumes[1].device,
                          "/dev/hdk")

    def test_instance_log(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = 'output'

        self.mox.StubOutWithMock(api, 'server_console_output')
        api.server_console_output(IsA(http.HttpRequest),
                                  server.id, tail_length=None) \
                                  .AndReturn(CONSOLE_OUTPUT)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:instances:console',
                      args=[server.id])
        tg = InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("log").get_id())
        res = self.client.get(url + qs)
        self.assertNoMessages()
        self.assertIsInstance(res, http.HttpResponse)
        self.assertContains(res, CONSOLE_OUTPUT)

    def test_instance_log_exception(self):
        server = self.servers.first()

        self.mox.StubOutWithMock(api, 'server_console_output')
        api.server_console_output(IsA(http.HttpRequest),
                                  server.id, tail_length=None) \
                                .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:instances:console',
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

        url = reverse('horizon:nova:instances_and_volumes:instances:vnc',
                      args=[server.id])
        res = self.client.get(url)
        redirect = CONSOLE_OUTPUT + '&title=%s(1)' % server.name
        self.assertRedirectsNoFollow(res, redirect)

    def test_instance_vnc_exception(self):
        server = self.servers.first()

        self.mox.StubOutWithMock(api, 'server_vnc_console')
        api.server_vnc_console(IsA(http.HttpRequest), server.id) \
                        .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:instances:vnc',
                      args=[server.id])
        res = self.client.get(url)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_create_instance_snapshot(self):
        server = self.servers.first()
        snapshot_server = deepcopy(server)
        setattr(snapshot_server, 'OS-EXT-STS:task_state',
                "IMAGE_SNAPSHOT")
        self.mox.StubOutWithMock(api, 'server_get')
        self.mox.StubOutWithMock(api, 'snapshot_create')
        self.mox.StubOutWithMock(api, 'snapshot_list_detailed')
        self.mox.StubOutWithMock(api, 'image_list_detailed')
        self.mox.StubOutWithMock(api, 'volume_snapshot_list')
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'server_delete')
        self.mox.StubOutWithMock(api, 'volume_list')
        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.snapshot_create(IsA(http.HttpRequest),
                            server.id,
                            "snapshot1")
        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.snapshot_list_detailed(IsA(http.HttpRequest),
                                marker=None).AndReturn([[], False])
        api.image_list_detailed(IsA(http.HttpRequest),
                                marker=None).AndReturn([[], False])
        api.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])

        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn([snapshot_server])
        api.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        self.mox.ReplayAll()

        formData = {'instance_id': server.id,
                    'method': 'CreateSnapshot',
                    'tenant_id': server.tenant_id,
                    'name': 'snapshot1'}
        url = reverse('horizon:nova:images_and_snapshots:snapshots:create',
                      args=[server.id])
        redir_url = reverse('horizon:nova:images_and_snapshots:index')
        res = self.client.post(url, formData)
        self.assertRedirects(res, redir_url)
        res = self.client.get(INDEX_URL)
        self.assertContains(res, "<td  class=\"status_unknown\">"
                                 "Snapshotting</td>", 1)

    def test_instance_update_get(self):
        server = self.servers.first()

        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:instances:update',
                      args=[server.id])
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                'nova/instances_and_volumes/instances/update.html')

    def test_instance_update_get_server_get_exception(self):
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_get')
        api.server_get(IsA(http.HttpRequest), server.id) \
                        .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:instances:update',
                      args=[server.id])
        res = self.client.get(url)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_update_post(self):
        server = self.servers.first()

        self.mox.StubOutWithMock(api, 'server_get')
        self.mox.StubOutWithMock(api, 'server_update')
        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.server_update(IsA(http.HttpRequest), server.id, server.name)
        self.mox.ReplayAll()

        formData = {'method': 'UpdateInstance',
                    'instance': server.id,
                    'name': server.name,
                    'tenant_id': self.tenant.id}
        url = reverse('horizon:nova:instances_and_volumes:instances:update',
                      args=[server.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_instance_update_post_api_exception(self):
        server = self.servers.first()

        self.mox.StubOutWithMock(api, 'server_get')
        self.mox.StubOutWithMock(api, 'server_update')
        api.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        api.server_update(IsA(http.HttpRequest), server.id, server.name) \
                          .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        formData = {'method': 'UpdateInstance',
                    'instance': server.id,
                    'name': server.name,
                    'tenant_id': self.tenant.id}
        url = reverse('horizon:nova:instances_and_volumes:instances:update',
                      args=[server.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_launch_get(self):
        quota_usages = self.quota_usages.first()

        self.mox.StubOutWithMock(api.glance, 'image_list_detailed')
        self.mox.StubOutWithMock(api.nova, 'tenant_quota_usages')
        # Two flavor_list calls, however, flavor_list is now memoized.
        self.mox.StubOutWithMock(api.nova, 'flavor_list')
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api.nova, 'security_group_list')
        self.mox.StubOutWithMock(api.nova, 'volume_snapshot_list')
        self.mox.StubOutWithMock(api.nova, 'volume_list')

        api.nova.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        api.nova.volume_snapshot_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.volumes.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id}) \
                  .AndReturn([[], False])
        api.nova.tenant_quota_usages(IsA(http.HttpRequest)) \
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

        url = reverse('horizon:nova:instances_and_volumes:instances:launch')
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                        'nova/instances_and_volumes/instances/launch.html')
        workflow = res.context['workflow']
        self.assertEqual(workflow.name, LaunchInstance.name)
        self.assertQuerysetEqual(workflow.steps,
                            ['<SetInstanceDetails: setinstancedetailsaction>',
                             '<SetAccessControls: setaccesscontrolsaction>',
                             '<VolumeOptions: volumeoptionsaction>',
                             '<PostCreationStep: customizeaction>'])

    def test_launch_post(self):
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

        self.mox.StubOutWithMock(api.glance, 'image_list_detailed')
        self.mox.StubOutWithMock(api.nova, 'flavor_list')
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api.nova, 'security_group_list')
        self.mox.StubOutWithMock(api.nova, 'volume_list')
        self.mox.StubOutWithMock(api.nova, 'volume_snapshot_list')
        self.mox.StubOutWithMock(api.nova, 'tenant_quota_usages')
        self.mox.StubOutWithMock(api.nova, 'server_create')

        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
                .AndReturn(self.keypairs.list())
        api.nova.security_group_list(IsA(http.HttpRequest)) \
                .AndReturn(self.security_groups.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id}) \
                  .AndReturn([[], False])
        api.nova.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        api.nova.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])
        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               image.id,
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [sec_group.name],
                               block_device_mapping,
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
                     'count': 1}
        url = reverse('horizon:nova:instances_and_volumes:instances:launch')
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res,
                 reverse('horizon:nova:instances_and_volumes:index'))

    def test_launch_flavorlist_error(self):
        self.mox.StubOutWithMock(api.glance, 'image_list_detailed')
        self.mox.StubOutWithMock(api.nova, 'tenant_quota_usages')
        self.mox.StubOutWithMock(api.nova, 'flavor_list')
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api.nova, 'security_group_list')
        self.mox.StubOutWithMock(api.nova, 'volume_snapshot_list')
        self.mox.StubOutWithMock(api.nova, 'volume_list')

        api.nova.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        api.nova.volume_snapshot_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id}) \
                  .AndReturn([[], False])
        api.nova.tenant_quota_usages(IsA(http.HttpRequest)) \
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

        url = reverse('horizon:nova:instances_and_volumes:instances:launch')
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                        'nova/instances_and_volumes/instances/launch.html')

    def test_launch_form_keystone_exception(self):
        flavor = self.flavors.first()
        image = self.images.first()
        keypair = self.keypairs.first()
        server = self.servers.first()
        sec_group = self.security_groups.first()
        customization_script = 'userData'

        self.mox.StubOutWithMock(api.glance, 'image_list_detailed')
        self.mox.StubOutWithMock(api.nova, 'flavor_list')
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api.nova, 'security_group_list')
        self.mox.StubOutWithMock(api.nova, 'server_create')
        self.mox.StubOutWithMock(api.nova, 'volume_list')
        self.mox.StubOutWithMock(api.nova, 'volume_snapshot_list')

        api.nova.volume_snapshot_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.volumes.list())
        api.nova.flavor_list(IgnoreArg()).AndReturn(self.flavors.list())
        api.nova.keypair_list(IgnoreArg()).AndReturn(self.keypairs.list())
        api.nova.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id}) \
                  .AndReturn([[], False])
        api.nova.volume_list(IgnoreArg()).AndReturn(self.volumes.list())
        api.nova.server_create(IsA(http.HttpRequest),
                               server.name,
                               image.id,
                               flavor.id,
                               keypair.name,
                               customization_script,
                               [sec_group.name],
                               None,
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
                     'count': 1}
        url = reverse('horizon:nova:instances_and_volumes:instances:launch')
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

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

        self.mox.StubOutWithMock(api.glance, 'image_list_detailed')
        self.mox.StubOutWithMock(api.nova, 'flavor_list')
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api.nova, 'security_group_list')
        self.mox.StubOutWithMock(api.nova, 'volume_list')
        self.mox.StubOutWithMock(api.nova, 'volume_snapshot_list')
        self.mox.StubOutWithMock(api.nova, 'tenant_quota_usages')

        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
                .AndReturn(self.keypairs.list())
        api.nova.security_group_list(IsA(http.HttpRequest)) \
                .AndReturn(self.security_groups.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id}) \
                  .AndReturn([[], False])
        api.nova.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list())
        api.nova.volume_snapshot_list(IsA(http.HttpRequest)).AndReturn([])

        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(self.flavors.list())
        api.nova.tenant_quota_usages(IsA(http.HttpRequest)) \
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
        url = reverse('horizon:nova:instances_and_volumes:instances:launch')
        res = self.client.post(url, form_data)
        self.assertContains(res, "greater than or equal to 1")
