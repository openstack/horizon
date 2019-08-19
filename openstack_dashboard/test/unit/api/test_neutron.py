# Copyright 2012 NEC Corporation
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
import copy

import mock
import netaddr
from neutronclient.common import exceptions as neutron_exc
from oslo_utils import uuidutils
import six

from django.test.utils import override_settings

from openstack_dashboard import api
from openstack_dashboard import policy
from openstack_dashboard.test import helpers as test


class NeutronApiTests(test.APIMockTestCase):
    @mock.patch.object(api.neutron, 'neutronclient')
    def test_network_list(self, mock_neutronclient):
        networks = {'networks': self.api_networks.list()}
        subnets = {'subnets': self.api_subnets.list()}

        neutronclient = mock_neutronclient.return_value
        neutronclient.list_networks.return_value = networks
        neutronclient.list_subnets.return_value = subnets

        ret_val = api.neutron.network_list(self.request)
        for n in ret_val:
            self.assertIsInstance(n, api.neutron.Network)
        neutronclient.list_networks.assert_called_once_with()
        neutronclient.list_subnets.assert_called_once_with()

    @override_settings(OPENSTACK_NEUTRON_NETWORK={
        'enable_auto_allocated_network': True})
    @test.create_mocks({api.neutron: ('network_list',
                                      'subnet_list')})
    def _test_network_list_for_tenant(
            self, include_external,
            filter_params, should_called, **extra_kwargs):
        """Convenient method to test network_list_for_tenant.

        :param include_external: Passed to network_list_for_tenant.
        :param filter_params: Filters passed to network_list_for_tenant
        :param should_called: this argument specifies which methods
            should be called. Methods in this list should be called.
            Valid values are non_shared, shared, and external.
        """
        filter_params = filter_params or {}
        all_networks = self.networks.list()
        tenant_id = '1'
        tenant_networks = [n for n in all_networks
                           if n['tenant_id'] == tenant_id]
        shared_networks = [n for n in all_networks if n['shared']]
        external_networks = [n for n in all_networks if n['router:external']]

        return_values = []
        expected_calls = []
        if 'non_shared' in should_called:
            params = filter_params.copy()
            params['shared'] = False
            return_values.append(tenant_networks)
            expected_calls.append(
                mock.call(test.IsHttpRequest(), tenant_id=tenant_id, **params),
            )
        if 'shared' in should_called:
            params = filter_params.copy()
            params['shared'] = True
            return_values.append(shared_networks)
            expected_calls.append(
                mock.call(test.IsHttpRequest(), **params),
            )
        if 'external' in should_called:
            params = filter_params.copy()
            params['router:external'] = True
            return_values.append(external_networks)
            expected_calls.append(
                mock.call(test.IsHttpRequest(), **params),
            )
        self.mock_network_list.side_effect = return_values

        extra_kwargs.update(filter_params)
        ret_val = api.neutron.network_list_for_tenant(
            self.request, tenant_id,
            include_external=include_external,
            **extra_kwargs)

        expected = []
        if 'non_shared' in should_called:
            expected += tenant_networks
        if 'shared' in should_called:
            expected += shared_networks
        if 'external' in should_called and include_external:
            expected += external_networks
        self.assertEqual(set(n.id for n in expected),
                         set(n.id for n in ret_val))
        self.mock_network_list.assert_has_calls(expected_calls)

        # Ensure all three types of networks are not empty. This is required
        # to check 'pre_auto_allocate' network is not included.
        self.assertTrue(tenant_networks)
        self.assertTrue(shared_networks)
        self.assertTrue(external_networks)
        self.assertNotIn(api.neutron.AUTO_ALLOCATE_ID,
                         [n.id for n in ret_val])

    def test_network_list_for_tenant(self):
        self._test_network_list_for_tenant(
            include_external=False, filter_params=None,
            should_called=['non_shared', 'shared'])

    def test_network_list_for_tenant_with_external(self):
        self._test_network_list_for_tenant(
            include_external=True, filter_params=None,
            should_called=['non_shared', 'shared', 'external'])

    def test_network_list_for_tenant_with_filters_shared_false_wo_incext(self):
        self._test_network_list_for_tenant(
            include_external=False, filter_params={'shared': True},
            should_called=['shared'])

    def test_network_list_for_tenant_with_filters_shared_true_w_incext(self):
        self._test_network_list_for_tenant(
            include_external=True, filter_params={'shared': True},
            should_called=['shared', 'external'])

    def test_network_list_for_tenant_with_filters_ext_false_wo_incext(self):
        self._test_network_list_for_tenant(
            include_external=False, filter_params={'router:external': False},
            should_called=['non_shared', 'shared'])

    def test_network_list_for_tenant_with_filters_ext_true_wo_incext(self):
        self._test_network_list_for_tenant(
            include_external=False, filter_params={'router:external': True},
            should_called=['non_shared', 'shared'])

    def test_network_list_for_tenant_with_filters_ext_false_w_incext(self):
        self._test_network_list_for_tenant(
            include_external=True, filter_params={'router:external': False},
            should_called=['non_shared', 'shared'])

    def test_network_list_for_tenant_with_filters_ext_true_w_incext(self):
        self._test_network_list_for_tenant(
            include_external=True, filter_params={'router:external': True},
            should_called=['non_shared', 'shared', 'external'])

    def test_network_list_for_tenant_with_filters_both_shared_ext(self):
        # To check 'shared' filter is specified in network_list
        # to look up external networks.
        self._test_network_list_for_tenant(
            include_external=True,
            filter_params={'router:external': True, 'shared': True},
            should_called=['shared', 'external'])

    def test_network_list_for_tenant_with_other_filters(self):
        # To check filter parameters other than shared and
        # router:external are passed as expected.
        self._test_network_list_for_tenant(
            include_external=True,
            filter_params={'router:external': True, 'shared': False,
                           'foo': 'bar'},
            should_called=['non_shared', 'external'])

    def test_network_list_for_tenant_no_pre_auto_allocate_if_net_exists(self):
        self._test_network_list_for_tenant(
            include_external=True, filter_params=None,
            should_called=['non_shared', 'shared', 'external'],
            include_pre_auto_allocate=True)

    @override_settings(OPENSTACK_NEUTRON_NETWORK={
        'enable_auto_allocated_network': True})
    @test.create_mocks({api.neutron: ['network_list',
                                      'is_extension_supported'],
                        api.nova: ['is_feature_available']})
    def test_network_list_for_tenant_with_pre_auto_allocate(self):
        tenant_id = '1'
        self.mock_network_list.return_value = []
        self.mock_is_extension_supported.return_value = True
        self.mock_is_feature_available.return_value = True

        ret_val = api.neutron.network_list_for_tenant(
            self.request, tenant_id, include_pre_auto_allocate=True)

        self.assertEqual(1, len(ret_val))
        self.assertIsInstance(ret_val[0], api.neutron.PreAutoAllocateNetwork)
        self.assertEqual(api.neutron.AUTO_ALLOCATE_ID, ret_val[0].id)

        self.assertEqual(2, self.mock_network_list.call_count)
        self.mock_network_list.assert_has_calls([
            mock.call(test.IsHttpRequest(), tenant_id=tenant_id,
                      shared=False),
            mock.call(test.IsHttpRequest(), shared=True),
        ])
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'auto-allocated-topology')
        self.mock_is_feature_available.assert_called_once_with(
            test.IsHttpRequest(),
            ('instance_description', 'auto_allocated_network'))

    @test.create_mocks({api.neutron: ['network_list']})
    def test_network_list_for_tenant_no_pre_auto_allocate_if_disabled(self):
        tenant_id = '1'
        self.mock_network_list.return_value = []

        ret_val = api.neutron.network_list_for_tenant(
            self.request, tenant_id, include_pre_auto_allocate=True)

        self.assertEqual(0, len(ret_val))

        self.assertEqual(2, self.mock_network_list.call_count)
        self.mock_network_list.assert_has_calls([
            mock.call(test.IsHttpRequest(), tenant_id=tenant_id,
                      shared=False),
            mock.call(test.IsHttpRequest(), shared=True),
        ])

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_network_get(self, mock_neutronclient):
        network = {'network': self.api_networks.first()}
        subnet = {'subnet': self.api_subnets.first()}
        subnetv6 = {'subnet': self.api_subnets.list()[1]}
        network_id = self.api_networks.first()['id']
        subnet_id = self.api_networks.first()['subnets'][0]
        subnetv6_id = self.api_networks.first()['subnets'][1]

        neutronclient = mock_neutronclient.return_value
        neutronclient.show_network.return_value = network
        neutronclient.show_subnet.side_effect = [subnet, subnetv6]

        ret_val = api.neutron.network_get(self.request, network_id)

        self.assertIsInstance(ret_val, api.neutron.Network)
        self.assertEqual(2, len(ret_val['subnets']))
        self.assertIsInstance(ret_val['subnets'][0], api.neutron.Subnet)
        neutronclient.show_network.assert_called_once_with(network_id)
        neutronclient.show_subnet.assert_has_calls([
            mock.call(subnet_id),
            mock.call(subnetv6_id),
        ])

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_network_get_with_subnet_get_notfound(self, mock_neutronclient):
        network = {'network': self.api_networks.first()}
        network_id = self.api_networks.first()['id']
        subnet_id = self.api_networks.first()['subnets'][0]

        neutronclient = mock_neutronclient.return_value
        neutronclient.show_network.return_value = network
        neutronclient.show_subnet.side_effect = neutron_exc.NotFound

        ret_val = api.neutron.network_get(self.request, network_id)
        self.assertIsInstance(ret_val, api.neutron.Network)
        self.assertEqual(2, len(ret_val['subnets']))
        self.assertNotIsInstance(ret_val['subnets'][0], api.neutron.Subnet)
        self.assertIsInstance(ret_val['subnets'][0], str)
        neutronclient.show_network.assert_called_once_with(network_id)
        neutronclient.show_subnet.assert_called_once_with(subnet_id)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_network_create(self, mock_neutronclient):
        network = {'network': self.api_networks.first()}
        form_data = {'network': {'name': 'net1',
                                 'tenant_id': self.request.user.project_id}}
        neutronclient = mock_neutronclient.return_value
        neutronclient.create_network.return_value = network

        ret_val = api.neutron.network_create(self.request, name='net1')

        self.assertIsInstance(ret_val, api.neutron.Network)
        neutronclient.create_network.assert_called_once_with(body=form_data)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_network_update(self, mock_neutronclient):
        network = {'network': self.api_networks.first()}
        network_id = self.api_networks.first()['id']

        neutronclient = mock_neutronclient.return_value
        form_data = {'network': {'name': 'net1'}}
        neutronclient.update_network.return_value = network

        ret_val = api.neutron.network_update(self.request, network_id,
                                             name='net1')

        self.assertIsInstance(ret_val, api.neutron.Network)
        neutronclient.update_network.assert_called_once_with(network_id,
                                                             body=form_data)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_network_delete(self, mock_neutronclient):
        network_id = self.api_networks.first()['id']

        neutronclient = mock_neutronclient.return_value
        neutronclient.delete_network.return_value = None

        api.neutron.network_delete(self.request, network_id)

        neutronclient.delete_network.assert_called_once_with(network_id)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_get_network_ip_availability(self, mock_neutronclient):
        network = {'network': self.api_networks.first()}
        mock_ip_availability = self.ip_availability.get()
        neutronclient = mock_neutronclient.return_value
        neutronclient.show_network_ip_availability.return_value = \
            mock_ip_availability

        ret_val = api.neutron.show_network_ip_availability(self.request,
                                                           network)

        self.assertIsInstance(ret_val, dict)
        neutronclient.show_network_ip_availability.assert_called_once_with(
            network)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_subnet_network_ip_availability(self, mock_neutronclient):
        network = {'network': self.api_networks.first()}
        mock_ip_availability = self.ip_availability.get()
        neutronclient = mock_neutronclient.return_value
        neutronclient.show_network_ip_availability.return_value = \
            mock_ip_availability

        ip_availability = api.neutron. \
            show_network_ip_availability(self.request, network)
        availabilities = ip_availability.get("network_ip_availability",
                                             {})
        ret_val = availabilities.get("subnet_ip_availability", [])

        self.assertIsInstance(ret_val, list)
        neutronclient.show_network_ip_availability.assert_called_once_with(
            network)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_subnet_list(self, mock_neutronclient):
        subnets = {'subnets': self.api_subnets.list()}

        neutronclient = mock_neutronclient.return_value
        neutronclient.list_subnets.return_value = subnets

        ret_val = api.neutron.subnet_list(self.request)

        for n in ret_val:
            self.assertIsInstance(n, api.neutron.Subnet)
        neutronclient.list_subnets.assert_called_once_with()

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_subnet_get(self, mock_neutronclient):
        subnet = {'subnet': self.api_subnets.first()}
        subnet_id = self.api_subnets.first()['id']

        neutronclient = mock_neutronclient.return_value
        neutronclient.show_subnet.return_value = subnet

        ret_val = api.neutron.subnet_get(self.request, subnet_id)

        self.assertIsInstance(ret_val, api.neutron.Subnet)
        neutronclient.show_subnet.assert_called_once_with(subnet_id)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_subnet_create(self, mock_neutronclient):
        subnet_data = self.api_subnets.first()
        params = {'network_id': subnet_data['network_id'],
                  'tenant_id': subnet_data['tenant_id'],
                  'name': subnet_data['name'],
                  'cidr': subnet_data['cidr'],
                  'ip_version': subnet_data['ip_version'],
                  'gateway_ip': subnet_data['gateway_ip']}

        neutronclient = mock_neutronclient.return_value
        neutronclient.create_subnet.return_value = {'subnet': subnet_data}

        ret_val = api.neutron.subnet_create(self.request, **params)

        self.assertIsInstance(ret_val, api.neutron.Subnet)
        neutronclient.create_subnet.assert_called_once_with(
            body={'subnet': params})

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_subnet_update(self, mock_neutronclient):
        subnet_data = self.api_subnets.first()
        subnet_id = subnet_data['id']
        params = {'name': subnet_data['name'],
                  'gateway_ip': subnet_data['gateway_ip']}

        neutronclient = mock_neutronclient.return_value
        neutronclient.update_subnet.return_value = {'subnet': subnet_data}

        ret_val = api.neutron.subnet_update(self.request, subnet_id, **params)

        self.assertIsInstance(ret_val, api.neutron.Subnet)
        neutronclient.update_subnet.assert_called_once_with(
            subnet_id, body={'subnet': params})

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_subnet_delete(self, mock_neutronclient):
        subnet_id = self.api_subnets.first()['id']

        neutronclient = mock_neutronclient.return_value
        neutronclient.delete_subnet.return_value = None

        api.neutron.subnet_delete(self.request, subnet_id)

        neutronclient.delete_subnet.assert_called_once_with(subnet_id)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_subnetpool_list(self, mock_neutronclient):
        subnetpools = {'subnetpools': self.api_subnetpools.list()}

        neutronclient = mock_neutronclient.return_value
        neutronclient.list_subnetpools.return_value = subnetpools

        ret_val = api.neutron.subnetpool_list(self.request)

        for n in ret_val:
            self.assertIsInstance(n, api.neutron.SubnetPool)
        neutronclient.list_subnetpools.assert_called_once_with()

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_subnetpool_get(self, mock_neutronclient):
        subnetpool = {'subnetpool': self.api_subnetpools.first()}
        subnetpool_id = self.api_subnetpools.first()['id']

        neutronclient = mock_neutronclient.return_value
        neutronclient.show_subnetpool.return_value = subnetpool

        ret_val = api.neutron.subnetpool_get(self.request, subnetpool_id)

        self.assertIsInstance(ret_val, api.neutron.SubnetPool)
        neutronclient.show_subnetpool.assert_called_once_with(subnetpool_id)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_subnetpool_create(self, mock_neutronclient):
        subnetpool_data = self.api_subnetpools.first()
        params = {'name': subnetpool_data['name'],
                  'prefixes': subnetpool_data['prefixes'],
                  'tenant_id': subnetpool_data['tenant_id']}

        neutronclient = mock_neutronclient.return_value
        neutronclient.create_subnetpool.return_value = {'subnetpool':
                                                        subnetpool_data}

        ret_val = api.neutron.subnetpool_create(self.request, **params)

        self.assertIsInstance(ret_val, api.neutron.SubnetPool)
        neutronclient.create_subnetpool.assert_called_once_with(
            body={'subnetpool': params})

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_subnetpool_update(self, mock_neutronclient):
        subnetpool_data = self.api_subnetpools.first()
        subnetpool_id = subnetpool_data['id']
        params = {'name': subnetpool_data['name'],
                  'prefixes': subnetpool_data['prefixes']}

        neutronclient = mock_neutronclient.return_value
        neutronclient.update_subnetpool.return_value = {'subnetpool':
                                                        subnetpool_data}

        ret_val = api.neutron.subnetpool_update(self.request, subnetpool_id,
                                                **params)

        self.assertIsInstance(ret_val, api.neutron.SubnetPool)
        neutronclient.update_subnetpool.assert_called_once_with(
            subnetpool_id, body={'subnetpool': params})

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_subnetpool_delete(self, mock_neutronclient):
        subnetpool_id = self.api_subnetpools.first()['id']

        neutronclient = mock_neutronclient.return_value
        neutronclient.delete_subnetpool.return_value = None

        api.neutron.subnetpool_delete(self.request, subnetpool_id)

        neutronclient.delete_subnetpool.assert_called_once_with(subnetpool_id)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_port_list(self, mock_neutronclient):
        ports = {'ports': self.api_ports.list()}

        neutronclient = mock_neutronclient.return_value
        neutronclient.list_ports.return_value = ports

        ret_val = api.neutron.port_list(self.request)

        for p in ret_val:
            self.assertIsInstance(p, api.neutron.Port)
        neutronclient.list_ports.assert_called_once_with()

    @mock.patch.object(api.neutron, 'is_extension_supported')
    @mock.patch.object(api.neutron, 'neutronclient')
    def test_port_list_with_trunk_types(
            self, mock_neutronclient, mock_is_extension_supported):
        ports = self.api_tp_ports.list()
        trunks = self.api_tp_trunks.list()

        # list_extensions is decorated with memoized_with_request, so
        # neutronclient() is not called. We need to mock it separately.
        mock_is_extension_supported.return_value = True  # trunk

        neutronclient = mock_neutronclient.return_value
        neutronclient.list_ports.return_value = {'ports': ports}
        neutronclient.list_trunks.return_value = {'trunks': trunks}

        expected_parent_port_ids = set()
        expected_subport_ids = set()
        for trunk in trunks:
            expected_parent_port_ids.add(trunk['port_id'])
            expected_subport_ids |= set([p['port_id'] for p
                                         in trunk['sub_ports']])
        expected_normal_port_ids = ({p['id'] for p in ports} -
                                    expected_parent_port_ids -
                                    expected_subport_ids)

        ret_val = api.neutron.port_list_with_trunk_types(self.request)

        self.assertEqual(len(ports), len(ret_val))

        parent_port_ids = {p.id for p in ret_val
                           if isinstance(p, api.neutron.PortTrunkParent)}
        subport_ids = {p.id for p in ret_val
                       if isinstance(p, api.neutron.PortTrunkSubport)}
        normal_port_ids = ({p.id for p in ret_val} -
                           parent_port_ids - subport_ids)
        self.assertEqual(expected_parent_port_ids, parent_port_ids)
        self.assertEqual(expected_subport_ids, subport_ids)
        self.assertEqual(expected_normal_port_ids, normal_port_ids)

        mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'trunk')
        neutronclient.list_ports.assert_called_once_with()
        neutronclient.list_trunks.assert_called_once_with()

    @mock.patch.object(api.neutron, 'is_extension_supported')
    @mock.patch.object(api.neutron, 'neutronclient')
    def test_port_list_with_trunk_types_without_trunk_extension(
            self, mock_neutronclient, mock_is_extension_supported):
        ports = self.api_tp_ports.list()

        # list_extensions is decorated with memoized_with_request,
        # the simpliest way is to mock it directly.
        mock_is_extension_supported.return_value = False  # trunk

        neutronclient = mock_neutronclient.return_value
        neutronclient.list_ports.return_value = {'ports': ports}

        ret_val = api.neutron.port_list_with_trunk_types(self.request)

        self.assertEqual(len(ports), len(ret_val))
        self.assertEqual(set(p['id'] for p in ports),
                         set(p.id for p in ret_val))
        # When trunk extension is disabled, all returned values should be
        # instances of Port class.
        self.assertTrue(all(isinstance(p, api.neutron.Port) for p in ret_val))

        mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'trunk')
        neutronclient.list_ports.assert_called_once_with()

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_port_get(self, mock_neutronclient):
        port = {'port': self.api_ports.first()}
        port_id = self.api_ports.first()['id']

        neutronclient = mock_neutronclient.return_value
        neutronclient.show_port.return_value = port

        ret_val = api.neutron.port_get(self.request, port_id)

        self.assertIsInstance(ret_val, api.neutron.Port)
        neutronclient.show_port.assert_called_once_with(port_id)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_port_create(self, mock_neutronclient):
        port = {'port': self.api_ports.first()}
        params = {'network_id': port['port']['network_id'],
                  'tenant_id': port['port']['tenant_id'],
                  'name': port['port']['name'],
                  'device_id': port['port']['device_id']}

        neutronclient = mock_neutronclient.return_value
        neutronclient.create_port.return_value = port

        ret_val = api.neutron.port_create(self.request, **params)

        self.assertIsInstance(ret_val, api.neutron.Port)
        self.assertEqual(api.neutron.Port(port['port']).id, ret_val.id)
        neutronclient.create_port.assert_called_once_with(
            body={'port': params})

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_port_update(self, mock_neutronclient):
        port_data = self.api_ports.first()
        port_id = port_data['id']
        params = {'name': port_data['name'],
                  'device_id': port_data['device_id']}

        neutronclient = mock_neutronclient.return_value
        neutronclient.update_port.return_value = {'port': port_data}

        ret_val = api.neutron.port_update(self.request, port_id, **params)

        self.assertIsInstance(ret_val, api.neutron.Port)
        self.assertEqual(api.neutron.Port(port_data).id, ret_val.id)
        neutronclient.update_port.assert_called_once_with(
            port_id, body={'port': params})

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_port_delete(self, mock_neutronclient):
        port_id = self.api_ports.first()['id']

        neutronclient = mock_neutronclient.return_value
        neutronclient.delete_port.return_value = None

        api.neutron.port_delete(self.request, port_id)

        neutronclient.delete_port.assert_called_once_with(port_id)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_trunk_list(self, mock_neutronclient):
        trunks = {'trunks': self.api_trunks.list()}
        neutron_client = mock_neutronclient.return_value
        neutron_client.list_trunks.return_value = trunks

        ret_val = api.neutron.trunk_list(self.request)

        for t in ret_val:
            self.assertIsInstance(t, api.neutron.Trunk)
        neutron_client.list_trunks.assert_called_once_with()

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_trunk_show(self, mock_neutronclient):
        trunk = {'trunk': self.api_trunks.first()}
        trunk_id = self.api_trunks.first()['id']

        neutron_client = mock_neutronclient.return_value
        neutron_client.show_trunk.return_value = trunk

        ret_val = api.neutron.trunk_show(self.request, trunk_id)

        self.assertIsInstance(ret_val, api.neutron.Trunk)
        neutron_client.show_trunk.assert_called_once_with(trunk_id)

    def test_trunk_object(self):
        trunk = self.api_trunks.first().copy()
        obj = api.neutron.Trunk(trunk)
        self.assertEqual(0, obj.subport_count)
        trunk_dict = obj.to_dict()
        self.assertIsInstance(trunk_dict, dict)
        self.assertEqual(trunk['name'], trunk_dict['name_or_id'])
        self.assertEqual(0, trunk_dict['subport_count'])

        trunk['name'] = ''  # to test name_or_id
        trunk['sub_ports'] = [uuidutils.generate_uuid() for i in range(2)]
        obj = api.neutron.Trunk(trunk)
        self.assertEqual(2, obj.subport_count)
        trunk_dict = obj.to_dict()
        self.assertEqual(obj.name_or_id, trunk_dict['name_or_id'])
        self.assertEqual(2, trunk_dict['subport_count'])

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_trunk_create(self, mock_neutronclient):
        trunk = {'trunk': self.api_trunks.first()}
        params = {'name': trunk['trunk']['name'],
                  'port_id': trunk['trunk']['port_id'],
                  'project_id': trunk['trunk']['project_id']}

        neutronclient = mock_neutronclient.return_value
        neutronclient.create_trunk.return_value = trunk

        ret_val = api.neutron.trunk_create(self.request, **params)

        self.assertIsInstance(ret_val, api.neutron.Trunk)
        self.assertEqual(api.neutron.Trunk(trunk['trunk']).id, ret_val.id)
        neutronclient.create_trunk.assert_called_once_with(
            body={'trunk': params})

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_trunk_delete(self, mock_neutronclient):
        trunk_id = self.api_trunks.first()['id']

        neutronclient = mock_neutronclient.return_value
        neutronclient.delete_trunk.return_value = None

        api.neutron.trunk_delete(self.request, trunk_id)

        neutronclient.delete_trunk.assert_called_once_with(trunk_id)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_trunk_update_details(self, mock_neutronclient):
        trunk_data = self.api_trunks.first()
        trunk_id = trunk_data['id']
        old_trunk = {'name': trunk_data['name'],
                     'description': trunk_data['description'],
                     'id': trunk_data['id'],
                     'port_id': trunk_data['port_id'],
                     'admin_state_up': trunk_data['admin_state_up']}
        new_trunk = {'name': 'foo',
                     'description': trunk_data['description'],
                     'id': trunk_data['id'],
                     'port_id': trunk_data['port_id'],
                     'admin_state_up': trunk_data['admin_state_up']}

        neutronclient = mock_neutronclient.return_value
        neutronclient.update_trunk.return_value = {'trunk': new_trunk}

        ret_val = api.neutron.trunk_update(self.request, trunk_id,
                                           old_trunk, new_trunk)

        self.assertIsInstance(ret_val, api.neutron.Trunk)
        self.assertEqual(api.neutron.Trunk(trunk_data).id, ret_val.id)
        self.assertEqual(ret_val.name, new_trunk['name'])
        neutronclient.update_trunk.assert_called_once_with(
            trunk_id, body={'trunk': {'name': 'foo'}})

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_trunk_update_add_subports(self, mock_neutronclient):
        trunk_data = self.api_trunks.first()
        trunk_id = trunk_data['id']
        old_trunk = {'name': trunk_data['name'],
                     'description': trunk_data['description'],
                     'id': trunk_data['id'],
                     'port_id': trunk_data['port_id'],
                     'sub_ports': trunk_data['sub_ports'],
                     'admin_state_up': trunk_data['admin_state_up']}
        new_trunk = {'name': trunk_data['name'],
                     'description': trunk_data['description'],
                     'id': trunk_data['id'],
                     'port_id': trunk_data['port_id'],
                     'sub_ports': [
                         {'port_id': 1,
                          'segmentation_id': 100,
                          'segmentation_type': 'vlan'}],
                     'admin_state_up': trunk_data['admin_state_up']}

        neutronclient = mock_neutronclient.return_value
        neutronclient.trunk_add_subports.return_value = {'trunk': new_trunk}

        ret_val = api.neutron.trunk_update(self.request, trunk_id,
                                           old_trunk, new_trunk)

        self.assertIsInstance(ret_val, api.neutron.Trunk)
        self.assertEqual(api.neutron.Trunk(trunk_data).id, ret_val.trunk['id'])
        self.assertEqual(ret_val.trunk['sub_ports'], new_trunk['sub_ports'])
        neutronclient.trunk_add_subports.assert_called_once_with(
            trunk_id,
            body={'sub_ports': [{'port_id': 1, 'segmentation_id': 100,
                                 'segmentation_type': 'vlan'}]}
        )

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_trunk_update_remove_subports(self, mock_neutronclient):
        trunk_data = self.api_trunks.first()
        trunk_id = trunk_data['id']
        old_trunk = {'name': trunk_data['name'],
                     'description': trunk_data['description'],
                     'id': trunk_data['id'],
                     'port_id': trunk_data['port_id'],
                     'sub_ports': [
                         {'port_id': 1,
                          'segmentation_id': 100,
                          'segmentation_type': 'vlan'}],
                     'admin_state_up': trunk_data['admin_state_up']}
        new_trunk = {'name': trunk_data['name'],
                     'description': trunk_data['description'],
                     'id': trunk_data['id'],
                     'port_id': trunk_data['port_id'],
                     'sub_ports': [],
                     'admin_state_up': trunk_data['admin_state_up']}

        neutronclient = mock_neutronclient.return_value
        neutronclient.trunk_remove_subports.return_value = {'trunk': new_trunk}

        ret_val = api.neutron.trunk_update(self.request, trunk_id,
                                           old_trunk, new_trunk)

        self.assertIsInstance(ret_val, api.neutron.Trunk)
        self.assertEqual(api.neutron.Trunk(trunk_data).id, ret_val.trunk['id'])
        self.assertEqual(ret_val.trunk['sub_ports'], new_trunk['sub_ports'])
        neutronclient.trunk_remove_subports.assert_called_once_with(
            trunk_id,
            body={'sub_ports': [{'port_id':
                                 old_trunk['sub_ports'][0]['port_id']}]}
        )

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_router_list(self, mock_neutronclient):
        routers = {'routers': self.api_routers.list()}

        neutronclient = mock_neutronclient.return_value
        neutronclient.list_routers.return_value = routers

        ret_val = api.neutron.router_list(self.request)

        for n in ret_val:
            self.assertIsInstance(n, api.neutron.Router)
        neutronclient.list_routers.assert_called_once_with()

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_router_get(self, mock_neutronclient):
        router = {'router': self.api_routers.first()}
        router_id = self.api_routers.first()['id']

        neutronclient = mock_neutronclient.return_value
        neutronclient.show_router.return_value = router

        ret_val = api.neutron.router_get(self.request, router_id)

        self.assertIsInstance(ret_val, api.neutron.Router)
        neutronclient.show_router.assert_called_once_with(router_id)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_router_create(self, mock_neutronclient):
        router = {'router': self.api_routers.first()}

        neutronclient = mock_neutronclient.return_value
        form_data = {'router': {'name': 'router1',
                                'tenant_id': self.request.user.project_id}}
        neutronclient.create_router.return_value = router

        ret_val = api.neutron.router_create(self.request, name='router1')

        self.assertIsInstance(ret_val, api.neutron.Router)
        neutronclient.create_router.assert_called_once_with(body=form_data)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_router_delete(self, mock_neutronclient):
        router_id = self.api_routers.first()['id']

        neutronclient = mock_neutronclient.return_value
        neutronclient.delete_router.return_value = None

        api.neutron.router_delete(self.request, router_id)

        neutronclient.delete_router.assert_called_once_with(router_id)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_router_add_interface(self, mock_neutronclient):
        subnet_id = self.api_subnets.first()['id']
        router_id = self.api_routers.first()['id']

        neutronclient = mock_neutronclient.return_value
        form_data = {'subnet_id': subnet_id}
        neutronclient.add_interface_router.return_value = None

        api.neutron.router_add_interface(
            self.request, router_id, subnet_id=subnet_id)

        neutronclient.add_interface_router.assert_called_once_with(router_id,
                                                                   form_data)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_router_remove_interface(self, mock_neutronclient):
        router_id = self.api_routers.first()['id']
        fake_port = self.api_ports.first()['id']

        neutronclient = mock_neutronclient.return_value
        neutronclient.remove_interface_router.return_value = None

        api.neutron.router_remove_interface(
            self.request, router_id, port_id=fake_port)

        neutronclient.remove_interface_router.assert_called_once_with(
            router_id, {'port_id': fake_port})

    # Mocking neutronclient() does not work because api.neutron.list_extensions
    # is decorated with memoized_with_request, so we need to mock
    # neutronclient.v2_0.client directly.
    @mock.patch('neutronclient.v2_0.client.Client.list_extensions')
    def test_is_extension_supported(self, mock_list_extensions):
        extensions = self.api_extensions.list()
        mock_list_extensions.return_value = {'extensions': extensions}
        self.assertTrue(
            api.neutron.is_extension_supported(self.request, 'quotas'))
        self.assertFalse(
            api.neutron.is_extension_supported(self.request, 'doesntexist'))

        mock_list_extensions.assert_called_once_with()

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_router_static_route_list(self, mock_neutronclient):
        router = {'router': self.api_routers_with_routes.first()}
        router_id = self.api_routers_with_routes.first()['id']

        neutronclient = mock_neutronclient.return_value
        neutronclient.show_router.return_value = router

        ret_val = api.neutron.router_static_route_list(self.request, router_id)

        self.assertIsInstance(ret_val[0], api.neutron.RouterStaticRoute)
        neutronclient.show_router.assert_called_once_with(router_id)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_router_static_route_remove(self, mock_neutronclient):
        router = {'router': self.api_routers_with_routes.first()}
        router_id = self.api_routers_with_routes.first()['id']
        post_router = copy.deepcopy(router)
        route = api.neutron.RouterStaticRoute(post_router['router']
                                              ['routes'].pop())

        neutronclient = mock_neutronclient.return_value
        neutronclient.show_router.return_value = router
        neutronclient.update_router.return_value = post_router

        api.neutron.router_static_route_remove(self.request,
                                               router_id, route.id)

        neutronclient.show_router.assert_called_once_with(router_id)
        body = {'router': {'routes': post_router['router']['routes']}}
        neutronclient.update_router.assert_called_once_with(
            router_id, body=body)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_router_static_route_add(self, mock_neutronclient):
        router = {'router': self.api_routers_with_routes.first()}
        router_id = self.api_routers_with_routes.first()['id']
        post_router = copy.deepcopy(router)
        route = {'nexthop': '10.0.0.5', 'destination': '40.0.1.0/24'}
        post_router['router']['routes'].insert(0, route)
        body = {'router': {'routes': post_router['router']['routes']}}

        neutronclient = mock_neutronclient.return_value
        neutronclient.show_router.return_value = router
        neutronclient.update_router.return_value = post_router

        api.neutron.router_static_route_add(self.request, router_id, route)

        neutronclient.show_router.assert_called_once_with(router_id)
        neutronclient.update_router.assert_called_once_with(router_id,
                                                            body=body)

    # NOTE(amotoki): "dvr" permission tests check most of
    # get_feature_permission features.
    # These tests are not specific to "dvr" extension.
    # Please be careful if you drop "dvr" extension in future.

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_distributed_router':
                                                  True},
                       POLICY_CHECK_FUNCTION=None)
    @test.create_mocks({api.neutron: ('is_extension_supported',)})
    def _test_get_dvr_permission_dvr_supported(self, dvr_enabled):
        self.mock_is_extension_supported.return_value = dvr_enabled
        self.assertEqual(dvr_enabled,
                         api.neutron.get_feature_permission(self.request,
                                                            'dvr', 'get'))
        self.mock_is_extension_supported.assert_called_once_with(
            self.request, 'dvr')

    def test_get_dvr_permission_dvr_supported(self):
        self._test_get_dvr_permission_dvr_supported(dvr_enabled=True)

    def test_get_dvr_permission_dvr_not_supported(self):
        self._test_get_dvr_permission_dvr_supported(dvr_enabled=False)

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_distributed_router':
                                                  True},
                       POLICY_CHECK_FUNCTION='openstack_auth.policy.check')
    @test.create_mocks({api.neutron: ('is_extension_supported',),
                        policy: ('check',)})
    def _test_get_dvr_permission_with_policy_check(self, policy_check_allowed,
                                                   operation):
        if operation == "create":
            role = (("network", "create_router:distributed"),)
        elif operation == "get":
            role = (("network", "get_router:distributed"),)
        self.mock_check.return_value = policy_check_allowed
        self.mock_is_extension_supported.return_value = policy_check_allowed

        self.assertEqual(policy_check_allowed,
                         api.neutron.get_feature_permission(self.request,
                                                            'dvr', operation))

        self.mock_check.assert_called_once_with(role, self.request)
        if policy_check_allowed:
            self.mock_is_extension_supported.assert_called_once_with(
                self.request, 'dvr')
        else:
            self.mock_is_extension_supported.assert_not_called()

    def test_get_dvr_permission_with_policy_check_allowed(self):
        self._test_get_dvr_permission_with_policy_check(True, "get")

    def test_get_dvr_permission_with_policy_check_disallowed(self):
        self._test_get_dvr_permission_with_policy_check(False, "get")

    def test_get_dvr_permission_create_with_policy_check_allowed(self):
        self._test_get_dvr_permission_with_policy_check(True, "create")

    def test_get_dvr_permission_create_with_policy_check_disallowed(self):
        self._test_get_dvr_permission_with_policy_check(False, "create")

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_distributed_router':
                                                  False})
    def test_get_dvr_permission_dvr_disabled_by_config(self):
        self.assertFalse(api.neutron.get_feature_permission(self.request,
                                                            'dvr', 'get'))

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_distributed_router':
                                                  True},
                       POLICY_CHECK_FUNCTION='openstack_auth.policy.check')
    def test_get_dvr_permission_dvr_unsupported_operation(self):
        self.assertRaises(ValueError,
                          api.neutron.get_feature_permission,
                          self.request, 'dvr', 'unSupported')

    @override_settings(OPENSTACK_NEUTRON_NETWORK={})
    def test_get_dvr_permission_dvr_default_config(self):
        self.assertFalse(api.neutron.get_feature_permission(self.request,
                                                            'dvr', 'get'))

    @override_settings(OPENSTACK_NEUTRON_NETWORK={})
    def test_get_dvr_permission_router_ha_default_config(self):
        self.assertFalse(api.neutron.get_feature_permission(self.request,
                                                            'l3-ha', 'get'))

    # NOTE(amotoki): Most of get_feature_permission are checked by "dvr" check
    # above. l3-ha check only checks l3-ha specific code.

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_ha_router': True},
                       POLICY_CHECK_FUNCTION='openstack_auth.policy.check')
    @test.create_mocks({api.neutron: ('is_extension_supported',),
                        policy: ('check',)})
    def _test_get_router_ha_permission_with_policy_check(self, ha_enabled):
        role = (("network", "create_router:ha"),)
        self.mock_check.return_value = True
        self.mock_is_extension_supported.return_value = ha_enabled

        self.assertEqual(ha_enabled,
                         api.neutron.get_feature_permission(self.request,
                                                            'l3-ha', 'create'))

        self.mock_check.assert_called_once_with(role, self.request)
        self.mock_is_extension_supported.assert_called_once_with(self.request,
                                                                 'l3-ha')

    def test_get_router_ha_permission_with_l3_ha_extension(self):
        self._test_get_router_ha_permission_with_policy_check(True)

    def test_get_router_ha_permission_without_l3_ha_extension(self):
        self._test_get_router_ha_permission_with_policy_check(False)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_list_resources_with_long_filters(self, mock_neutronclient):
        # In this tests, port_list is called with id=[10 port ID]
        # filter. It generates about 40*10 char length URI.
        # Each port ID is converted to "id=<UUID>&" in URI and
        # it means 40 chars (len(UUID)=36).
        # If excess length is 220, it means 400-220=180 chars
        # can be sent in the first request.
        # As a result three API calls with 4, 4, 2 port ID
        # are expected.

        ports = [{'id': uuidutils.generate_uuid(),
                  'name': 'port%s' % i,
                  'admin_state_up': True}
                 for i in range(10)]
        port_ids = tuple([port['id'] for port in ports])

        neutronclient = mock_neutronclient.return_value
        uri_len_exc = neutron_exc.RequestURITooLong(excess=220)
        list_ports_retval = [uri_len_exc]
        for i in range(0, 10, 4):
            list_ports_retval.append({'ports': ports[i:i + 4]})
        neutronclient.list_ports.side_effect = list_ports_retval

        ret_val = api.neutron.list_resources_with_long_filters(
            api.neutron.port_list, 'id', tuple(port_ids),
            request=self.request)
        self.assertEqual(10, len(ret_val))
        self.assertEqual(port_ids, tuple([p.id for p in ret_val]))

        expected_calls = []
        expected_calls.append(mock.call(id=tuple(port_ids)))
        for i in range(0, 10, 4):
            expected_calls.append(mock.call(id=tuple(port_ids[i:i + 4])))
        neutronclient.list_ports.assert_has_calls(expected_calls)

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_qos_policies_list(self, mock_neutronclient):
        exp_policies = self.qos_policies.list()
        api_qos_policies = {'policies': self.api_qos_policies.list()}

        neutronclient = mock_neutronclient.return_value
        neutronclient.list_qos_policies.return_value = api_qos_policies

        ret_val = api.neutron.policy_list(self.request)

        self.assertEqual(len(ret_val), len(exp_policies))
        self.assertIsInstance(ret_val[0], api.neutron.QoSPolicy)
        self.assertEqual(exp_policies[0].name, ret_val[0].name)
        neutronclient.list_qos_policies.assert_called_once_with()

    @mock.patch.object(api.neutron, 'neutronclient')
    def test_qos_policy_create(self, mock_neutronclient):
        qos_policy = self.api_qos_policies.first()
        post_data = {'policy': {'name': qos_policy['name']}}

        neutronclient = mock_neutronclient.return_value
        neutronclient.create_qos_policy.return_value = {'policy': qos_policy}

        ret_val = api.neutron.policy_create(self.request,
                                            name=qos_policy['name'])

        self.assertIsInstance(ret_val, api.neutron.QoSPolicy)
        self.assertEqual(qos_policy['name'], ret_val.name)
        neutronclient.create_qos_policy.assert_called_once_with(body=post_data)


