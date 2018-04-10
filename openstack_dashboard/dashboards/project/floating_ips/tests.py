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

from mox3.mox import IsA
import six

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

from horizon.workflows import views


INDEX_URL = reverse('horizon:project:floating_ips:index')
NAMESPACE = "horizon:project:floating_ips"


class FloatingIpViewTests(test.TestCase):

    @test.create_stubs({api.neutron: ('floating_ip_target_list',
                                      'tenant_floating_ip_list',)})
    def test_associate(self):
        api.neutron.floating_ip_target_list(IsA(http.HttpRequest)) \
            .AndReturn(self._get_fip_targets())
        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.get(url)
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        workflow = res.context['workflow']
        choices = dict(workflow.steps[0].action.fields['ip_id'].choices)
        # Verify that our "associated" floating IP isn't in the choices list.
        self.assertNotIn(self.floating_ips.first(), choices)

    @test.create_stubs({api.neutron: ('floating_ip_target_list',
                                      'floating_ip_target_get_by_instance',
                                      'tenant_floating_ip_list',)})
    def test_associate_with_instance_id(self):
        targets = self._get_fip_targets()
        target = targets[0]
        api.neutron.floating_ip_target_list(IsA(http.HttpRequest)) \
            .AndReturn(targets)
        api.neutron.floating_ip_target_get_by_instance(
            IsA(http.HttpRequest), target.instance_id, targets) \
            .AndReturn(target.id)
        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        base_url = reverse('%s:associate' % NAMESPACE)
        params = urlencode({'instance_id': target.instance_id})
        url = '?'.join([base_url, params])
        res = self.client.get(url)
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        workflow = res.context['workflow']
        choices = dict(workflow.steps[0].action.fields['ip_id'].choices)
        # Verify that our "associated" floating IP isn't in the choices list.
        self.assertNotIn(self.floating_ips.first(), choices)

    def _get_compute_ports(self):
        return [p for p in self.ports.list()
                if not p.device_owner.startswith('network:')]

    def _get_fip_targets(self):
        server_dict = dict((s.id, s.name) for s in self.servers.list())
        targets = []
        for p in self._get_compute_ports():
            for ip in p.fixed_ips:
                targets.append(api.neutron.FloatingIpTarget(
                    p, ip['ip_address'], server_dict[p.device_id]))
        return targets

    @staticmethod
    def _get_target_id(port):
        return '%s_%s' % (port.id, port.fixed_ips[0]['ip_address'])

    @test.create_stubs({api.neutron: ('floating_ip_target_list',
                                      'tenant_floating_ip_list',)})
    def test_associate_with_port_id(self):
        compute_port = self._get_compute_ports()[0]
        associated_fips = [fip.id for fip in self.floating_ips.list()
                           if fip.port_id]

        api.neutron.floating_ip_target_list(IsA(http.HttpRequest)) \
            .AndReturn(self._get_fip_targets())
        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        base_url = reverse('%s:associate' % NAMESPACE)
        params = urlencode({'port_id': compute_port.id})
        url = '?'.join([base_url, params])
        res = self.client.get(url)
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        workflow = res.context['workflow']
        choices = dict(workflow.steps[0].action.fields['ip_id'].choices)
        # Verify that our "associated" floating IP isn't in the choices list.
        self.assertFalse(set(associated_fips) & set(choices.keys()))

    @test.create_stubs({api.neutron: ('floating_ip_associate',
                                      'floating_ip_target_list',
                                      'tenant_floating_ip_list',)})
    def test_associate_post(self):
        floating_ip = [fip for fip in self.floating_ips.list()
                       if not fip.port_id][0]
        compute_port = self._get_compute_ports()[0]
        port_target_id = self._get_target_id(compute_port)

        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        api.neutron.floating_ip_target_list(IsA(http.HttpRequest)) \
            .AndReturn(self._get_fip_targets())
        api.neutron.floating_ip_associate(IsA(http.HttpRequest),
                                          floating_ip.id,
                                          port_target_id)
        self.mox.ReplayAll()

        form_data = {'instance_id': port_target_id,
                     'ip_id': floating_ip.id}
        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('floating_ip_associate',
                                      'floating_ip_target_list',
                                      'tenant_floating_ip_list',)})
    def test_associate_post_with_redirect(self):
        floating_ip = [fip for fip in self.floating_ips.list()
                       if not fip.port_id][0]
        compute_port = self._get_compute_ports()[0]
        port_target_id = self._get_target_id(compute_port)

        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        api.neutron.floating_ip_target_list(IsA(http.HttpRequest)) \
            .AndReturn(self._get_fip_targets())
        api.neutron.floating_ip_associate(IsA(http.HttpRequest),
                                          floating_ip.id,
                                          port_target_id)
        self.mox.ReplayAll()
        next = reverse("horizon:project:instances:index")
        form_data = {'instance_id': port_target_id,
                     'next': next,
                     'ip_id': floating_ip.id}
        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, next)

    @test.create_stubs({api.neutron: ('floating_ip_associate',
                                      'floating_ip_target_list',
                                      'tenant_floating_ip_list',)})
    def test_associate_post_with_exception(self):
        floating_ip = [fip for fip in self.floating_ips.list()
                       if not fip.port_id][0]
        compute_port = self._get_compute_ports()[0]
        port_target_id = self._get_target_id(compute_port)

        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        api.neutron.floating_ip_target_list(IsA(http.HttpRequest)) \
            .AndReturn(self._get_fip_targets())
        api.neutron.floating_ip_associate(IsA(http.HttpRequest),
                                          floating_ip.id,
                                          port_target_id) \
            .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        form_data = {'instance_id': port_target_id,
                     'ip_id': floating_ip.id}
        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_list',),
                        api.neutron: ('floating_ip_disassociate',
                                      'floating_ip_pools_list',
                                      'tenant_floating_ip_get',
                                      'tenant_floating_ip_list',
                                      'is_extension_supported',)})
    def test_disassociate_post(self):
        floating_ip = self.floating_ips.first()

        api.nova.server_list(IsA(http.HttpRequest), detailed=False) \
            .AndReturn([self.servers.list(), False])
        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        api.neutron.floating_ip_pools_list(IsA(http.HttpRequest)) \
            .AndReturn(self.pools.list())
        api.neutron.floating_ip_disassociate(IsA(http.HttpRequest),
                                             floating_ip.id)
        self.mox.ReplayAll()

        action = "floating_ips__disassociate__%s" % floating_ip.id
        res = self.client.post(INDEX_URL, {"action": action})
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.nova: ('server_list',),
                        api.neutron: ('floating_ip_disassociate',
                                      'floating_ip_pools_list',
                                      'tenant_floating_ip_get',
                                      'tenant_floating_ip_list',
                                      'is_extension_supported',)})
    def test_disassociate_post_with_exception(self):
        floating_ip = self.floating_ips.first()

        api.nova.server_list(IsA(http.HttpRequest), detailed=False) \
            .AndReturn([self.servers.list(), False])
        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        api.neutron.floating_ip_pools_list(IsA(http.HttpRequest)) \
            .AndReturn(self.pools.list())
        api.neutron.floating_ip_disassociate(IsA(http.HttpRequest),
                                             floating_ip.id) \
            .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        action = "floating_ips__disassociate__%s" % floating_ip.id
        res = self.client.post(INDEX_URL, {"action": action})
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('tenant_floating_ip_list',
                                      'floating_ip_pools_list',),
                        api.nova: ('server_list',),
                        quotas: ('tenant_quota_usages',),
                        api.base: ('is_service_enabled',)})
    def test_allocate_button_attributes(self):
        floating_ips = self.floating_ips.list()
        floating_pools = self.pools.list()
        quota_data = self.quota_usages.first()
        quota_data['floating_ips']['available'] = 10

        api.neutron.tenant_floating_ip_list(
            IsA(http.HttpRequest)) \
            .AndReturn(floating_ips)
        api.neutron.floating_ip_pools_list(
            IsA(http.HttpRequest)) \
            .AndReturn(floating_pools)
        api.nova.server_list(
            IsA(http.HttpRequest), detailed=False) \
            .AndReturn([self.servers.list(), False])
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest), targets=('floating_ips', )).MultipleTimes()\
            .AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        allocate_action = self.getAndAssertTableAction(res, 'floating_ips',
                                                       'allocate')
        self.assertEqual(set(['ajax-modal']), set(allocate_action.classes))
        self.assertEqual('Allocate IP To Project',
                         six.text_type(allocate_action.verbose_name))
        self.assertIsNone(allocate_action.policy_rules)

        url = 'horizon:project:floating_ips:allocate'
        self.assertEqual(url, allocate_action.url)

    @test.create_stubs({api.neutron: ('tenant_floating_ip_list',
                                      'floating_ip_pools_list',),
                        api.nova: ('server_list',),
                        quotas: ('tenant_quota_usages',),
                        api.base: ('is_service_enabled',)})
    def test_allocate_button_disabled_when_quota_exceeded(self):
        floating_ips = self.floating_ips.list()
        floating_pools = self.pools.list()
        quota_data = self.quota_usages.first()
        quota_data['floating_ips']['available'] = 0

        api.neutron.tenant_floating_ip_list(
            IsA(http.HttpRequest)) \
            .AndReturn(floating_ips)
        api.neutron.floating_ip_pools_list(
            IsA(http.HttpRequest)) \
            .AndReturn(floating_pools)
        api.nova.server_list(
            IsA(http.HttpRequest), detailed=False) \
            .AndReturn([self.servers.list(), False])
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest), targets=('floating_ips', )).MultipleTimes()\
            .AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        allocate_action = self.getAndAssertTableAction(res, 'floating_ips',
                                                       'allocate')
        self.assertIn('disabled', allocate_action.classes,
                      'The create button should be disabled')
        self.assertEqual('Allocate IP To Project (Quota exceeded)',
                         six.text_type(allocate_action.verbose_name))

    @test.create_stubs({api.neutron: ('floating_ip_pools_list',
                                      'floating_ip_supported',
                                      'tenant_floating_ip_list',
                                      'is_extension_supported',
                                      'is_router_enabled',
                                      'tenant_quota_get'),
                        api.base: ('is_service_enabled',),
                        api.cinder: ('is_volume_service_enabled',)})
    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_correct_quotas_displayed(self):
        api.cinder.is_volume_service_enabled(IsA(http.HttpRequest)) \
            .AndReturn(False)
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .MultipleTimes().AndReturn(True)
        api.base.is_service_enabled(IsA(http.HttpRequest), 'compute') \
            .MultipleTimes().AndReturn(True)
        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'security-group').AndReturn(True)
        api.neutron.is_extension_supported(IsA(http.HttpRequest), 'quotas') \
            .AndReturn(True)
        api.neutron.is_router_enabled(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.neutron.tenant_quota_get(IsA(http.HttpRequest), self.tenant.id) \
            .AndReturn(self.neutron_quotas.first())
        api.neutron.floating_ip_supported(IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.neutron.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(self.floating_ips.list())
        api.neutron.floating_ip_pools_list(IsA(http.HttpRequest)) \
            .AndReturn(self.pools.list())
        self.mox.ReplayAll()

        url = reverse('%s:allocate' % NAMESPACE)
        res = self.client.get(url)
        self.assertEqual(res.context['usages']['floating_ips']['quota'],
                         self.neutron_quotas.first().get('floatingip').limit)
