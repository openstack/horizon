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
from django.utils.http import urlencode

from mox3.mox import IsA  # noqa
import six

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.access_and_security \
    .floating_ips import tables
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

from horizon.workflows import views


INDEX_URL = reverse('horizon:project:access_and_security:index')
NAMESPACE = "horizon:project:access_and_security:floating_ips"


class FloatingIpViewTests(test.TestCase):
    @test.create_stubs({api.network: ('floating_ip_target_list',
                                      'tenant_floating_ip_list',)})
    def test_associate(self):
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

    @test.create_stubs({api.network: ('floating_ip_target_list',
                                      'floating_ip_target_get_by_instance',
                                      'tenant_floating_ip_list',)})
    def test_associate_with_instance_id(self):
        api.network.floating_ip_target_list(IsA(http.HttpRequest)) \
            .AndReturn(self.servers.list())
        api.network.floating_ip_target_get_by_instance(
            IsA(http.HttpRequest), 'TEST-ID', self.servers.list()) \
            .AndReturn('TEST-ID')
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        base_url = reverse('%s:associate' % NAMESPACE)
        params = urlencode({'instance_id': 'TEST-ID'})
        url = '?'.join([base_url, params])
        res = self.client.get(url)
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        workflow = res.context['workflow']
        choices = dict(workflow.steps[0].action.fields['ip_id'].choices)
        # Verify that our "associated" floating IP isn't in the choices list.
        self.assertTrue(self.floating_ips.first() not in choices)

    @test.create_stubs({api.network: ('floating_ip_target_list',
                                      'tenant_floating_ip_list',)})
    def test_associate_with_port_id(self):
        targets = [api.nova.FloatingIpTarget(s) for s in self.servers.list()]
        targets[0].port_id = '101'
        api.network.floating_ip_target_list(IsA(http.HttpRequest)) \
            .AndReturn(targets)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        base_url = reverse('%s:associate' % NAMESPACE)
        params = urlencode({'port_id': '101'})
        url = '?'.join([base_url, params])
        res = self.client.get(url)
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        workflow = res.context['workflow']
        choices = dict(workflow.steps[0].action.fields['ip_id'].choices)
        # Verify that our "associated" floating IP isn't in the choices list.
        self.assertTrue(self.floating_ips.first() not in choices)

    @test.create_stubs({api.network: ('floating_ip_associate',
                                      'floating_ip_target_list',
                                      'tenant_floating_ip_list',)})
    def test_associate_post(self):
        floating_ip = self.floating_ips.list()[1]
        server = self.servers.first()

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

    @test.create_stubs({api.network: ('floating_ip_associate',
                                      'floating_ip_target_list',
                                      'tenant_floating_ip_list',)})
    def test_associate_post_with_redirect(self):
        floating_ip = self.floating_ips.list()[1]
        server = self.servers.first()

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

    @test.create_stubs({api.network: ('floating_ip_associate',
                                      'floating_ip_target_list',
                                      'tenant_floating_ip_list',)})
    def test_associate_post_with_exception(self):
        floating_ip = self.floating_ips.list()[1]
        server = self.servers.first()

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

    @test.create_stubs({api.nova: ('server_list',),
                        api.network: ('floating_ip_disassociate',
                                      'floating_ip_supported',
                                      'tenant_floating_ip_get',
                                      'tenant_floating_ip_list',)})
    def test_disassociate_post(self):
        floating_ip = self.floating_ips.first()

        api.nova.server_list(IsA(http.HttpRequest)) \
            .AndReturn([self.servers.list(), False])
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        api.network.floating_ip_disassociate(IsA(http.HttpRequest),
                                             floating_ip.id)
        self.mox.ReplayAll()

        action = "floating_ips__disassociate__%s" % floating_ip.id
        res = self.client.post(INDEX_URL, {"action": action})
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_list',),
                        api.network: ('floating_ip_disassociate',
                                      'floating_ip_supported',
                                      'tenant_floating_ip_get',
                                      'tenant_floating_ip_list',)})
    def test_disassociate_post_with_exception(self):
        floating_ip = self.floating_ips.first()

        api.nova.server_list(IsA(http.HttpRequest)) \
            .AndReturn([self.servers.list(), False])
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())

        api.network.floating_ip_disassociate(IsA(http.HttpRequest),
                                             floating_ip.id) \
            .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        action = "floating_ips__disassociate__%s" % floating_ip.id
        res = self.client.post(INDEX_URL, {"action": action})
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.network: ('floating_ip_supported',
                                      'tenant_floating_ip_list',
                                      'security_group_list',
                                      'floating_ip_pools_list',),
                        api.nova: ('keypair_list',
                                   'server_list',),
                        quotas: ('tenant_quota_usages',),
                        api.base: ('is_service_enabled',)})
    def test_allocate_button_disabled_when_quota_exceeded(self):
        keypairs = self.keypairs.list()
        floating_ips = self.floating_ips.list()
        floating_pools = self.pools.list()
        quota_data = self.quota_usages.first()
        quota_data['floating_ips']['available'] = 0
        sec_groups = self.security_groups.list()

        api.network.floating_ip_supported(
            IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(
            IsA(http.HttpRequest)) \
            .AndReturn(floating_ips)
        api.network.security_group_list(
            IsA(http.HttpRequest)).MultipleTimes()\
            .AndReturn(sec_groups)
        api.network.floating_ip_pools_list(
            IsA(http.HttpRequest)) \
            .AndReturn(floating_pools)
        api.nova.keypair_list(
            IsA(http.HttpRequest)) \
            .AndReturn(keypairs)
        api.nova.server_list(
            IsA(http.HttpRequest)) \
            .AndReturn([self.servers.list(), False])
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)).MultipleTimes() \
            .AndReturn(quota_data)

        api.base.is_service_enabled(
            IsA(http.HttpRequest),
            'network').MultipleTimes() \
            .AndReturn(True)
        api.base.is_service_enabled(
            IsA(http.HttpRequest),
            'ec2').MultipleTimes() \
            .AndReturn(False)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL +
                              "?tab=access_security_tabs__floating_ips_tab")

        allocate_link = tables.AllocateIP()
        url = allocate_link.get_link_url()
        classes = (list(allocate_link.get_default_classes())
                   + list(allocate_link.classes))
        link_name = "%s (%s)" % (six.text_type(allocate_link.verbose_name),
                                 "Quota exceeded")
        expected_string = ("<a href='%s' title='%s' class='%s disabled' "
                           "id='floating_ips__action_allocate'>"
                           "<span class='fa fa-link'>"
                           "</span>%s</a>"
                           % (url, link_name, " ".join(classes), link_name))
        self.assertContains(res, expected_string, html=True,
                            msg_prefix="The create button is not disabled")


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
                        api.network: ('floating_ip_pools_list',
                                      'floating_ip_supported',
                                      'security_group_list',
                                      'tenant_floating_ip_list'),
                        api.neutron: ('is_extension_supported',
                                      'tenant_quota_get',
                                      'network_list',
                                      'router_list',
                                      'subnet_list'),
                        api.base: ('is_service_enabled',)})
    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_correct_quotas_displayed(self):
        servers = [s for s in self.servers.list()
                   if s.tenant_id == self.request.user.tenant_id]

        api.base.is_service_enabled(IsA(http.HttpRequest), 'volume') \
            .AndReturn(False)
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .MultipleTimes().AndReturn(True)
        api.nova.tenant_quota_get(IsA(http.HttpRequest), '1') \
            .AndReturn(self.quotas.first())
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        search_opts = {'tenant_id': self.request.user.tenant_id}
        api.nova.server_list(IsA(http.HttpRequest), search_opts=search_opts,
                             all_tenants=True) \
            .AndReturn([servers, False])
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'security-group').AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'quotas') \
            .AndReturn(True)
        api.neutron.tenant_quota_get(IsA(http.HttpRequest), self.tenant.id) \
            .AndReturn(self.neutron_quotas.first())
        api.neutron.router_list(IsA(http.HttpRequest)) \
            .AndReturn(self.routers.list())
        api.neutron.subnet_list(IsA(http.HttpRequest)) \
            .AndReturn(self.subnets.list())
        api.neutron.network_list(IsA(http.HttpRequest), shared=False) \
            .AndReturn(self.networks.list())
        api.network.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(self.floating_ips.list())
        api.network.floating_ip_pools_list(IsA(http.HttpRequest)) \
            .AndReturn(self.pools.list())
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(self.security_groups.list())
        self.mox.ReplayAll()

        url = reverse('%s:allocate' % NAMESPACE)
        res = self.client.get(url)
        self.assertEqual(res.context['usages']['floating_ips']['quota'],
                         self.neutron_quotas.first().get('floatingip').limit)
