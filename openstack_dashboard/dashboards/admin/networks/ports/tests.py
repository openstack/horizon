# Copyright 2012 NEC Corporation
# Copyright 2015 Cisco Systems, Inc.
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

import collections

from django.test.utils import override_settings
from django.urls import reverse

import mock

from horizon.workflows import views

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

DETAIL_URL = 'horizon:admin:networks:ports:detail'

NETWORKS_INDEX_URL = reverse('horizon:admin:networks:index')
NETWORKS_DETAIL_URL = 'horizon:admin:networks:detail'


class NetworkPortTests(test.BaseAdminViewTests):

    def _stub_is_extension_supported(self, features):
        self._features = features
        self._feature_call_counts = collections.defaultdict(int)

        def fake_extension_supported(request, alias):
            self._feature_call_counts[alias] += 1
            return self._features[alias]

        self.mock_is_extension_supported.side_effect = fake_extension_supported

    def _check_is_extension_supported(self, expected_count):
        self.assertEqual(expected_count, self._feature_call_counts)

    def test_port_detail(self):
        self._test_port_detail()

    def test_port_detail_with_mac_learning(self):
        self._test_port_detail(mac_learning=True)

    @test.create_mocks({api.neutron: ('network_get',
                                      'port_get',
                                      'is_extension_supported',)})
    def _test_port_detail(self, mac_learning=False):
        port = self.ports.first()
        network_id = self.networks.first().id

        self.mock_port_get.return_value = self.ports.first()
        self._stub_is_extension_supported(
            {'mac-learning': mac_learning,
             'allowed-address-pairs': False})
        self.mock_network_get.return_value = self.networks.first()

        res = self.client.get(reverse(DETAIL_URL, args=[port.id]))

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['port'].id, port.id)

        self.mock_port_get.assert_called_once_with(test.IsHttpRequest(),
                                                   port.id)
        self._check_is_extension_supported(
            {'mac-learning': 3,
             'allowed-address-pairs': 2})
        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network_id)

    @test.create_mocks({api.neutron: ('port_get',)})
    def test_port_detail_exception(self):
        port = self.ports.first()
        self.mock_port_get.side_effect = self.exceptions.neutron

        res = self.client.get(reverse(DETAIL_URL, args=[port.id]))

        redir_url = NETWORKS_INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

        self.mock_port_get.assert_called_once_with(test.IsHttpRequest(),
                                                   port.id)

    def test_port_create_get(self):
        self._test_port_create_get()

    def test_port_create_get_with_mac_learning(self):
        self._test_port_create_get(mac_learning=True)

    def test_port_create_get_with_port_security(self):
        self._test_port_create_get(port_security=True)

    @test.create_mocks({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'security_group_list',)})
    def _test_port_create_get(self, mac_learning=False, binding=False,
                              port_security=False):
        network = self.networks.first()
        self.mock_network_get.return_value = network
        self.mock_security_group_list.return_value = \
            self.security_groups.list()
        self._stub_is_extension_supported(
            {'mac-learning': mac_learning,
             'binding': binding,
             'port-security': port_security})

        url = reverse('horizon:admin:networks:addport',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id='1')
        self._check_is_extension_supported(
            {'mac-learning': 1,
             'binding': 1,
             'port-security': 1})

    @test.create_mocks({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'security_group_list',)})
    def test_port_create_on_network_from_different_tenant(self):
        network = self.networks.list()[1]
        tenant_id = self.request.user.tenant_id
        # Ensure the network belongs to a different tenant
        self.assertNotEqual(tenant_id, network.tenant_id)

        self.mock_network_get.return_value = network
        self.mock_security_group_list.return_value = \
            self.security_groups.list()
        self._stub_is_extension_supported(
            {'mac-learning': False,
             'binding': False,
             'port-security': True})

        url = reverse('horizon:admin:networks:addport',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        # Check the new port belongs to a tenant of the network
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=network.tenant_id)
        self._check_is_extension_supported(
            {'mac-learning': 1,
             'binding': 1,
             'port-security': 1})

    def test_port_create_post(self):
        self._test_port_create_post()

    def test_port_create_post_with_mac_learning(self):
        self._test_port_create_post(mac_learning=True, binding=False)

    def test_port_create_post_with_port_security(self):
        self._test_port_create_post(port_security=True)

    @test.create_mocks({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'security_group_list',
                                      'port_create',)})
    def _test_port_create_post(self, mac_learning=False, binding=False,
                               port_security=False):
        network = self.networks.first()
        port = self.ports.first()
        security_groups = self.security_groups.list()
        sg_ids = [sg.id for sg in security_groups]

        self.mock_network_get.return_value = network
        self.mock_security_group_list.return_value = security_groups
        self._stub_is_extension_supported(
            {'mac-learning': mac_learning,
             'binding': binding,
             'port-security': port_security})
        self.mock_port_create.return_value = port

        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id,
                     'mac_address': port.mac_address}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        if port_security:
            form_data['port_security_enabled'] = True
            form_data['default_create_security_groups_role'] = 'member'
            form_data['create_security_groups_role_member'] = sg_ids
        url = reverse('horizon:admin:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id='1')
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = \
                port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        if port_security:
            extension_kwargs['port_security_enabled'] = True
            extension_kwargs['security_groups'] = sg_ids
        else:
            extension_kwargs['security_groups'] = []
        self.mock_port_create.assert_called_once_with(
            test.IsHttpRequest(),
            tenant_id=network.tenant_id,
            network_id=network.id,
            name=port.name,
            admin_state_up=port.admin_state_up,
            device_id=port.device_id,
            device_owner=port.device_owner,
            binding__host_id=port.binding__host_id,
            mac_address=port.mac_address,
            **extension_kwargs)
        self._check_is_extension_supported(
            {'mac-learning': 1,
             'binding': 1,
             'port-security': 1})

    @test.create_mocks({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'security_group_list',
                                      'port_create',)})
    def test_port_create_post_with_fixed_ip(self):
        network = self.networks.first()
        port = self.ports.first()
        self.mock_network_get.return_value = network
        self.mock_security_group_list.return_value = \
            self.security_groups.list()
        self._stub_is_extension_supported(
            {'mac-learning': False,
             'binding': True,
             'port-security': True})
        self.mock_port_create.return_value = port

        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id,
                     'mac_address': port.mac_address,
                     'specify_ip': 'fixed_ip',
                     'fixed_ip': port.fixed_ips[0]['ip_address'],
                     'subnet_id': port.fixed_ips[0]['subnet_id']}
        form_data['binding__vnic_type'] = port.binding__vnic_type
        url = reverse('horizon:admin:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self._check_is_extension_supported(
            {'mac-learning': 1,
             'binding': 1,
             'port-security': 1})
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id='1')
        fixed_ips = [{'ip_address': ip['ip_address']} for ip in port.fixed_ips]
        self.mock_port_create.assert_called_once_with(
            test.IsHttpRequest(),
            tenant_id=network.tenant_id,
            network_id=network.id,
            name=port.name,
            admin_state_up=port.admin_state_up,
            device_id=port.device_id,
            device_owner=port.device_owner,
            binding__host_id=port.binding__host_id,
            binding__vnic_type=port.binding__vnic_type,
            mac_address=port.mac_address,
            fixed_ips=fixed_ips,
            port_security_enabled=False,
            security_groups=[])

    def test_port_create_post_exception(self):
        self._test_port_create_post_exception()

    def test_port_create_post_exception_with_mac_learning(self):
        self._test_port_create_post_exception(mac_learning=True)

    def test_port_create_post_exception_with_port_security(self):
        self._test_port_create_post_exception(port_security=True)

    @test.create_mocks({api.neutron: ('network_get',
                                      'port_create',
                                      'security_group_list',
                                      'is_extension_supported',)})
    def _test_port_create_post_exception(self, mac_learning=False,
                                         binding=False,
                                         port_security=False):
        network = self.networks.first()
        port = self.ports.first()
        security_groups = self.security_groups.list()
        sg_ids = [sg.id for sg in security_groups]

        self.mock_network_get.return_value = network
        self._stub_is_extension_supported(
            {'mac-learning': mac_learning,
             'binding': binding,
             'port-security': port_security})
        self.mock_security_group_list.return_value = security_groups
        self.mock_port_create.side_effect = self.exceptions.neutron

        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'mac_state': True,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id,
                     'mac_address': port.mac_address}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_learning_enabled'] = True
        if port_security:
            form_data['port_security_enabled'] = True
            form_data['default_create_security_groups_role'] = 'member'
            form_data['create_security_groups_role_member'] = sg_ids
        url = reverse('horizon:admin:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self._check_is_extension_supported(
            {'mac-learning': 1,
             'binding': 1,
             'port-security': 1})
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id='1')
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        if port_security:
            extension_kwargs['port_security_enabled'] = True
            extension_kwargs['security_groups'] = sg_ids
        else:
            extension_kwargs['security_groups'] = []
        self.mock_port_create.assert_called_once_with(
            test.IsHttpRequest(),
            tenant_id=network.tenant_id,
            network_id=network.id,
            name=port.name,
            admin_state_up=port.admin_state_up,
            device_id=port.device_id,
            device_owner=port.device_owner,
            binding__host_id=port.binding__host_id,
            mac_address=port.mac_address,
            **extension_kwargs)

    def test_port_update_get(self):
        self._test_port_update_get()

    def test_port_update_get_with_mac_learning(self):
        self._test_port_update_get(mac_learning=True)

    def test_port_update_get_with_port_security(self):
        self._test_port_update_get(port_security=True)

    @test.create_mocks({api.neutron: ('port_get',
                                      'security_group_list',
                                      'is_extension_supported',)})
    def _test_port_update_get(self, mac_learning=False, binding=False,
                              port_security=False):
        port = self.ports.first()
        self.mock_port_get.return_value = port
        self._stub_is_extension_supported(
            {'binding': binding,
             'mac-learning': mac_learning,
             'port-security': port_security})
        self.mock_security_group_list.return_value = \
            self.security_groups.list()

        url = reverse('horizon:admin:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_port_get, 2,
            mock.call(test.IsHttpRequest(), port.id))
        self._check_is_extension_supported(
            {'binding': 1,
             'mac-learning': 1,
             'port-security': 1})
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id='1')

    def test_port_update_post(self):
        self._test_port_update_post()

    def test_port_update_post_with_mac_learning(self):
        self._test_port_update_post(mac_learning=True)

    def test_port_update_post_with_port_security(self):
        self._test_port_update_post(port_security=True)

    @test.create_mocks({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'security_group_list',
                                      'port_update')})
    def _test_port_update_post(self, mac_learning=False, binding=False,
                               port_security=False):
        port = self.ports.first()
        self.mock_port_get.return_value = port
        self._stub_is_extension_supported(
            {'binding': binding,
             'mac-learning': mac_learning,
             'port-security': port_security})
        self.mock_security_group_list.return_value = \
            self.security_groups.list()
        self.mock_port_update.return_value = port

        form_data = {'network_id': port.network_id,
                     'port_id': port.id,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id,
                     'mac_address': port.mac_address}

        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        if port_security:
            form_data['port_security_enabled'] = True
        url = reverse('horizon:admin:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, form_data)

        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_port_get, 2,
            mock.call(test.IsHttpRequest(), port.id))
        self._check_is_extension_supported(
            {'binding': 1,
             'mac-learning': 1,
             'port-security': 1})
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id='1')
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        if port_security:
            extension_kwargs['port_security_enabled'] = True
        self.mock_port_update.assert_called_once_with(
            test.IsHttpRequest(), port.id,
            name=port.name,
            admin_state_up=port.admin_state_up,
            device_id=port.device_id,
            device_owner=port.device_owner,
            binding__host_id=port.binding__host_id,
            mac_address=port.mac_address,
            security_groups=[],
            **extension_kwargs)

    def test_port_update_post_exception(self):
        self._test_port_update_post_exception()

    def test_port_update_post_exception_with_mac_learning(self):
        self._test_port_update_post_exception(mac_learning=True, binding=False)

    def test_port_update_post_exception_with_port_security(self):
        self._test_port_update_post_exception(port_security=True)

    @test.create_mocks({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'security_group_list',
                                      'port_update')})
    def _test_port_update_post_exception(self, mac_learning=False,
                                         binding=False,
                                         port_security=False):
        port = self.ports.first()
        self.mock_port_get.return_value = port
        self._stub_is_extension_supported(
            {'binding': binding,
             'mac-learning': mac_learning,
             'port-security': port_security})
        self.mock_security_group_list.return_value = \
            self.security_groups.list()
        self.mock_port_update.side_effect = self.exceptions.neutron

        form_data = {'network_id': port.network_id,
                     'port_id': port.id,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id,
                     'mac_address': port.mac_address}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        if port_security:
            form_data['port_security_enabled'] = True
        url = reverse('horizon:admin:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, form_data)

        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_port_get, 2,
            mock.call(test.IsHttpRequest(), port.id))
        self._check_is_extension_supported(
            {'binding': 1,
             'mac-learning': 1,
             'port-security': 1})
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id='1')
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        if port_security:
            extension_kwargs['port_security_enabled'] = True
        self.mock_port_update.assert_called_once_with(
            test.IsHttpRequest(), port.id,
            name=port.name,
            admin_state_up=port.admin_state_up,
            device_id=port.device_id,
            device_owner=port.device_owner,
            binding__host_id=port.binding__host_id,
            mac_address=port.mac_address,
            security_groups=[],
            **extension_kwargs)

    def test_port_delete(self):
        self._test_port_delete()

    def test_port_delete_with_mac_learning(self):
        self._test_port_delete(mac_learning=True)

    @test.create_mocks({api.neutron: ('port_delete',
                                      'subnet_list',
                                      'port_list',
                                      'show_network_ip_availability',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def _test_port_delete(self, mac_learning=False):
        port = self.ports.first()
        network_id = port.network_id
        self.mock_port_list.return_value = self.ports.list()
        self._stub_is_extension_supported(
            {'network-ip-availability': True,
             'mac-learning': mac_learning})

        form_data = {'action': 'ports__delete__%s' % port.id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

        self.mock_port_list.assert_called_once_with(test.IsHttpRequest(),
                                                    network_id=network_id)
        self._check_is_extension_supported(
            {'network-ip-availability': 1,
             'mac-learning': 1})

    def test_port_delete_exception(self):
        self._test_port_delete_exception()

    def test_port_delete_exception_with_mac_learning(self):
        self._test_port_delete_exception(mac_learning=True)

    @test.create_mocks({api.neutron: ('port_delete',
                                      'subnet_list',
                                      'port_list',
                                      'show_network_ip_availability',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks')})
    def _test_port_delete_exception(self, mac_learning=False):
        port = self.ports.first()
        network_id = port.network_id

        self.mock_port_delete.side_effect = self.exceptions.neutron
        self.mock_port_list.return_value = [self.ports.first()]
        self._stub_is_extension_supported(
            {'network-ip-availability': True,
             'mac-learning': mac_learning})

        form_data = {'action': 'ports__delete__%s' % port.id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

        self.mock_port_delete.assert_called_once_with(test.IsHttpRequest(),
                                                      port.id)
        self.mock_port_list.assert_called_once_with(test.IsHttpRequest(),
                                                    network_id=network_id)
        self._check_is_extension_supported(
            {'network-ip-availability': 1,
             'mac-learning': 1})

    @override_settings(POLICY_CHECK_FUNCTION='openstack_auth.policy.check')
    @test.create_mocks({api.neutron: ('port_get',
                                      'network_get',
                                      'is_extension_supported')})
    def test_add_allowed_address_pair_button_shown(self):
        port = self.ports.first()
        url = reverse('horizon:project:networks:ports:addallowedaddresspairs',
                      args=[port.id])
        classes = 'btn data-table-action btn-default ajax-modal'
        link_name = "Add Allowed Address Pair"

        expected_string = \
            '<a id="allowed_address_pairs__action_AddAllowedAddressPair" ' \
            'class="%s" href="%s" title="Add Allowed Address Pair">' \
            '<span class="fa fa-plus"></span> %s</a>' \
            % (classes, url, link_name)

        res = self.client.get(reverse('horizon:project:networks:ports:detail',
                                      args=[port.id]))

        self.assertTemplateUsed(res, 'horizon/common/_detail_tab_group.html')
        self.assertIn(expected_string, res.context_data['tab_group'].render())

    @override_settings(POLICY_CHECK_FUNCTION='openstack_auth.policy.check')
    @test.create_mocks({api.neutron: ('port_get',
                                      'network_get',
                                      'port_update',
                                      'is_extension_supported')})
    def test_delete_address_pair_button_shown(self):
        port = self.ports.first()
        classes = 'data-table-action btn-danger btn'

        expected_string = \
            '<button data-batch-action="true" ' \
            'id="allowed_address_pairs__action_delete" ' \
            'class="%s" name="action" help_text="This action cannot be ' \
            'undone." type="submit" value="allowed_address_pairs__delete">' \
            '<span class="fa fa-trash"></span>' \
            ' Delete</button>' \
            % (classes)

        res = self.client.get(reverse(
            'horizon:project:networks:ports:detail', args=[port.id]))

        self.assertTemplateUsed(res, 'horizon/common/_detail_tab_group.html')
        self.assertIn(expected_string, res.context_data['tab_group'].render())