class NeutronApiSecurityGroupTests(test.APIMockTestCase):

    def setUp(self):
        super(NeutronApiSecurityGroupTests, self).setUp()
        neutronclient = mock.patch.object(api.neutron, 'neutronclient').start()
        self.qclient = neutronclient.return_value
        self.sg_dict = dict([(sg['id'], sg['name']) for sg
                             in self.api_security_groups.list()])

    def _cmp_sg_rule(self, exprule, retrule):
        self.assertEqual(exprule['id'], retrule.id)
        self.assertEqual(exprule['security_group_id'],
                         retrule.parent_group_id)
        self.assertEqual(exprule['direction'],
                         retrule.direction)
        self.assertEqual(exprule['ethertype'],
                         retrule.ethertype)
        self.assertEqual(exprule['port_range_min'],
                         retrule.from_port)
        self.assertEqual(exprule['port_range_max'],
                         retrule.to_port,)
        if (exprule['remote_ip_prefix'] is None and
                exprule['remote_group_id'] is None):
            expcidr = ('::/0' if exprule['ethertype'] == 'IPv6'
                       else '0.0.0.0/0')
        else:
            expcidr = exprule['remote_ip_prefix']
        self.assertEqual(expcidr, retrule.ip_range.get('cidr'))
        self.assertEqual(self.sg_dict.get(exprule['remote_group_id']),
                         retrule.group.get('name'))

    def _cmp_sg(self, exp_sg, ret_sg):
        self.assertEqual(exp_sg['id'], ret_sg.id)
        self.assertEqual(exp_sg['name'], ret_sg.name)
        # When a SG has no rules, neutron API does not contain
        # 'security_group_rules' field, so .get() method needs to be used.
        exp_rules = exp_sg.get('security_group_rules', [])
        self.assertEqual(len(exp_rules), len(ret_sg.rules))
        for (exprule, retrule) in six.moves.zip(exp_rules, ret_sg.rules):
            self._cmp_sg_rule(exprule, retrule)

    def _test_security_group_list(self, **params):
        sgs = self.api_security_groups.list()
        q_params = {'tenant_id': self.request.user.tenant_id}
        # if tenant_id is specified, the passed tenant_id should be sent.
        q_params.update(params)
        # use deepcopy to ensure self.api_security_groups is not modified.
        self.qclient.list_security_groups.return_value = {'security_groups':
                                                          copy.deepcopy(sgs)}

        rets = api.neutron.security_group_list(self.request, **params)
        self.assertEqual(len(sgs), len(rets))
        for (exp, ret) in six.moves.zip(sgs, rets):
            self._cmp_sg(exp, ret)
        self.qclient.list_security_groups.assert_called_once_with(**q_params)

    def test_security_group_list(self):
        self._test_security_group_list()

    def test_security_group_list_with_params(self):
        self._test_security_group_list(name='sg1')

    def test_security_group_list_with_tenant_id(self):
        self._test_security_group_list(tenant_id='tenant1', name='sg1')

    def test_security_group_get(self):
        secgroup = self.api_security_groups.first()
        sg_ids = set([secgroup['id']] +
                     [rule['remote_group_id'] for rule
                      in secgroup['security_group_rules']
                      if rule['remote_group_id']])
        related_sgs = [sg for sg in self.api_security_groups.list()
                       if sg['id'] in sg_ids]
        # use deepcopy to ensure self.api_security_groups is not modified.
        self.qclient.show_security_group.return_value = \
            {'security_group': copy.deepcopy(secgroup)}
        self.qclient.list_security_groups.return_value = \
            {'security_groups': related_sgs}

        ret = api.neutron.security_group_get(self.request, secgroup['id'])

        self._cmp_sg(secgroup, ret)
        self.qclient.show_security_group.assert_called_once_with(
            secgroup['id'])
        self.qclient.list_security_groups.assert_called_once_with(
            id=sg_ids, fields=['id', 'name'])

    def test_security_group_create(self):
        secgroup = self.api_security_groups.list()[1]
        body = {'security_group':
                {'name': secgroup['name'],
                 'description': secgroup['description'],
                 'tenant_id': self.request.user.project_id}}
        self.qclient.create_security_group.return_value = \
            {'security_group': copy.deepcopy(secgroup)}

        ret = api.neutron.security_group_create(self.request, secgroup['name'],
                                                secgroup['description'])

        self._cmp_sg(secgroup, ret)
        self.qclient.create_security_group.assert_called_once_with(body)

    def test_security_group_update(self):
        secgroup = self.api_security_groups.list()[1]
        secgroup = copy.deepcopy(secgroup)
        secgroup['name'] = 'newname'
        secgroup['description'] = 'new description'
        body = {'security_group':
                {'name': secgroup['name'],
                 'description': secgroup['description']}}
        self.qclient.update_security_group.return_value = {'security_group':
                                                           secgroup}

        ret = api.neutron.security_group_update(self.request,
                                                secgroup['id'],
                                                secgroup['name'],
                                                secgroup['description'])
        self._cmp_sg(secgroup, ret)
        self.qclient.update_security_group.assert_called_once_with(
            secgroup['id'], body)

    def test_security_group_delete(self):
        secgroup = self.api_security_groups.first()
        self.qclient.delete_security_group.return_value = None

        api.neutron.security_group_delete(self.request, secgroup['id'])

        self.qclient.delete_security_group.assert_called_once_with(
            secgroup['id'])

    def test_security_group_rule_create(self):
        self._test_security_group_rule_create(with_desc=True)

    def test_security_group_rule_create_without_desc(self):
        self._test_security_group_rule_create(with_desc=False)

    def test_security_group_rule_create_with_custom_protocol(self):
        self._test_security_group_rule_create(custom_ip_proto=True)

    def _test_security_group_rule_create(self, with_desc=False,
                                         custom_ip_proto=False):
        if custom_ip_proto:
            sg_rule = [r for r in self.api_security_group_rules.list()
                       if r['protocol'] == '99'][0]
        else:
            sg_rule = [r for r in self.api_security_group_rules.list()
                       if r['protocol'] == 'tcp' and r['remote_ip_prefix']][0]
        sg_id = sg_rule['security_group_id']
        secgroup = [sg for sg in self.api_security_groups.list()
                    if sg['id'] == sg_id][0]

        post_rule = copy.deepcopy(sg_rule)
        del post_rule['id']
        del post_rule['tenant_id']
        if not with_desc:
            del post_rule['description']
        post_body = {'security_group_rule': post_rule}
        self.qclient.create_security_group_rule.return_value = \
            {'security_group_rule': copy.deepcopy(sg_rule)}
        self.qclient.list_security_groups.return_value = \
            {'security_groups': [copy.deepcopy(secgroup)]}

        if with_desc:
            description = sg_rule['description']
        else:
            description = None

        ret = api.neutron.security_group_rule_create(
            self.request, sg_rule['security_group_id'],
            sg_rule['direction'], sg_rule['ethertype'], sg_rule['protocol'],
            sg_rule['port_range_min'], sg_rule['port_range_max'],
            sg_rule['remote_ip_prefix'], sg_rule['remote_group_id'],
            description)

        self._cmp_sg_rule(sg_rule, ret)
        self.qclient.create_security_group_rule.assert_called_once_with(
            post_body)
        self.qclient.list_security_groups.assert_called_once_with(
            id=set([sg_id]), fields=['id', 'name'])

    def test_security_group_rule_delete(self):
        sg_rule = self.api_security_group_rules.first()
        self.qclient.delete_security_group_rule.return_value = None

        api.neutron.security_group_rule_delete(self.request, sg_rule['id'])

        self.qclient.delete_security_group_rule.assert_called_once_with(
            sg_rule['id'])

    def _get_instance(self, cur_sg_ids):
        instance_port = [p for p in self.api_ports.list()
                         if p['device_owner'].startswith('compute:')][0]
        instance_id = instance_port['device_id']
        # Emulate an instance with two ports
        instance_ports = []
        for _i in range(2):
            p = copy.deepcopy(instance_port)
            p['id'] = uuidutils.generate_uuid()
            p['security_groups'] = cur_sg_ids
            instance_ports.append(p)
        return (instance_id, instance_ports)

    def test_server_security_groups(self):
        cur_sg_ids = [sg['id'] for sg in self.api_security_groups.list()[:2]]
        instance_id, instance_ports = self._get_instance(cur_sg_ids)
        self.qclient.list_ports.return_value = {'ports': instance_ports}
        secgroups = copy.deepcopy(self.api_security_groups.list())
        self.qclient.list_security_groups.return_value = \
            {'security_groups': secgroups}

        api.neutron.server_security_groups(self.request, instance_id)

        self.qclient.list_ports.assert_called_once_with(device_id=instance_id)
        self.qclient.list_security_groups.assert_called_once_with(
            id=set(cur_sg_ids))

    def test_server_update_security_groups(self):
        cur_sg_ids = [self.api_security_groups.first()['id']]
        new_sg_ids = [sg['id'] for sg in self.api_security_groups.list()[:2]]
        instance_id, instance_ports = self._get_instance(cur_sg_ids)

        self.qclient.list_ports.return_value = {'ports': instance_ports}
        self.qclient.update_port.side_effect = \
            [{'port': p} for p in instance_ports]

        api.neutron.server_update_security_groups(
            self.request, instance_id, new_sg_ids)

        self.qclient.list_ports.assert_called_once_with(device_id=instance_id)
        body = {'port': {'security_groups': new_sg_ids}}
        expected_calls = [mock.call(p['id'], body=body)
                          for p in instance_ports]
        self.qclient.update_port.assert_has_calls(expected_calls)


