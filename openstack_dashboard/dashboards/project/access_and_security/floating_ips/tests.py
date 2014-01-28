# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright (c) 2012 X.commerce, a business unit of eBay Inc.
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
from django.test.utils import override_settings

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from horizon.workflows import views


INDEX_URL = reverse('horizon:project:access_and_security:index')
NAMESPACE = "horizon:project:access_and_security:floating_ips"


class FloatingIpViewTests(test.TestCase):
    def test_associate(self):
        self.mox.StubOutWithMock(api.network, 'floating_ip_target_list')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        api.network.floating_ip_target_list(IsA(http.HttpRequest)) \
                .AndReturn(self.servers.list())
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.get(url)
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        workflow = res.context['workflow']
        choices = dict(workflow.steps[0].action.fields['ip_id'].choices)
        # Verify that our "associated" floating IP isn't in the choices list.
        self.assertTrue(self.floating_ips.first() not in choices)

    def test_associate_post(self):
        floating_ip = self.floating_ips.list()[1]
        server = self.servers.first()
        self.mox.StubOutWithMock(api.network, 'floating_ip_associate')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api.network, 'floating_ip_target_list')

        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        api.network.floating_ip_target_list(IsA(http.HttpRequest)) \
                .AndReturn(self.servers.list())
        api.network.floating_ip_associate(IsA(http.HttpRequest),
                                          floating_ip.id,
                                          server.id)
        self.mox.ReplayAll()

        form_data = {'instance_id': server.id,
                     'ip_id': floating_ip.id}
        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_associate_post_with_redirect(self):
        floating_ip = self.floating_ips.list()[1]
        server = self.servers.first()
        self.mox.StubOutWithMock(api.network, 'floating_ip_associate')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api.network, 'floating_ip_target_list')

        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        api.network.floating_ip_target_list(IsA(http.HttpRequest)) \
                .AndReturn(self.servers.list())
        api.network.floating_ip_associate(IsA(http.HttpRequest),
                                          floating_ip.id,
                                          server.id)
        self.mox.ReplayAll()

        form_data = {'instance_id': server.id,
                     'ip_id': floating_ip.id}
        url = reverse('%s:associate' % NAMESPACE)
        next = reverse("horizon:project:instances:index")
        res = self.client.post("%s?next=%s" % (url, next), form_data)
        self.assertRedirectsNoFollow(res, next)

    def test_associate_post_with_exception(self):
        floating_ip = self.floating_ips.list()[1]
        server = self.servers.first()
        self.mox.StubOutWithMock(api.network, 'floating_ip_associate')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api.network, 'floating_ip_target_list')

        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        api.network.floating_ip_target_list(IsA(http.HttpRequest)) \
                .AndReturn(self.servers.list())
        api.network.floating_ip_associate(IsA(http.HttpRequest),
                                          floating_ip.id,
                                          server.id) \
                .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        form_data = {'instance_id': server.id,
                     'ip_id': floating_ip.id}
        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_disassociate_post(self):
        floating_ip = self.floating_ips.first()
        server = self.servers.first()
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_get')
        self.mox.StubOutWithMock(api.network, 'floating_ip_disassociate')
        self.mox.StubOutWithMock(api.nova, 'server_list')

        api.nova.server_list(IsA(http.HttpRequest)) \
                            .AndReturn([self.servers.list(), False])
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                                    .AndReturn(self.floating_ips.list())
        api.network.floating_ip_disassociate(IsA(http.HttpRequest),
                                             floating_ip.id,
                                             server.id)
        self.mox.ReplayAll()

        action = "floating_ips__disassociate__%s" % floating_ip.id
        res = self.client.post(INDEX_URL, {"action": action})
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_disassociate_post_with_exception(self):
        floating_ip = self.floating_ips.first()
        server = self.servers.first()
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_get')
        self.mox.StubOutWithMock(api.network, 'floating_ip_disassociate')
        self.mox.StubOutWithMock(api.nova, 'server_list')

        api.nova.server_list(IsA(http.HttpRequest)) \
                        .AndReturn([self.servers.list(), False])
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())

        api.network.floating_ip_disassociate(IsA(http.HttpRequest),
                                             floating_ip.id,
                                             server.id) \
            .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        action = "floating_ips__disassociate__%s" % floating_ip.id
        res = self.client.post(INDEX_URL, {"action": action})
        self.assertRedirectsNoFollow(res, INDEX_URL)


class FloatingIpNeutronViewTests(FloatingIpViewTests):
    def setUp(self):
        super(FloatingIpViewTests, self).setUp()
        self._floating_ips_orig = self.floating_ips
        self.floating_ips = self.floating_ips_uuid

    def tearDown(self):
        self.floating_ips = self._floating_ips_orig
        super(FloatingIpViewTests, self).tearDown()

    @test.create_stubs({api.nova: ('tenant_quota_get', 'flavor_list',
                                   'server_list'),
                        api.cinder: ('tenant_quota_get', 'volume_list',
                                     'volume_snapshot_list',),
                        api.network: ('floating_ip_pools_list',
                                      'tenant_floating_ip_list'),
                        api.neutron: ('is_extension_supported',
                                      'tenant_quota_get')})
    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_correct_quotas_displayed(self):
        servers = [s for s in self.servers.list()
                   if s.tenant_id == self.request.user.tenant_id]

        api.nova.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.quotas.first())
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.server_list(IsA(http.HttpRequest)) \
            .AndReturn([servers, False])
        api.cinder.volume_list(IsA(http.HttpRequest)) \
            .AndReturn(self.volumes.list())
        api.cinder.volume_snapshot_list(IsA(http.HttpRequest)) \
            .AndReturn(self.snapshots.list())
        api.cinder.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.cinder_quotas.first())
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'security-group').AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'quotas') \
            .AndReturn(True)
        api.neutron.tenant_quota_get(IsA(http.HttpRequest), self.tenant.id) \
            .AndReturn(self.neutron_quotas.first())
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(self.floating_ips.list())
        api.network.floating_ip_pools_list(IsA(http.HttpRequest)) \
            .AndReturn(self.pools.list())
        self.mox.ReplayAll()

        url = reverse('%s:allocate' % NAMESPACE)
        res = self.client.get(url)
        self.assertEqual(res.context['usages']['floating_ips']['quota'],
                         self.neutron_quotas.first().get('floatingip').limit)
