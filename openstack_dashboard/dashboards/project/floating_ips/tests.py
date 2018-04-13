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

from django.urls import reverse
from django.utils.http import urlencode

import mock
import six

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

from horizon.workflows import views


INDEX_URL = reverse('horizon:project:floating_ips:index')
NAMESPACE = "horizon:project:floating_ips"


class FloatingIpViewTests(test.TestCase):

    @test.create_mocks({api.neutron: ('floating_ip_target_list',
                                      'tenant_floating_ip_list')})
    def test_associate(self):
        self.mock_floating_ip_target_list.return_value = \
            self._get_fip_targets()
        self.mock_tenant_floating_ip_list.return_value = \
            self.floating_ips.list()

        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.get(url)
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        workflow = res.context['workflow']
        choices = dict(workflow.steps[0].action.fields['ip_id'].choices)
        # Verify that our "associated" floating IP isn't in the choices list.
        self.assertNotIn(self.floating_ips.first(), choices)

        self.mock_floating_ip_target_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest())

    @test.create_mocks({api.neutron: ('floating_ip_target_list_by_instance',
                                      'tenant_floating_ip_list')})
    def test_associate_with_instance_id(self):
        targets = self._get_fip_targets()
        target = targets[0]
        self.mock_floating_ip_target_list_by_instance.return_value = [target]
        self.mock_tenant_floating_ip_list.return_value = \
            self.floating_ips.list()

        base_url = reverse('%s:associate' % NAMESPACE)
        params = urlencode({'instance_id': target.instance_id})
        url = '?'.join([base_url, params])
        res = self.client.get(url)
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        workflow = res.context['workflow']
        choices = dict(workflow.steps[0].action.fields['ip_id'].choices)
        # Verify that our "associated" floating IP isn't in the choices list.
        self.assertNotIn(self.floating_ips.first(), choices)

        self.mock_floating_ip_target_list_by_instance.assert_called_once_with(
            test.IsHttpRequest(), target.instance_id)
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest())

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

    @test.create_mocks({api.neutron: ('floating_ip_target_list',
                                      'tenant_floating_ip_list')})
    def test_associate_with_port_id(self):
        compute_port = self._get_compute_ports()[0]
        associated_fips = [fip.id for fip in self.floating_ips.list()
                           if fip.port_id]

        self.mock_floating_ip_target_list.return_value = \
            self._get_fip_targets()
        self.mock_tenant_floating_ip_list.return_value = \
            self.floating_ips.list()

        base_url = reverse('%s:associate' % NAMESPACE)
        params = urlencode({'port_id': compute_port.id})
        url = '?'.join([base_url, params])
        res = self.client.get(url)
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        workflow = res.context['workflow']
        choices = dict(workflow.steps[0].action.fields['ip_id'].choices)
        # Verify that our "associated" floating IP isn't in the choices list.
        self.assertFalse(set(associated_fips) & set(choices.keys()))

        self.mock_floating_ip_target_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest())

    @test.create_mocks({api.neutron: ('floating_ip_associate',
                                      'floating_ip_target_list',
                                      'tenant_floating_ip_list')})
    def test_associate_post(self):
        floating_ip = [fip for fip in self.floating_ips.list()
                       if not fip.port_id][0]
        compute_port = self._get_compute_ports()[0]
        port_target_id = self._get_target_id(compute_port)

        self.mock_tenant_floating_ip_list.return_value = \
            self.floating_ips.list()
        self.mock_floating_ip_target_list.return_value = \
            self._get_fip_targets()
        self.mock_floating_ip_associate.return_value = None

        form_data = {'instance_id': port_target_id,
                     'ip_id': floating_ip.id}
        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_target_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_associate.assert_called_once_with(
            test.IsHttpRequest(), floating_ip.id, port_target_id)

    @test.create_mocks({api.neutron: ('floating_ip_associate',
                                      'floating_ip_target_list',
                                      'tenant_floating_ip_list')})
    def test_associate_post_with_redirect(self):
        floating_ip = [fip for fip in self.floating_ips.list()
                       if not fip.port_id][0]
        compute_port = self._get_compute_ports()[0]
        port_target_id = self._get_target_id(compute_port)

        self.mock_tenant_floating_ip_list.return_value = \
            self.floating_ips.list()
        self.mock_floating_ip_target_list.return_value = \
            self._get_fip_targets()
        self.mock_floating_ip_associate.return_value = None

        next = reverse("horizon:project:instances:index")
        form_data = {'instance_id': port_target_id,
                     'next': next,
                     'ip_id': floating_ip.id}
        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, next)

        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_target_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_associate.assert_called_once_with(
            test.IsHttpRequest(), floating_ip.id, port_target_id)

    @test.create_mocks({api.neutron: ('floating_ip_associate',
                                      'floating_ip_target_list',
                                      'tenant_floating_ip_list')})
    def test_associate_post_with_exception(self):
        floating_ip = [fip for fip in self.floating_ips.list()
                       if not fip.port_id][0]
        compute_port = self._get_compute_ports()[0]
        port_target_id = self._get_target_id(compute_port)

        self.mock_tenant_floating_ip_list.return_value = \
            self.floating_ips.list()
        self.mock_floating_ip_target_list.return_value = \
            self._get_fip_targets()
        self.mock_floating_ip_associate.side_effect = self.exceptions.nova

        form_data = {'instance_id': port_target_id,
                     'ip_id': floating_ip.id}
        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_target_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_associate.assert_called_once_with(
            test.IsHttpRequest(), floating_ip.id, port_target_id)

    @test.create_mocks({api.nova: ('server_list',),
                        api.neutron: ('floating_ip_disassociate',
                                      'floating_ip_pools_list',
                                      'is_extension_supported',
                                      'tenant_floating_ip_list')})
    def test_disassociate_post(self):
        floating_ip = self.floating_ips.first()

        self.mock_is_extension_supported.return_value = False
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_tenant_floating_ip_list.return_value = \
            self.floating_ips.list()
        self.mock_floating_ip_pools_list.return_value = self.pools.list()
        self.mock_floating_ip_disassociate.return_value = None

        action = "floating_ips__disassociate__%s" % floating_ip.id
        res = self.client.post(INDEX_URL, {"action": action})
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_list.assert_called_once_with(test.IsHttpRequest(),
                                                      detailed=False)
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_pools_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_disassociate.assert_called_once_with(
            test.IsHttpRequest(), floating_ip.id)
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'dns-integration')

    @test.create_mocks({api.nova: ('server_list',),
                        api.neutron: ('floating_ip_disassociate',
                                      'floating_ip_pools_list',
                                      'is_extension_supported',
                                      'tenant_floating_ip_list')})
    def test_disassociate_post_with_exception(self):
        floating_ip = self.floating_ips.first()

        self.mock_is_extension_supported.return_value = False
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_tenant_floating_ip_list.return_value = \
            self.floating_ips.list()
        self.mock_floating_ip_pools_list.return_value = self.pools.list()
        self.mock_floating_ip_disassociate.side_effect = self.exceptions.nova

        action = "floating_ips__disassociate__%s" % floating_ip.id
        res = self.client.post(INDEX_URL, {"action": action})
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_list.assert_called_once_with(test.IsHttpRequest(),
                                                      detailed=False)
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_pools_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_disassociate.assert_called_once_with(
            test.IsHttpRequest(), floating_ip.id)
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'dns-integration')

    @test.create_mocks({api.neutron: ('tenant_floating_ip_list',
                                      'is_extension_supported',
                                      'floating_ip_pools_list'),
                        api.nova: ('server_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_allocate_button_attributes(self):
        floating_ips = self.floating_ips.list()
        floating_pools = self.pools.list()
        quota_data = self.neutron_quota_usages.first()

        self.mock_is_extension_supported.return_value = False
        self.mock_tenant_floating_ip_list.return_value = floating_ips
        self.mock_floating_ip_pools_list.return_value = floating_pools
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_tenant_quota_usages.return_value = quota_data

        res = self.client.get(INDEX_URL)

        allocate_action = self.getAndAssertTableAction(res, 'floating_ips',
                                                       'allocate')
        self.assertEqual(set(['ajax-modal']), set(allocate_action.classes))
        self.assertEqual('Allocate IP To Project',
                         six.text_type(allocate_action.verbose_name))
        self.assertIsNone(allocate_action.policy_rules)

        url = 'horizon:project:floating_ips:allocate'
        self.assertEqual(url, allocate_action.url)

        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_pools_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_server_list.assert_called_once_with(test.IsHttpRequest(),
                                                      detailed=False)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 3,
            mock.call(test.IsHttpRequest(), targets=('floatingip', )))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'dns-integration',
        )

    @test.create_mocks({api.neutron: ('tenant_floating_ip_list',
                                      'is_extension_supported',
                                      'floating_ip_pools_list'),
                        api.nova: ('server_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_allocate_button_disabled_when_quota_exceeded(self):
        floating_ips = self.floating_ips.list()
        floating_pools = self.pools.list()
        quota_data = self.neutron_quota_usages.first()
        quota_data['floatingip']['available'] = 0

        self.mock_is_extension_supported.return_value = False
        self.mock_tenant_floating_ip_list.return_value = floating_ips
        self.mock_floating_ip_pools_list.return_value = floating_pools
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_tenant_quota_usages.return_value = quota_data

        res = self.client.get(INDEX_URL)

        allocate_action = self.getAndAssertTableAction(res, 'floating_ips',
                                                       'allocate')
        self.assertIn('disabled', allocate_action.classes,
                      'The create button should be disabled')
        self.assertEqual('Allocate IP To Project (Quota exceeded)',
                         six.text_type(allocate_action.verbose_name))

        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_pools_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_server_list.assert_called_once_with(test.IsHttpRequest(),
                                                      detailed=False)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_quota_usages, 3,
            mock.call(test.IsHttpRequest(), targets=('floatingip', )))
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'dns-integration',
        )

    @test.create_mocks({api.neutron: ('floating_ip_pools_list',
                                      'tenant_floating_ip_list',
                                      'is_extension_supported',
                                      'is_router_enabled',
                                      'tenant_quota_get'),
                        api.base: ('is_service_enabled',)})
    @test.update_settings(OPENSTACK_NEUTRON_NETWORK={'enable_quotas': True})
    def test_correct_quotas_displayed(self):
        self.mock_is_service_enabled.return_value = True
        self.mock_is_extension_supported.side_effect = [False, True, False]
        self.mock_is_router_enabled.return_value = True
        self.mock_tenant_quota_get.return_value = self.neutron_quotas.first()
        self.mock_tenant_floating_ip_list.return_value = \
            self.floating_ips.list()
        self.mock_floating_ip_pools_list.return_value = self.pools.list()

        url = reverse('%s:allocate' % NAMESPACE)
        res = self.client.get(url)
        self.assertEqual(res.context['usages']['floatingip']['quota'],
                         self.neutron_quotas.first().get('floatingip').limit)

        self.mock_is_service_enabled.assert_called_once_with(
            test.IsHttpRequest(), 'network')
        self.assertEqual(3, self.mock_is_extension_supported.call_count)
        self.mock_is_extension_supported.assert_has_calls([
            mock.call(test.IsHttpRequest(), 'dns-integration'),
            mock.call(test.IsHttpRequest(), 'quotas'),
            mock.call(test.IsHttpRequest(), 'quota_details'),
        ])
        self.mock_is_router_enabled.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_tenant_quota_get.assert_called_once_with(
            test.IsHttpRequest(), self.tenant.id)
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_floating_ip_pools_list.assert_called_once_with(
            test.IsHttpRequest())