class NeutronApiFloatingIpTests(test.APIMockTestCase):

    def setUp(self):
        super(NeutronApiFloatingIpTests, self).setUp()
        neutronclient = mock.patch.object(api.neutron, 'neutronclient').start()
        self.qclient = neutronclient.return_value

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_router': True})
    def test_floating_ip_supported(self):
        self.assertTrue(api.neutron.floating_ip_supported(self.request))

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_router': False})
    def test_floating_ip_supported_false(self):
        self.assertFalse(api.neutron.floating_ip_supported(self.request))

    def test_floating_ip_pools_list(self):
        search_opts = {'router:external': True}
        ext_nets = [n for n in self.api_networks.list()
                    if n['router:external']]
        self.qclient.list_networks.return_value = {'networks': ext_nets}

        rets = api.neutron.floating_ip_pools_list(self.request)
        for attr in ['id', 'name']:
            self.assertEqual([p[attr] for p in ext_nets],
                             [getattr(p, attr) for p in rets])
        self.qclient.list_networks.assert_called_once_with(**search_opts)

    def test_floating_ip_list(self):
        fips = self.api_floating_ips.list()
        filters = {'tenant_id': self.request.user.tenant_id}

        self.qclient.list_floatingips.return_value = {'floatingips': fips}
        self.qclient.list_ports.return_value = {'ports': self.api_ports.list()}

        rets = api.neutron.tenant_floating_ip_list(self.request)

        assoc_port = self.api_ports.list()[1]
        self.assertEqual(len(fips), len(rets))
        for ret, exp in zip(rets, fips):
            for attr in ['id', 'ip', 'pool', 'fixed_ip', 'port_id']:
                self.assertEqual(exp[attr], getattr(ret, attr))
            if exp['port_id']:
                dev_id = assoc_port['device_id'] if exp['port_id'] else None
                self.assertEqual(dev_id, ret.instance_id)
                self.assertEqual('compute', ret.instance_type)
            else:
                self.assertIsNone(ret.instance_id)
                self.assertIsNone(ret.instance_type)
        self.qclient.list_floatingips.assert_called_once_with(**filters)
        self.qclient.list_ports.assert_called_once_with(**filters)

    def test_floating_ip_list_all_tenants(self):
        fips = self.api_floating_ips.list()
        self.qclient.list_floatingips.return_value = {'floatingips': fips}
        self.qclient.list_ports.return_value = {'ports': self.api_ports.list()}

        fip_manager = api.neutron.FloatingIpManager(self.request)
        rets = fip_manager.list(all_tenants=True)

        assoc_port = self.api_ports.list()[1]
        self.assertEqual(len(fips), len(rets))
        for ret, exp in zip(rets, fips):
            for attr in ['id', 'ip', 'pool', 'fixed_ip', 'port_id']:
                self.assertEqual(getattr(ret, attr), exp[attr])
            if exp['port_id']:
                dev_id = assoc_port['device_id'] if exp['port_id'] else None
                self.assertEqual(dev_id, ret.instance_id)
                self.assertEqual('compute', ret.instance_type)
            else:
                self.assertIsNone(ret.instance_id)
                self.assertIsNone(ret.instance_type)
        self.qclient.list_floatingips.assert_called_once_with()
        self.qclient.list_ports.assert_called_once_with()

    def _test_floating_ip_get_associated(self, assoc_port, exp_instance_type):
        fip = self.api_floating_ips.list()[1]
        self.qclient.show_floatingip.return_value = {'floatingip': fip}
        self.qclient.show_port.return_value = {'port': assoc_port}

        ret = api.neutron.tenant_floating_ip_get(self.request, fip['id'])

        for attr in ['id', 'ip', 'pool', 'fixed_ip', 'port_id']:
            self.assertEqual(fip[attr], getattr(ret, attr))
        self.assertEqual(assoc_port['device_id'], ret.instance_id)
        self.assertEqual(exp_instance_type, ret.instance_type)
        self.qclient.show_floatingip.assert_called_once_with(fip['id'])
        self.qclient.show_port.assert_called_once_with(assoc_port['id'])

    def test_floating_ip_get_associated(self):
        assoc_port = self.api_ports.list()[1]
        self._test_floating_ip_get_associated(assoc_port, 'compute')

    def test_floating_ip_get_associated_with_loadbalancer_vip(self):
        assoc_port = copy.deepcopy(self.api_ports.list()[1])
        assoc_port['device_owner'] = 'neutron:LOADBALANCER'
        assoc_port['device_id'] = uuidutils.generate_uuid()
        assoc_port['name'] = 'vip-' + uuidutils.generate_uuid()
        self._test_floating_ip_get_associated(assoc_port, 'loadbalancer')

    def test_floating_ip_get_unassociated(self):
        fip = self.api_floating_ips.list()[0]

        self.qclient.show_floatingip.return_value = {'floatingip': fip}

        ret = api.neutron.tenant_floating_ip_get(self.request, fip['id'])

        for attr in ['id', 'ip', 'pool', 'fixed_ip', 'port_id']:
            self.assertEqual(fip[attr], getattr(ret, attr))
        self.assertIsNone(ret.instance_id)
        self.assertIsNone(ret.instance_type)
        self.qclient.show_floatingip.assert_called_once_with(fip['id'])

    def test_floating_ip_allocate(self):
        ext_nets = [n for n in self.api_networks.list()
                    if n['router:external']]
        ext_net = ext_nets[0]
        fip = self.api_floating_ips.first()
        self.qclient.create_floatingip.return_value = {'floatingip': fip}

        ret = api.neutron.tenant_floating_ip_allocate(self.request,
                                                      ext_net['id'])
        for attr in ['id', 'ip', 'pool', 'fixed_ip', 'port_id']:
            self.assertEqual(fip[attr], getattr(ret, attr))
        self.assertIsNone(ret.instance_id)
        self.assertIsNone(ret.instance_type)
        self.qclient.create_floatingip.assert_called_once_with(
            {'floatingip': {'floating_network_id': ext_net['id'],
                            'tenant_id': self.request.user.project_id}})

    def test_floating_ip_release(self):
        fip = self.api_floating_ips.first()
        self.qclient.delete_floatingip.return_value = None

        api.neutron.tenant_floating_ip_release(self.request, fip['id'])

        self.qclient.delete_floatingip.assert_called_once_with(fip['id'])

    def test_floating_ip_associate(self):
        fip = self.api_floating_ips.list()[1]
        assoc_port = self.api_ports.list()[1]
        ip_address = assoc_port['fixed_ips'][0]['ip_address']
        target_id = '%s_%s' % (assoc_port['id'], ip_address)
        params = {'port_id': assoc_port['id'],
                  'fixed_ip_address': ip_address}
        self.qclient.update_floatingip.return_value = None

        api.neutron.floating_ip_associate(self.request, fip['id'], target_id)

        self.qclient.update_floatingip.assert_called_once_with(
            fip['id'], {'floatingip': params})

    def test_floating_ip_disassociate(self):
        fip = self.api_floating_ips.list()[1]

        self.qclient.update_floatingip.return_value = None

        api.neutron.floating_ip_disassociate(self.request, fip['id'])

        self.qclient.update_floatingip.assert_called_once_with(
            fip['id'], {'floatingip': {'port_id': None}})

    def _get_target_id(self, port, ip=None, index=0):
        param = {'id': port['id'],
                 'addr': ip or port['fixed_ips'][index]['ip_address']}
        return '%(id)s_%(addr)s' % param

    def _get_target_name(self, port, ip=None):
        param = {'svrid': port['device_id'],
                 'addr': ip or port['fixed_ips'][0]['ip_address']}
        return 'server_%(svrid)s: %(addr)s' % param

    @override_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'enable_fip_topology_check': True,
        }
    )
    @mock.patch.object(api._nova, 'novaclient')
    def test_floating_ip_target_list(self, mock_novaclient):
        ports = self.api_ports.list()
        # Port on the first subnet is connected to a router
        # attached to external network in neutron_data.
        subnet_id = self.subnets.first().id
        shared_nets = [n for n in self.api_networks.list() if n['shared']]
        shared_subnet_ids = [s for n in shared_nets for s in n['subnets']]
        target_ports = []
        for p in ports:
            if p['device_owner'].startswith('network:'):
                continue
            port_subnets = [ip['subnet_id'] for ip in p['fixed_ips']]
            if not (subnet_id in port_subnets or
                    (set(shared_subnet_ids) & set(port_subnets))):
                continue
            for ip in p['fixed_ips']:
                if netaddr.IPAddress(ip['ip_address']).version != 4:
                    continue
                target_ports.append((
                    self._get_target_id(p, ip['ip_address']),
                    self._get_target_name(p, ip['ip_address'])))
        filters = {'tenant_id': self.request.user.tenant_id}
        self.qclient.list_ports.return_value = {'ports': ports}
        servers = self.servers.list()
        novaclient = mock_novaclient.return_value
        ver = mock.Mock(min_version='2.1', version='2.45')
        novaclient.versions.get_current.return_value = ver
        novaclient.servers.list.return_value = servers

        ext_nets = [n for n in self.api_networks.list()
                    if n['router:external']]
        list_networks_retvals = [{'networks': ext_nets},
                                 {'networks': shared_nets}]
        self.qclient.list_networks.side_effect = list_networks_retvals
        self.qclient.list_routers.return_value = {'routers':
                                                  self.api_routers.list()}
        shared_subs = [s for s in self.api_subnets.list()
                       if s['id'] in shared_subnet_ids]
        self.qclient.list_subnets.return_value = {'subnets': shared_subs}

        rets = api.neutron.floating_ip_target_list(self.request)

        self.assertEqual(len(target_ports), len(rets))
        for ret, exp in zip(rets, target_ports):
            pid, ip_address = ret.id.split('_', 1)
            self.assertEqual(4, netaddr.IPAddress(ip['ip_address']).version)
            self.assertEqual(exp[0], ret.id)
            self.assertEqual(exp[1], ret.name)

        self.qclient.list_ports.assert_called_once_with(**filters)
        novaclient.versions.get_current.assert_called_once_with()
        novaclient.servers.list.assert_called_once_with(
            False, {'project_id': self.request.user.tenant_id})
        self.qclient.list_networks.assert_has_calls([
            mock.call(**{'router:external': True}),
            mock.call(shared=True),
        ])
        self.qclient.list_routers.assert_called_once_with()
        self.qclient.list_subnets.assert_called_once_with()

    @mock.patch.object(api._nova, 'novaclient')
    def _test_target_floating_ip_port_by_instance(self, server, ports,
                                                  candidates, mock_novaclient):
        # list_ports and list_networks are called multiple times,
        # we prepare a list for return values.
        list_ports_retvals = []
        self.qclient.list_ports.side_effect = list_ports_retvals
        list_nets_retvals = []
        self.qclient.list_networks.side_effect = list_nets_retvals

        # _target_ports_by_instance()
        list_ports_retvals.append({'ports': candidates})

        # _get_reachable_subnets()
        ext_nets = [n for n in self.api_networks.list()
                    if n['router:external']]
        list_nets_retvals.append({'networks': ext_nets})
        self.qclient.list_routers.side_effect = [{'routers':
                                                  self.api_routers.list()}]
        rinfs = [p for p in ports
                 if p['device_owner'] in api.neutron.ROUTER_INTERFACE_OWNERS]
        list_ports_retvals.append({'ports': rinfs})
        shared_nets = [n for n in self.api_networks.list() if n['shared']]
        list_nets_retvals.append({'networks': shared_nets})
        shared_subnet_ids = [s for n in shared_nets for s in n['subnets']]
        shared_subs = [s for s in self.api_subnets.list()
                       if s['id'] in shared_subnet_ids]
        self.qclient.list_subnets.side_effect = [{'subnets': shared_subs}]

        # _get_server_name()
        novaclient = mock_novaclient.return_value
        ver = mock.Mock(min_version='2.1', version='2.45')
        novaclient.versions.get_current.return_value = ver
        novaclient.servers.get.return_value = server

        ret_val = api.neutron.floating_ip_target_list_by_instance(self.request,
                                                                  server.id)

        self.qclient.list_ports.assert_has_calls([
            mock.call(device_id=server.id),
            mock.call(device_owner=api.neutron.ROUTER_INTERFACE_OWNERS),
        ])
        self.qclient.list_networks.assert_has_calls([
            mock.call(**{'router:external': True}),
            mock.call(shared=True),
        ])
        self.qclient.list_routers.assert_called_once_with()
        self.qclient.list_subnets.assert_called_once_with()
        novaclient.versions.get_current.assert_called_once_with()
        novaclient.servers.get.assert_called_once_with(server.id)

        return ret_val

    def test_target_floating_ip_port_by_instance(self):
        server = self.servers.first()
        ports = self.api_ports.list()
        candidates = [p for p in ports if p['device_id'] == server.id]

        ret = self._test_target_floating_ip_port_by_instance(server, ports,
                                                             candidates)
        self.assertEqual(1, len(ret))
        ret_val = ret[0]
        self.assertEqual(self._get_target_id(candidates[0]), ret_val.id)
        self.assertEqual(candidates[0]['id'], ret_val.port_id)
        self.assertEqual(candidates[0]['device_id'], ret_val.instance_id)

    def test_target_floating_ip_port_by_instance_with_ipv6(self):
        server = self.servers.first()
        ports = self.api_ports.list()
        candidates = [p for p in ports if p['device_id'] == server.id]
        # Move the IPv6 entry first
        fixed_ips = candidates[0]['fixed_ips']
        candidates[0]['fixed_ips'] = [fixed_ips[1], fixed_ips[0]]
        # Check the first IP address is IPv6
        first_ip = candidates[0]['fixed_ips'][0]['ip_address']
        self.assertEqual(6, netaddr.IPAddress(first_ip).version)

        ret = self._test_target_floating_ip_port_by_instance(server, ports,
                                                             candidates)
        self.assertEqual(1, len(ret))
        ret_val = ret[0]
        self.assertEqual(self._get_target_id(candidates[0], index=1),
                         ret_val.id)
        self.assertEqual(candidates[0]['id'], ret_val.port_id)
        self.assertEqual(candidates[0]['device_id'], ret_val.instance_id)

    def _get_preloaded_targets(self):
        return [
            api.neutron.FloatingIpTarget(
                api.neutron.Port({'name': 'name11', 'id': 'id11',
                                  'device_id': 'id-vm1'}),
                '192.168.1.1', 'vm1'),
            api.neutron.FloatingIpTarget(
                api.neutron.Port({'name': 'name21', 'id': 'id21',
                                  'device_id': 'id-vm2'}),
                '172.16.1.1', 'vm2'),
            api.neutron.FloatingIpTarget(
                api.neutron.Port({'name': 'name22', 'id': 'id22',
                                  'device_id': 'id-vm2'}),
                '10.11.12.13', 'vm3'),
        ]

    def test_target_floating_ip_port_by_instance_with_preloaded_target(self):
        target_list = self._get_preloaded_targets()

        ret = api.neutron.floating_ip_target_list_by_instance(
            self.request, 'id-vm2', target_list)
        self.assertEqual(['id21', 'id22'], [r.port_id for r in ret])
