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
import copy

from django.test.utils import override_settings
from django.urls import reverse

import mock

from openstack_auth import utils as auth_utils

from horizon.workflows import views

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

DETAIL_URL = 'horizon:project:networks:ports:detail'

NETWORKS_INDEX_URL = reverse('horizon:project:networks:index')
NETWORKS_DETAIL_URL = 'horizon:project:networks:detail'


class NetworkPortTests(test.TestCase):

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
                                      'is_extension_supported',
                                      'security_group_list')})
    def _test_port_detail(self, mac_learning=False):
        # Use a port associated with security group
        port = [p for p in self.ports.list() if p.security_groups][0]
        sgs = [sg for sg in self.security_groups.list()
               if sg.id in port.security_groups]
        network_id = self.networks.first().id
        self.mock_port_get.return_value = port
        self.mock_security_group_list.return_value = sgs
        self._stub_is_extension_supported({'mac-learning': mac_learning,
                                           'allowed-address-pairs': False})
        self.mock_network_get.return_value = self.networks.first()

        res = self.client.get(reverse(DETAIL_URL, args=[port.id]))

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['port'].id, port.id)

        self.mock_port_get.assert_called_once_with(test.IsHttpRequest(),
                                                   port.id)
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(),
            id=tuple(sg.id for sg in port.security_groups))
        self._check_is_extension_supported({'mac-learning': 2,
                                            'allowed-address-pairs': 2})
        self.mock_network_get.assert_called_once_with(test.IsHttpRequest(),
                                                      network_id)

    @test.create_mocks({api.neutron: ('port_get',)})
    def test_port_detail_exception(self):
        port = self.ports.first()
        self.mock_port_get.side_effect = self.exceptions.neutron

        res = self.client.get(reverse(DETAIL_URL, args=[port.id]))

        self.assertRedirectsNoFollow(res, NETWORKS_INDEX_URL)
        self.mock_port_get.assert_called_once_with(test.IsHttpRequest(),
                                                   port.id)

    def test_port_update_get(self):
        self._test_port_update_get()

    def test_port_update_get_with_mac_learning(self):
        self._test_port_update_get(mac_learning=True)

    @test.create_mocks({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'security_group_list')})
    def _test_port_update_get(self, mac_learning=False, binding=False):
        port = self.ports.first()
        self.mock_port_get.return_value = port
        self._stub_is_extension_supported({'binding': binding,
                                           'mac-learning': mac_learning,
                                           'port_security': False})
        self.mock_security_group_list.return_value = \
            self.security_groups.list()

        url = reverse('horizon:project:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_port_get, 2,
            mock.call(test.IsHttpRequest(), port.id))
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=self.tenant.id)
        self._check_is_extension_supported({'binding': 1,
                                            'mac-learning': 1,
                                            'port-security': 1})

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
        security_groups = self.security_groups.list()
        sg_ids = [sg.id for sg in security_groups]

        self.mock_port_get.return_value = port
        self.mock_security_group_list.return_value = \
            self.security_groups.list()
        self._stub_is_extension_supported({'binding': binding,
                                           'mac-learning': mac_learning,
                                           'port-security': port_security})
        self.mock_port_update.return_value = port

        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        if port_security:
            extension_kwargs['port_security_enabled'] = True
        extension_kwargs['security_groups'] = sg_ids

        form_data = {'network_id': port.network_id,
                     'port_id': port.id,
                     'name': port.name,
                     'admin_state': port.admin_state_up}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        if port_security:
            form_data['port_security_enabled'] = True
        form_data['default_update_security_groups_role'] = 'member'
        form_data['update_security_groups_role_member'] = sg_ids
        url = reverse('horizon:project:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, form_data)

        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_port_get, 2,
            mock.call(test.IsHttpRequest(), port.id))
        self._check_is_extension_supported({'binding': 1,
                                            'mac-learning': 1,
                                            'port-security': 1})
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=self.tenant.id)
        self.mock_port_update.assert_called_once_with(
            test.IsHttpRequest(), port.id, name=port.name,
            admin_state_up=port.admin_state_up,
            **extension_kwargs)

    def test_port_update_post_exception(self):
        self._test_port_update_post_exception()

    def test_port_update_post_exception_with_mac_learning(self):
        self._test_port_update_post_exception(mac_learning=True)

    def test_port_update_post_exception_with_port_security(self):
        self._test_port_update_post_exception(port_security=True)

    @test.create_mocks({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'security_group_list',
                                      'port_update')})
    def _test_port_update_post_exception(self, mac_learning=False,
                                         binding=False, port_security=False):
        port = self.ports.first()
        security_groups = self.security_groups.list()
        sg_ids = [sg.id for sg in security_groups]

        self.mock_port_get.return_value = port
        self.mock_security_group_list.return_value = \
            self.security_groups.list()
        self._stub_is_extension_supported({'binding': binding,
                                           'mac-learning': mac_learning,
                                           'port-security': port_security})
        self.mock_port_update.side_effect = self.exceptions.neutron

        form_data = {'network_id': port.network_id,
                     'port_id': port.id,
                     'name': port.name,
                     'admin_state': port.admin_state_up}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        if port_security:
            form_data['port_security_enabled'] = True
        form_data['default_update_security_groups_role'] = 'member'
        form_data['update_security_groups_role_member'] = sg_ids
        url = reverse('horizon:project:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, form_data)

        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_port_get, 2,
            mock.call(test.IsHttpRequest(), port.id))
        self._check_is_extension_supported({'binding': 1,
                                            'mac-learning': 1,
                                            'port-security': 1})
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=self.tenant.id)
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        if port_security:
            extension_kwargs['port_security_enabled'] = True
        extension_kwargs['security_groups'] = sg_ids
        self.mock_port_update.assert_called_once_with(
            test.IsHttpRequest(), port.id, name=port.name,
            admin_state_up=port.admin_state_up,
            **extension_kwargs)

    @test.create_mocks({api.neutron: ('port_get',
                                      'network_get',
                                      'is_extension_supported')})
    def test_allowed_address_pair_detail(self):
        port = self.ports.first()
        network = self.networks.first()
        self.mock_port_get.return_value = self.ports.first()
        self.mock_network_get.return_value = network
        self._stub_is_extension_supported({'allowed-address-pairs': True,
                                           'mac-learning': False})

        res = self.client.get(reverse('horizon:project:networks:ports:detail',
                                      args=[port.id]))

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['port'].id, port.id)
        address_pairs = res.context['allowed_address_pairs_table'].data
        self.assertItemsEqual(port.allowed_address_pairs, address_pairs)

        self.mock_port_get.assert_called_once_with(test.IsHttpRequest(),
                                                   port.id)
        self._check_is_extension_supported({'allowed-address-pairs': 2,
                                            'mac-learning': 2})
        self.mock_network_get.assert_called_once_with(
            test.IsHttpRequest(), network.id)

    @override_settings(POLICY_CHECK_FUNCTION='openstack_auth.policy.check')
    @test.create_mocks({api.neutron: ('port_get',
                                      'network_get',
                                      'is_extension_supported')})
    def test_add_allowed_address_pair_button_shown_to_network_owner(self):
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
                                      'is_extension_supported')})
    def test_add_allowed_address_pair_button_disabled_to_other_tenant(self):
        # Current user tenant_id is 1 so select port whose tenant_id is
        # other than 1 for checking "Add Allowed Address Pair" button is not
        # displayed on the screen.
        user = auth_utils.get_user(self.request)

        # select port such that tenant_id is different from user's tenant_id.
        port = [p for p in self.ports.list()
                if p.tenant_id != user.tenant_id][0]

        self._stub_is_extension_supported(
            {'allowed-address-pairs': False, 'mac-learning': False})

        with mock.patch('openstack_auth.utils.get_user', return_value=user):
            url = reverse(
                'horizon:project:networks:ports:addallowedaddresspairs',
                args=[port.id])
            classes = 'btn data-table-action btn-default ajax-modal'
            link_name = "Add Allowed Address Pair"

            expected_string = \
                '<a id="allowed_address_pairs__action_AddAllowedAddressPair" ' \
                'class="%s" href="%s" title="Add Allowed Address Pair">' \
                '<span class="fa fa-plus"></span> %s</a>' \
                % (classes, url, link_name)

            res = self.client.get(reverse(
                'horizon:project:networks:ports:detail', args=[port.id]))

            self.assertNotIn(
                expected_string, res.context_data['tab_group'].render())

    @test.create_mocks({api.neutron: ('port_get',
                                      'port_update')})
    def test_port_add_allowed_address_pair(self):
        detail_path = 'horizon:project:networks:ports:detail'

        pre_port = self.ports.first()
        post_port = copy.deepcopy(pre_port)
        pair = {'ip_address': '179.0.0.201',
                'mac_address': 'fa:16:4e:7a:7b:18'}
        post_port['allowed_address_pairs'].insert(
            1, api.neutron.PortAllowedAddressPair(pair))

        self.mock_port_get.return_value = pre_port
        self.mock_port_update.return_value = {'port': post_port}

        form_data = {'ip': pair['ip_address'], 'mac': pair['mac_address'],
                     'port_id': pre_port.id}
        url = reverse('horizon:project:networks:ports:addallowedaddresspairs',
                      args=[pre_port.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        detail_url = reverse(detail_path, args=[pre_port.id])
        self.assertRedirectsNoFollow(res, detail_url)
        self.assertMessageCount(success=1)

        self.mock_port_get.assert_called_once_with(
            test.IsHttpRequest(), pre_port.id)
        update_pairs = post_port['allowed_address_pairs']
        update_pairs = [p.to_dict() for p in update_pairs]
        params = {'allowed_address_pairs': update_pairs}
        self.mock_port_update.assert_called_once_with(
            test.IsHttpRequest(), pre_port.id, **params)

    def test_port_add_allowed_address_pair_incorrect_mac(self):
        pre_port = self.ports.first()
        pair = {'ip_address': '179.0.0.201',
                'mac_address': 'incorrect'}
        form_data = {'ip': pair['ip_address'], 'mac': pair['mac_address'],
                     'port_id': pre_port.id}
        url = reverse('horizon:project:networks:ports:addallowedaddresspairs',
                      args=[pre_port.id])
        res = self.client.post(url, form_data)
        self.assertFormErrors(res, 1)
        self.assertContains(res, "Invalid MAC Address format")

    def test_port_add_allowed_address_pair_incorrect_ip(self):
        pre_port = self.ports.first()
        pair = {'ip_address': 'incorrect',
                'mac_address': 'fa:16:4e:7a:7b:18'}
        form_data = {'ip': pair['ip_address'], 'mac': pair['mac_address'],
                     'port_id': pre_port.id}
        url = reverse('horizon:project:networks:ports:addallowedaddresspairs',
                      args=[pre_port.id])
        res = self.client.post(url, form_data)
        self.assertFormErrors(res, 1)
        self.assertContains(res, "Incorrect format for IP address")

    @override_settings(POLICY_CHECK_FUNCTION='openstack_auth.policy.check')
    @test.create_mocks({api.neutron: ('port_get',
                                      'network_get',
                                      'port_update',
                                      'is_extension_supported')})
    def test_delete_address_pair_button_shown_to_network_owner(self):
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

    @override_settings(POLICY_CHECK_FUNCTION='openstack_auth.policy.check')
    @test.create_mocks({api.neutron: ('port_get',
                                      'network_get',
                                      'is_extension_supported')})
    def test_delete_address_pair_button_disabled_to_other_tenant(self):
        # Current user tenant_id is 1 so select port whose tenant_id is
        # other than 1 for checking "Delete Allowed Address Pair" button is
        # not displayed on the screen.
        user = auth_utils.get_user(self.request)

        # select port such that tenant_id is different from user's tenant_id.
        port = [p for p in self.ports.list()
                if p.tenant_id != user.tenant_id][0]

        self._stub_is_extension_supported(
            {'allowed-address-pairs': False, 'mac-learning': False})

        with mock.patch('openstack_auth.utils.get_user', return_value=user):
            classes = 'data-table-action btn-danger btn'

            expected_string = \
                '<button data-batch-action="true" ' \
                'id="allowed_address_pairs__action_delete" ' \
                'class="%s" name="action" help_text="This action cannot be ' \
                'undone." type="submit" ' \
                'value="allowed_address_pairs__delete">' \
                '<span class="fa fa-trash"></span>' \
                ' Delete</button>' % (classes)

            res = self.client.get(reverse(
                'horizon:project:networks:ports:detail', args=[port.id]))

            self.assertNotIn(
                expected_string, res.context_data['tab_group'].render())

    @test.create_mocks({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_remove_allowed_address_pair(self):
        detail_path = 'horizon:project:networks:ports:detail'

        pre_port = self.ports.first()
        post_port = copy.deepcopy(pre_port)
        pair = post_port['allowed_address_pairs'].pop()

        # After update the detail page is loaded
        self.mock_port_get.side_effect = [pre_port, post_port]
        self.mock_port_update.return_value = {'port': post_port}
        self._stub_is_extension_supported({'mac-learning': False,
                                           'allowed-address-pairs': True})

        pair_ip = pair['ip_address']
        form_data = {'action': 'allowed_address_pairs__delete__%s' % pair_ip}
        url = reverse(detail_path, args=[pre_port.id])

        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, url)
        self.assertMessageCount(success=1)

        self.mock_port_get.assert_has_calls([
            mock.call(test.IsHttpRequest(), pre_port.id),
            mock.call(test.IsHttpRequest(), pre_port.id),
        ])
        self.assertEqual(2, self.mock_port_get.call_count)
        params = {'allowed_address_pairs': post_port['allowed_address_pairs']}
        self.mock_port_update.assert_called_once_with(
            test.IsHttpRequest(), pre_port.id, **params)
        self._check_is_extension_supported({'mac-learning': 1,
                                            'allowed-address-pairs': 2})

    def test_port_create_get(self):
        self._test_port_create_get()

    def test_port_create_get_with_mac_learning(self):
        self._test_port_create_get(mac_learning=True)

    def test_port_create_get_without_subnet_detail(self):
        self._test_port_create_get(no_subnet_detail=True)

    @test.create_mocks({api.neutron: ('network_get',
                                      'security_group_list',
                                      'is_extension_supported')})
    def _test_port_create_get(self, mac_learning=False, binding=False,
                              no_subnet_detail=False):
        network = self.networks.first()
        if no_subnet_detail:
            # Set Subnet UUID list to network.subnets to emulate
            # a situation where a user has no enough permission to
            # retrieve subnet details.
            network.subnets = [s.id for s in network.subnets]
        self.mock_network_get.return_value = self.networks.first()
        self._stub_is_extension_supported({'binding': binding,
                                           'mac-learning': mac_learning,
                                           'port-security': True})
        self.mock_security_group_list.return_value = \
            self.security_groups.list()

        url = reverse('horizon:project:networks:addport',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self._check_is_extension_supported({'binding': 1,
                                            'mac-learning': 1,
                                            'port-security': 1})
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id='1')

    @test.create_mocks({api.neutron: ('network_get',
                                      'security_group_list',
                                      'is_extension_supported')})
    def test_port_create_on_network_from_different_tenant(self):
        network = self.networks.list()[1]
        tenant_id = self.request.user.tenant_id
        # Ensure the network belongs to a different tenant
        self.assertNotEqual(tenant_id, network.tenant_id)

        self.mock_network_get.return_value = self.networks.first()
        self._stub_is_extension_supported({'binding': False,
                                           'mac-learning': False,
                                           'port-security': True})
        self.mock_security_group_list.return_value = \
            self.security_groups.list()

        url = reverse('horizon:project:networks:addport',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self._check_is_extension_supported({'binding': 1,
                                            'mac-learning': 1,
                                            'port-security': 1})
        # Check the new port belongs to a tenant of the login user
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id=tenant_id)

    def test_port_create_post(self):
        self._test_port_create_post()

    def test_port_create_post_with_mac_learning(self):
        self._test_port_create_post(mac_learning=True, binding=False)

    def test_port_create_post_with_port_security(self):
        self._test_port_create_post(port_security=True)

    @test.create_mocks({api.neutron: ('network_get',
                                      'port_create',
                                      'security_group_list',
                                      'is_extension_supported')})
    def _test_port_create_post(self, mac_learning=False, binding=False,
                               port_security=False):
        network = self.networks.first()
        port = self.ports.first()
        self.mock_network_get.return_value = self.networks.first()
        self._stub_is_extension_supported({'binding': binding,
                                           'mac-learning': mac_learning,
                                           'port-security': port_security})
        self.mock_security_group_list.return_value = \
            self.security_groups.list()
        self.mock_port_create.return_value = port

        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'specify_ip': 'fixed_ip',
                     'fixed_ip': port.fixed_ips[0]['ip_address'],
                     'subnet_id': port.fixed_ips[0]['subnet_id'],
                     'mac_address': port.mac_address}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        if port_security:
            form_data['port_security_enabled'] = False
        url = reverse('horizon:project:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self._check_is_extension_supported({'binding': 1,
                                            'mac-learning': 1,
                                            'port-security': 1})
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = \
                port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        if port_security:
            # The default value is True, so False is intentionally used.
            extension_kwargs['port_security_enabled'] = False
        fixed_ips = [{'ip_address': ip['ip_address']} for ip in port.fixed_ips]
        self.mock_port_create.assert_called_once_with(
            test.IsHttpRequest(),
            network_id=network.id,
            name=port.name,
            admin_state_up=port.admin_state_up,
            device_id=port.device_id,
            device_owner=port.device_owner,
            fixed_ips=fixed_ips,
            mac_address=port.mac_address,
            security_groups=[],
            **extension_kwargs)
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id='1')

    @test.create_mocks({api.neutron: ('network_get',
                                      'security_group_list',
                                      'is_extension_supported')})
    def test_port_create_post_designated_subnet(self):
        network = self.networks.first()
        port = self.ports.first()
        self.mock_network_get.return_value = self.networks.first()
        self._stub_is_extension_supported({'binding': False,
                                           'mac-learning': False,
                                           'port-security': False})
        self.mock_security_group_list.return_value = \
            self.security_groups.list()
        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'specify_ip': 'subnet_id',
                     'subnet_id': "",
                     'mac_address': port.mac_address}
        url = reverse('horizon:project:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)
        self.assertFormErrors(res, 1)
        self.assertContains(res, "This field is required.")
        self._check_is_extension_supported({'binding': 1,
                                            'mac-learning': 1,
                                            'port-security': 1})
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id='1')
        self.mock_network_get.assert_called_with(test.IsHttpRequest(),
                                                 network.id)

    @test.create_mocks({api.neutron: ('network_get',
                                      'security_group_list',
                                      'is_extension_supported')})
    def test_port_create_post_designated_fixed_ip(self):
        network = self.networks.first()
        port = self.ports.first()
        self.mock_network_get.return_value = self.networks.first()
        self._stub_is_extension_supported({'binding': False,
                                           'mac-learning': False,
                                           'port-security': False})
        self.mock_security_group_list.return_value = \
            self.security_groups.list()
        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'specify_ip': 'fixed_ip',
                     'fixed_ip': "",
                     'mac_address': port.mac_address}
        url = reverse('horizon:project:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)
        self.assertFormErrors(res, 1)
        self.assertContains(res, "This field is required.")
        self._check_is_extension_supported({'binding': 1,
                                            'mac-learning': 1,
                                            'port-security': 1})
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id='1')
        self.mock_network_get.assert_called_with(test.IsHttpRequest(),
                                                 network.id)

    def test_port_create_post_exception(self):
        self._test_port_create_post_exception()

    def test_port_create_post_exception_with_mac_learning(self):
        self._test_port_create_post_exception(mac_learning=True)

    @test.create_mocks({api.neutron: ('network_get',
                                      'port_create',
                                      'security_group_list',
                                      'is_extension_supported')})
    def _test_port_create_post_exception(self, mac_learning=False,
                                         binding=False, port_security=False):
        network = self.networks.first()
        port = self.ports.first()
        self.mock_network_get.return_value = self.networks.first()
        self._stub_is_extension_supported({'binding': binding,
                                           'mac-learning': mac_learning,
                                           'port-security': port_security})
        self.mock_port_create.side_effect = self.exceptions.neutron
        self.mock_security_group_list.return_value = \
            self.security_groups.list()

        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'mac_state': True,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'specify_ip': 'fixed_ip',
                     'fixed_ip': port.fixed_ips[0]['ip_address'],
                     'subnet_id': port.fixed_ips[0]['subnet_id'],
                     'mac_address': port.mac_address}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_learning_enabled'] = True
        if port_security:
            form_data['port_security_enabled'] = False
        url = reverse('horizon:project:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_get, 2,
            mock.call(test.IsHttpRequest(), network.id))
        self._check_is_extension_supported({'binding': 1,
                                            'mac-learning': 1,
                                            'port-security': 1})
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        if port_security:
            extension_kwargs['port_security_enabled'] = False
        fixed_ips = [{'ip_address': ip['ip_address']} for ip in port.fixed_ips]
        self.mock_port_create.assert_called_once_with(
            test.IsHttpRequest(),
            network_id=network.id,
            name=port.name,
            admin_state_up=port.admin_state_up,
            device_id=port.device_id,
            device_owner=port.device_owner,
            fixed_ips=fixed_ips,
            mac_address=port.mac_address,
            security_groups=[],
            **extension_kwargs)
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest(), tenant_id='1')

    def test_port_delete(self):
        self._test_port_delete()

    def test_port_delete_with_mac_learning(self):
        self._test_port_delete(mac_learning=True)

    @test.create_mocks({api.neutron: ('port_delete',
                                      'port_list',
                                      'is_extension_supported')})
    def _test_port_delete(self, mac_learning=False):
        port = self.ports.first()
        network_id = port.network_id

        self.mock_port_delete.return_value = None
        self.mock_port_list.return_value = [self.ports.first()]
        self.mock_is_extension_supported.return_value = mac_learning

        form_data = {'action': 'ports__delete__%s' % port.id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

        self.mock_port_delete.assert_called_once_with(test.IsHttpRequest(),
                                                      port.id)
        self.mock_port_list.assert_called_once_with(test.IsHttpRequest(),
                                                    network_id=network_id)
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'mac-learning')

    def test_port_delete_exception(self):
        self._test_port_delete_exception()

    def test_port_delete_exception_with_mac_learning(self):
        self._test_port_delete_exception(mac_learning=True)

    @test.create_mocks({api.neutron: ('port_delete',
                                      'port_list',
                                      'is_extension_supported')})
    def _test_port_delete_exception(self, mac_learning=False):
        port = self.ports.first()
        network_id = port.network_id

        self.mock_port_delete.side_effect = self.exceptions.neutron
        self.mock_port_list.return_value = [self.ports.first()]
        self.mock_is_extension_supported.return_value = mac_learning

        form_data = {'action': 'ports__delete__%s' % port.id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

        self.mock_port_delete.assert_called_once_with(test.IsHttpRequest(),
                                                      port.id)
        self.mock_port_list.assert_called_once_with(test.IsHttpRequest(),
                                                    network_id=network_id)
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'mac-learning')
