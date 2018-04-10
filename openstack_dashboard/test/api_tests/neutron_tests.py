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

from mox3.mox import IsA
from neutronclient.common import exceptions as neutron_exc
from oslo_utils import uuidutils
import six

from django import http
from django.test.utils import override_settings

from openstack_dashboard import api
from openstack_dashboard import policy
from openstack_dashboard.test import helpers as test


class NeutronApiTestBase(test.APITestCase):
    def setUp(self):
        super(NeutronApiTestBase, self).setUp()
        self.qclient = self.stub_neutronclient()


class NeutronApiTests(test.APITestCase):
    def test_network_list(self):
        networks = {'networks': self.api_networks.list()}
        subnets = {'subnets': self.api_subnets.list()}

        neutronclient = self.stub_neutronclient()
        neutronclient.list_networks().AndReturn(networks)
        neutronclient.list_subnets().AndReturn(subnets)
        self.mox.ReplayAll()

        ret_val = api.neutron.network_list(self.request)
        for n in ret_val:
            self.assertIsInstance(n, api.neutron.Network)

    @test.create_stubs({api.neutron: ('network_list',
                                      'subnet_list')})
    def _test_network_list_for_tenant(
            self, include_external,
            filter_params, should_called):
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
        if 'non_shared' in should_called:
            params = filter_params.copy()
            params['shared'] = False
            api.neutron.network_list(
                IsA(http.HttpRequest),
                tenant_id=tenant_id,
                **params).AndReturn([
                    network for network in all_networks
                    if network['tenant_id'] == tenant_id
                ])
        if 'shared' in should_called:
            params = filter_params.copy()
            params['shared'] = True
            api.neutron.network_list(
                IsA(http.HttpRequest),
                **params).AndReturn([
                    network for network in all_networks
                    if network.get('shared')
                ])
        if 'external' in should_called:
            params = filter_params.copy()
            params['router:external'] = True
            api.neutron.network_list(
                IsA(http.HttpRequest), **params).AndReturn([
                    network for network in all_networks
                    if network.get('router:external')
                ])
        self.mox.ReplayAll()

        ret_val = api.neutron.network_list_for_tenant(
            self.request, tenant_id,
            include_external=include_external,
            **filter_params)

        expected = [n for n in all_networks
                    if (('non_shared' in should_called and
                         n['tenant_id'] == tenant_id) or
                        ('shared' in should_called and n['shared']) or
                        ('external' in should_called and
                         include_external and n['router:external']))]
        self.assertEqual(set(n.id for n in expected),
                         set(n.id for n in ret_val))

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

    def test_network_get(self):
        network = {'network': self.api_networks.first()}
        subnet = {'subnet': self.api_subnets.first()}
        network_id = self.api_networks.first()['id']
        subnet_id = self.api_networks.first()['subnets'][0]

        neutronclient = self.stub_neutronclient()
        neutronclient.show_network(network_id).AndReturn(network)
        neutronclient.show_subnet(subnet_id).AndReturn(subnet)
        self.mox.ReplayAll()

        ret_val = api.neutron.network_get(self.request, network_id)
        self.assertIsInstance(ret_val, api.neutron.Network)
        self.assertEqual(1, len(ret_val['subnets']))
        self.assertIsInstance(ret_val['subnets'][0], api.neutron.Subnet)

    def test_network_get_with_subnet_get_notfound(self):
        network = {'network': self.api_networks.first()}
        network_id = self.api_networks.first()['id']
        subnet_id = self.api_networks.first()['subnets'][0]

        neutronclient = self.stub_neutronclient()
        neutronclient.show_network(network_id).AndReturn(network)
        neutronclient.show_subnet(subnet_id).AndRaise(neutron_exc.NotFound)
        self.mox.ReplayAll()

        ret_val = api.neutron.network_get(self.request, network_id)
        self.assertIsInstance(ret_val, api.neutron.Network)
        self.assertEqual(1, len(ret_val['subnets']))
        self.assertNotIsInstance(ret_val['subnets'][0], api.neutron.Subnet)
        self.assertIsInstance(ret_val['subnets'][0], str)

    def test_network_create(self):
        network = {'network': self.api_networks.first()}
        form_data = {'network': {'name': 'net1',
                                 'tenant_id': self.request.user.project_id}}
        neutronclient = self.stub_neutronclient()
        neutronclient.create_network(body=form_data).AndReturn(network)
        self.mox.ReplayAll()
        ret_val = api.neutron.network_create(self.request, name='net1')
        self.assertIsInstance(ret_val, api.neutron.Network)

    def test_network_update(self):
        network = {'network': self.api_networks.first()}
        network_id = self.api_networks.first()['id']

        neutronclient = self.stub_neutronclient()
        form_data = {'network': {'name': 'net1'}}
        neutronclient.update_network(network_id, body=form_data)\
            .AndReturn(network)
        self.mox.ReplayAll()

        ret_val = api.neutron.network_update(self.request, network_id,
                                             name='net1')
        self.assertIsInstance(ret_val, api.neutron.Network)

    def test_network_delete(self):
        network_id = self.api_networks.first()['id']

        neutronclient = self.stub_neutronclient()
        neutronclient.delete_network(network_id)
        self.mox.ReplayAll()

        api.neutron.network_delete(self.request, network_id)

    def test_get_network_ip_availability(self):
        network = {'network': self.api_networks.first()}
        mock_ip_availability = self.ip_availability.get()
        neutronclient = self.stub_neutronclient()
        neutronclient.show_network_ip_availability(network).\
            AndReturn(mock_ip_availability)

        self.mox.ReplayAll()
        ret_val = api.neutron.show_network_ip_availability(self.request,
                                                           network)

        self.assertIsInstance(ret_val, dict)

    def test_subnet_network_ip_availability(self):
        network = {'network': self.api_networks.first()}
        mock_ip_availability = self.ip_availability.get()
        neutronclient = self.stub_neutronclient()
        neutronclient.show_network_ip_availability(network).\
            AndReturn(mock_ip_availability)

        self.mox.ReplayAll()
        ip_availability = api.neutron. \
            show_network_ip_availability(self.request, network)
        availabilities = ip_availability.get("network_ip_availability",
                                             {})
        ret_val = availabilities.get("subnet_ip_availability", [])

        self.assertIsInstance(ret_val, list)

    def test_subnet_list(self):
        subnets = {'subnets': self.api_subnets.list()}

        neutronclient = self.stub_neutronclient()
        neutronclient.list_subnets().AndReturn(subnets)
        self.mox.ReplayAll()

        ret_val = api.neutron.subnet_list(self.request)
        for n in ret_val:
            self.assertIsInstance(n, api.neutron.Subnet)

    def test_subnet_get(self):
        subnet = {'subnet': self.api_subnets.first()}
        subnet_id = self.api_subnets.first()['id']

        neutronclient = self.stub_neutronclient()
        neutronclient.show_subnet(subnet_id).AndReturn(subnet)
        self.mox.ReplayAll()

        ret_val = api.neutron.subnet_get(self.request, subnet_id)
        self.assertIsInstance(ret_val, api.neutron.Subnet)

    def test_subnet_create(self):
        subnet_data = self.api_subnets.first()
        params = {'network_id': subnet_data['network_id'],
                  'tenant_id': subnet_data['tenant_id'],
                  'name': subnet_data['name'],
                  'cidr': subnet_data['cidr'],
                  'ip_version': subnet_data['ip_version'],
                  'gateway_ip': subnet_data['gateway_ip']}

        neutronclient = self.stub_neutronclient()
        neutronclient.create_subnet(body={'subnet': params})\
            .AndReturn({'subnet': subnet_data})
        self.mox.ReplayAll()

        ret_val = api.neutron.subnet_create(self.request, **params)
        self.assertIsInstance(ret_val, api.neutron.Subnet)

    def test_subnet_update(self):
        subnet_data = self.api_subnets.first()
        subnet_id = subnet_data['id']
        params = {'name': subnet_data['name'],
                  'gateway_ip': subnet_data['gateway_ip']}

        neutronclient = self.stub_neutronclient()
        neutronclient.update_subnet(subnet_id, body={'subnet': params})\
            .AndReturn({'subnet': subnet_data})
        self.mox.ReplayAll()

        ret_val = api.neutron.subnet_update(self.request, subnet_id, **params)
        self.assertIsInstance(ret_val, api.neutron.Subnet)

    def test_subnet_delete(self):
        subnet_id = self.api_subnets.first()['id']

        neutronclient = self.stub_neutronclient()
        neutronclient.delete_subnet(subnet_id)
        self.mox.ReplayAll()

        api.neutron.subnet_delete(self.request, subnet_id)

    def test_subnetpool_list(self):
        subnetpools = {'subnetpools': self.api_subnetpools.list()}

        neutronclient = self.stub_neutronclient()
        neutronclient.list_subnetpools().AndReturn(subnetpools)
        self.mox.ReplayAll()

        ret_val = api.neutron.subnetpool_list(self.request)
        for n in ret_val:
            self.assertIsInstance(n, api.neutron.SubnetPool)

    def test_subnetpool_get(self):
        subnetpool = {'subnetpool': self.api_subnetpools.first()}
        subnetpool_id = self.api_subnetpools.first()['id']

        neutronclient = self.stub_neutronclient()
        neutronclient.show_subnetpool(subnetpool_id).AndReturn(subnetpool)
        self.mox.ReplayAll()

        ret_val = api.neutron.subnetpool_get(self.request, subnetpool_id)
        self.assertIsInstance(ret_val, api.neutron.SubnetPool)

    def test_subnetpool_create(self):
        subnetpool_data = self.api_subnetpools.first()
        params = {'name': subnetpool_data['name'],
                  'prefixes': subnetpool_data['prefixes'],
                  'tenant_id': subnetpool_data['tenant_id']}

        neutronclient = self.stub_neutronclient()
        neutronclient.create_subnetpool(body={'subnetpool': params})\
            .AndReturn({'subnetpool': subnetpool_data})
        self.mox.ReplayAll()

        ret_val = api.neutron.subnetpool_create(self.request, **params)
        self.assertIsInstance(ret_val, api.neutron.SubnetPool)

    def test_subnetpool_update(self):
        subnetpool_data = self.api_subnetpools.first()
        subnetpool_id = subnetpool_data['id']
        params = {'name': subnetpool_data['name'],
                  'prefixes': subnetpool_data['prefixes']}

        neutronclient = self.stub_neutronclient()
        neutronclient.update_subnetpool(subnetpool_id,
                                        body={'subnetpool': params})\
            .AndReturn({'subnetpool': subnetpool_data})
        self.mox.ReplayAll()

        ret_val = api.neutron.subnetpool_update(self.request, subnetpool_id,
                                                **params)
        self.assertIsInstance(ret_val, api.neutron.SubnetPool)

    def test_subnetpool_delete(self):
        subnetpool_id = self.api_subnetpools.first()['id']

        neutronclient = self.stub_neutronclient()
        neutronclient.delete_subnetpool(subnetpool_id)
        self.mox.ReplayAll()

        api.neutron.subnetpool_delete(self.request, subnetpool_id)

    def test_port_list(self):
        ports = {'ports': self.api_ports.list()}

        neutronclient = self.stub_neutronclient()
        neutronclient.list_ports().AndReturn(ports)
        self.mox.ReplayAll()

        ret_val = api.neutron.port_list(self.request)
        for p in ret_val:
            self.assertIsInstance(p, api.neutron.Port)

    def test_port_get(self):
        port = {'port': self.api_ports.first()}
        port_id = self.api_ports.first()['id']

        neutronclient = self.stub_neutronclient()
        neutronclient.show_port(port_id).AndReturn(port)
        self.mox.ReplayAll()

        ret_val = api.neutron.port_get(self.request, port_id)
        self.assertIsInstance(ret_val, api.neutron.Port)

    def test_port_create(self):
        port = {'port': self.api_ports.first()}
        params = {'network_id': port['port']['network_id'],
                  'tenant_id': port['port']['tenant_id'],
                  'name': port['port']['name'],
                  'device_id': port['port']['device_id']}

        neutronclient = self.stub_neutronclient()
        neutronclient.create_port(body={'port': params}).AndReturn(port)
        self.mox.ReplayAll()
        ret_val = api.neutron.port_create(self.request, **params)
        self.assertIsInstance(ret_val, api.neutron.Port)
        self.assertEqual(api.neutron.Port(port['port']).id, ret_val.id)

    def test_port_update(self):
        port_data = self.api_ports.first()
        port_id = port_data['id']
        params = {'name': port_data['name'],
                  'device_id': port_data['device_id']}

        neutronclient = self.stub_neutronclient()
        neutronclient.update_port(port_id, body={'port': params})\
            .AndReturn({'port': port_data})
        self.mox.ReplayAll()

        ret_val = api.neutron.port_update(self.request, port_id, **params)
        self.assertIsInstance(ret_val, api.neutron.Port)
        self.assertEqual(api.neutron.Port(port_data).id, ret_val.id)

    def test_port_delete(self):
        port_id = self.api_ports.first()['id']

        neutronclient = self.stub_neutronclient()
        neutronclient.delete_port(port_id)
        self.mox.ReplayAll()

        api.neutron.port_delete(self.request, port_id)

    def test_trunk_list(self):
        trunks = {'trunks': self.api_trunks.list()}
        neutron_client = self.stub_neutronclient()
        neutron_client.list_trunks().AndReturn(trunks)
        self.mox.ReplayAll()

        ret_val = api.neutron.trunk_list(self.request)
        for t in ret_val:
            self.assertIsInstance(t, api.neutron.Trunk)

    def test_trunk_show(self):
        trunk = {'trunk': self.api_trunks.first()}
        trunk_id = self.api_trunks.first()['id']

        neutron_client = self.stub_neutronclient()
        neutron_client.show_trunk(trunk_id).AndReturn(trunk)
        self.mox.ReplayAll()

        ret_val = api.neutron.trunk_show(self.request, trunk_id)
        self.assertIsInstance(ret_val, api.neutron.Trunk)

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

    def test_trunk_delete(self):
        trunk_id = self.api_trunks.first()['id']

        neutronclient = self.stub_neutronclient()
        neutronclient.delete_trunk(trunk_id)
        self.mox.ReplayAll()

        api.neutron.trunk_delete(self.request, trunk_id)

    def test_router_list(self):
        routers = {'routers': self.api_routers.list()}

        neutronclient = self.stub_neutronclient()
        neutronclient.list_routers().AndReturn(routers)
        self.mox.ReplayAll()

        ret_val = api.neutron.router_list(self.request)
        for n in ret_val:
            self.assertIsInstance(n, api.neutron.Router)

    def test_router_get(self):
        router = {'router': self.api_routers.first()}
        router_id = self.api_routers.first()['id']

        neutronclient = self.stub_neutronclient()
        neutronclient.show_router(router_id).AndReturn(router)
        self.mox.ReplayAll()

        ret_val = api.neutron.router_get(self.request, router_id)
        self.assertIsInstance(ret_val, api.neutron.Router)

    def test_router_create(self):
        router = {'router': self.api_routers.first()}

        neutronclient = self.stub_neutronclient()
        form_data = {'router': {'name': 'router1',
                                'tenant_id': self.request.user.project_id}}
        neutronclient.create_router(body=form_data).AndReturn(router)
        self.mox.ReplayAll()

        ret_val = api.neutron.router_create(self.request, name='router1')
        self.assertIsInstance(ret_val, api.neutron.Router)

    def test_router_delete(self):
        router_id = self.api_routers.first()['id']

        neutronclient = self.stub_neutronclient()
        neutronclient.delete_router(router_id)
        self.mox.ReplayAll()

        api.neutron.router_delete(self.request, router_id)

    def test_router_add_interface(self):
        subnet_id = self.api_subnets.first()['id']
        router_id = self.api_routers.first()['id']

        neutronclient = self.stub_neutronclient()
        form_data = {'subnet_id': subnet_id}
        neutronclient.add_interface_router(
            router_id, form_data).AndReturn(None)
        self.mox.ReplayAll()

        api.neutron.router_add_interface(
            self.request, router_id, subnet_id=subnet_id)

    def test_router_remove_interface(self):
        router_id = self.api_routers.first()['id']
        fake_port = self.api_ports.first()['id']

        neutronclient = self.stub_neutronclient()
        neutronclient.remove_interface_router(
            router_id, {'port_id': fake_port})
        self.mox.ReplayAll()

        api.neutron.router_remove_interface(
            self.request, router_id, port_id=fake_port)

    def test_is_extension_supported(self):
        neutronclient = self.stub_neutronclient()
        neutronclient.list_extensions() \
            .AndReturn({'extensions': self.api_extensions.list()})
        self.mox.ReplayAll()

        self.assertTrue(
            api.neutron.is_extension_supported(self.request, 'quotas'))
        self.assertFalse(
            api.neutron.is_extension_supported(self.request, 'doesntexist'))

    def test_router_static_route_list(self):
        router = {'router': self.api_routers_with_routes.first()}
        router_id = self.api_routers_with_routes.first()['id']

        neutronclient = self.stub_neutronclient()
        neutronclient.show_router(router_id).AndReturn(router)
        self.mox.ReplayAll()

        ret_val = api.neutron.router_static_route_list(self.request, router_id)
        self.assertIsInstance(ret_val[0], api.neutron.RouterStaticRoute)

    def test_router_static_route_remove(self):
        router = {'router': self.api_routers_with_routes.first()}
        router_id = self.api_routers_with_routes.first()['id']
        post_router = copy.deepcopy(router)
        route = api.neutron.RouterStaticRoute(post_router['router']
                                              ['routes'].pop())

        neutronclient = self.stub_neutronclient()
        neutronclient.show_router(router_id).AndReturn(router)
        body = {'router': {'routes': post_router['router']['routes']}}
        neutronclient.update_router(router_id, body=body)\
                     .AndReturn(post_router)
        self.mox.ReplayAll()

        api.neutron.router_static_route_remove(self.request,
                                               router_id, route.id)

    def test_router_static_route_add(self):
        router = {'router': self.api_routers_with_routes.first()}
        router_id = self.api_routers_with_routes.first()['id']
        post_router = copy.deepcopy(router)
        route = {'nexthop': '10.0.0.5', 'destination': '40.0.1.0/24'}
        post_router['router']['routes'].insert(0, route)
        body = {'router': {'routes': post_router['router']['routes']}}

        neutronclient = self.stub_neutronclient()
        neutronclient.show_router(router_id).AndReturn(router)
        neutronclient.update_router(router_id, body=body)\
                     .AndReturn(post_router)
        self.mox.ReplayAll()

        api.neutron.router_static_route_add(self.request, router_id, route)

    # NOTE(amotoki): "dvr" permission tests check most of
    # get_feature_permission features.
    # These tests are not specific to "dvr" extension.
    # Please be careful if you drop "dvr" extension in future.

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_distributed_router':
                                                  True},
                       POLICY_CHECK_FUNCTION=None)
    @test.create_stubs({api.neutron: ('is_extension_supported',)})
    def _test_get_dvr_permission_dvr_supported(self, dvr_enabled):
        api.neutron.is_extension_supported(self.request, 'dvr').\
            AndReturn(dvr_enabled)
        self.mox.ReplayAll()
        self.assertEqual(dvr_enabled,
                         api.neutron.get_feature_permission(self.request,
                                                            'dvr', 'get'))

    def test_get_dvr_permission_dvr_supported(self):
        self._test_get_dvr_permission_dvr_supported(dvr_enabled=True)

    def test_get_dvr_permission_dvr_not_supported(self):
        self._test_get_dvr_permission_dvr_supported(dvr_enabled=False)

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_distributed_router':
                                                  True},
                       POLICY_CHECK_FUNCTION='openstack_auth.policy.check')
    @test.create_stubs({api.neutron: ('is_extension_supported',)})
    def _test_get_dvr_permission_with_policy_check(self, policy_check_allowed,
                                                   operation):
        self.mox.StubOutWithMock(policy, 'check')
        if operation == "create":
            role = (("network", "create_router:distributed"),)
        elif operation == "get":
            role = (("network", "get_router:distributed"),)
        policy.check(role, self.request).AndReturn(policy_check_allowed)
        if policy_check_allowed:
            api.neutron.is_extension_supported(self.request, 'dvr').\
                AndReturn(policy_check_allowed)
        self.mox.ReplayAll()
        self.assertEqual(policy_check_allowed,
                         api.neutron.get_feature_permission(self.request,
                                                            'dvr', operation))

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
    @test.create_stubs({api.neutron: ('is_extension_supported', )})
    def _test_get_router_ha_permission_with_policy_check(self, ha_enabled):
        self.mox.StubOutWithMock(policy, 'check')
        role = (("network", "create_router:ha"),)
        policy.check(role, self.request).AndReturn(True)
        api.neutron.is_extension_supported(self.request, 'l3-ha')\
            .AndReturn(ha_enabled)
        self.mox.ReplayAll()
        self.assertEqual(ha_enabled,
                         api.neutron.get_feature_permission(self.request,
                                                            'l3-ha', 'create'))

    def test_get_router_ha_permission_with_l3_ha_extension(self):
        self._test_get_router_ha_permission_with_policy_check(True)

    def test_get_router_ha_permission_without_l3_ha_extension(self):
        self._test_get_router_ha_permission_with_policy_check(False)

    def test_list_resources_with_long_filters(self):
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
        port_ids = [port['id'] for port in ports]

        neutronclient = self.stub_neutronclient()
        uri_len_exc = neutron_exc.RequestURITooLong(excess=220)
        neutronclient.list_ports(id=port_ids).AndRaise(uri_len_exc)
        for i in range(0, 10, 4):
            neutronclient.list_ports(id=port_ids[i:i + 4]) \
                .AndReturn({'ports': ports[i:i + 4]})
        self.mox.ReplayAll()

        ret_val = api.neutron.list_resources_with_long_filters(
            api.neutron.port_list, 'id', port_ids,
            request=self.request)
        self.assertEqual(10, len(ret_val))
        self.assertEqual(port_ids, [p.id for p in ret_val])

    def test_qos_policies_list(self):
        exp_policies = self.qos_policies.list()
        api_qos_policies = {'policies': self.api_qos_policies.list()}

        neutronclient = self.stub_neutronclient()
        neutronclient.list_qos_policies().AndReturn(api_qos_policies)
        self.mox.ReplayAll()

        ret_val = api.neutron.policy_list(self.request)
        self.assertEqual(len(ret_val), len(exp_policies))
        self.assertIsInstance(ret_val[0], api.neutron.QoSPolicy)
        self.assertEqual(exp_policies[0].name, ret_val[0].name)

    def test_qos_policy_create(self):
        qos_policy = self.api_qos_policies.first()
        post_data = {'policy': {'name': qos_policy['name']}}

        neutronclient = self.stub_neutronclient()
        neutronclient.create_qos_policy(body=post_data) \
            .AndReturn({'policy': qos_policy})
        self.mox.ReplayAll()

        ret_val = api.neutron.policy_create(self.request,
                                            name=qos_policy['name'])
        self.assertIsInstance(ret_val, api.neutron.QoSPolicy)
        self.assertEqual(qos_policy['name'], ret_val.name)


class NeutronApiSecurityGroupTests(NeutronApiTestBase):

    def setUp(self):
        super(NeutronApiSecurityGroupTests, self).setUp()
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
        exp_rules = exp_sg['security_group_rules']
        self.assertEqual(len(exp_rules), len(ret_sg.rules))
        for (exprule, retrule) in six.moves.zip(exp_rules, ret_sg.rules):
            self._cmp_sg_rule(exprule, retrule)

    def _test_security_group_list(self, **params):
        sgs = self.api_security_groups.list()
        q_params = {'tenant_id': self.request.user.tenant_id}
        # if tenant_id is specified, the passed tenant_id should be sent.
        q_params.update(params)
        # use deepcopy to ensure self.api_security_groups is not modified.
        self.qclient.list_security_groups(**q_params) \
            .AndReturn({'security_groups': copy.deepcopy(sgs)})
        self.mox.ReplayAll()

        rets = api.neutron.security_group_list(self.request, **params)
        self.assertEqual(len(sgs), len(rets))
        for (exp, ret) in six.moves.zip(sgs, rets):
            self._cmp_sg(exp, ret)

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
        self.qclient.show_security_group(secgroup['id']) \
            .AndReturn({'security_group': copy.deepcopy(secgroup)})
        self.qclient.list_security_groups(id=sg_ids, fields=['id', 'name']) \
            .AndReturn({'security_groups': related_sgs})
        self.mox.ReplayAll()
        ret = api.neutron.security_group_get(self.request, secgroup['id'])
        self._cmp_sg(secgroup, ret)

    def test_security_group_create(self):
        secgroup = self.api_security_groups.list()[1]
        body = {'security_group':
                {'name': secgroup['name'],
                 'description': secgroup['description'],
                 'tenant_id': self.request.user.project_id}}
        self.qclient.create_security_group(body) \
            .AndReturn({'security_group': copy.deepcopy(secgroup)})
        self.mox.ReplayAll()
        ret = api.neutron.security_group_create(self.request, secgroup['name'],
                                                secgroup['description'])
        self._cmp_sg(secgroup, ret)

    def test_security_group_update(self):
        secgroup = self.api_security_groups.list()[1]
        secgroup = copy.deepcopy(secgroup)
        secgroup['name'] = 'newname'
        secgroup['description'] = 'new description'
        body = {'security_group':
                {'name': secgroup['name'],
                 'description': secgroup['description']}}
        self.qclient.update_security_group(secgroup['id'], body) \
            .AndReturn({'security_group': secgroup})
        self.mox.ReplayAll()
        ret = api.neutron.security_group_update(self.request,
                                                secgroup['id'],
                                                secgroup['name'],
                                                secgroup['description'])
        self._cmp_sg(secgroup, ret)

    def test_security_group_delete(self):
        secgroup = self.api_security_groups.first()
        self.qclient.delete_security_group(secgroup['id'])
        self.mox.ReplayAll()
        api.neutron.security_group_delete(self.request, secgroup['id'])

    def test_security_group_rule_create(self):
        sg_rule = [r for r in self.api_security_group_rules.list()
                   if r['protocol'] == 'tcp' and r['remote_ip_prefix']][0]
        sg_id = sg_rule['security_group_id']
        secgroup = [sg for sg in self.api_security_groups.list()
                    if sg['id'] == sg_id][0]

        post_rule = copy.deepcopy(sg_rule)
        del post_rule['id']
        del post_rule['tenant_id']
        post_body = {'security_group_rule': post_rule}
        self.qclient.create_security_group_rule(post_body) \
            .AndReturn({'security_group_rule': copy.deepcopy(sg_rule)})
        self.qclient.list_security_groups(id=set([sg_id]),
                                          fields=['id', 'name']) \
            .AndReturn({'security_groups': [copy.deepcopy(secgroup)]})
        self.mox.ReplayAll()

        ret = api.neutron.security_group_rule_create(
            self.request, sg_rule['security_group_id'],
            sg_rule['direction'], sg_rule['ethertype'], sg_rule['protocol'],
            sg_rule['port_range_min'], sg_rule['port_range_max'],
            sg_rule['remote_ip_prefix'], sg_rule['remote_group_id'])
        self._cmp_sg_rule(sg_rule, ret)

    def test_security_group_rule_delete(self):
        sg_rule = self.api_security_group_rules.first()
        self.qclient.delete_security_group_rule(sg_rule['id'])
        self.mox.ReplayAll()
        api.neutron.security_group_rule_delete(self.request, sg_rule['id'])

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
        self.qclient.list_ports(device_id=instance_id) \
            .AndReturn({'ports': instance_ports})
        secgroups = copy.deepcopy(self.api_security_groups.list())
        self.qclient.list_security_groups(id=set(cur_sg_ids)) \
            .AndReturn({'security_groups': secgroups})
        self.mox.ReplayAll()

        api.neutron.server_security_groups(self.request, instance_id)

    def test_server_update_security_groups(self):
        cur_sg_ids = [self.api_security_groups.first()['id']]
        new_sg_ids = [sg['id'] for sg in self.api_security_groups.list()[:2]]
        instance_id, instance_ports = self._get_instance(cur_sg_ids)
        self.qclient.list_ports(device_id=instance_id) \
            .AndReturn({'ports': instance_ports})
        for p in instance_ports:
            body = {'port': {'security_groups': new_sg_ids}}
            self.qclient.update_port(p['id'], body=body).AndReturn({'port': p})
        self.mox.ReplayAll()
        api.neutron.server_update_security_groups(
            self.request, instance_id, new_sg_ids)


class NeutronApiFloatingIpTests(NeutronApiTestBase):

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_router': True})
    def test_floating_ip_supported(self):
        self.mox.ReplayAll()
        self.assertTrue(api.neutron.floating_ip_supported(self.request))

    @override_settings(OPENSTACK_NEUTRON_NETWORK={'enable_router': False})
    def test_floating_ip_supported_false(self):
        self.mox.ReplayAll()
        self.assertFalse(api.neutron.floating_ip_supported(self.request))

    def test_floating_ip_pools_list(self):
        search_opts = {'router:external': True}
        ext_nets = [n for n in self.api_networks.list()
                    if n['router:external']]
        self.qclient.list_networks(**search_opts) \
            .AndReturn({'networks': ext_nets})
        self.mox.ReplayAll()

        rets = api.neutron.floating_ip_pools_list(self.request)
        for attr in ['id', 'name']:
            self.assertEqual([p[attr] for p in ext_nets],
                             [getattr(p, attr) for p in rets])

    def test_floating_ip_list(self):
        fips = self.api_floating_ips.list()
        filters = {'tenant_id': self.request.user.tenant_id}

        self.qclient.list_floatingips(**filters) \
            .AndReturn({'floatingips': fips})
        self.qclient.list_ports(**filters) \
            .AndReturn({'ports': self.api_ports.list()})
        self.mox.ReplayAll()

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

    def test_floating_ip_list_all_tenants(self):
        fips = self.api_floating_ips.list()
        self.qclient.list_floatingips().AndReturn({'floatingips': fips})
        self.qclient.list_ports().AndReturn({'ports': self.api_ports.list()})
        self.mox.ReplayAll()

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

    def _test_floating_ip_get_associated(self, assoc_port, exp_instance_type):
        fip = self.api_floating_ips.list()[1]

        self.qclient.show_floatingip(fip['id']).AndReturn({'floatingip': fip})
        self.qclient.show_port(assoc_port['id']) \
            .AndReturn({'port': assoc_port})
        self.mox.ReplayAll()

        ret = api.neutron.tenant_floating_ip_get(self.request, fip['id'])
        for attr in ['id', 'ip', 'pool', 'fixed_ip', 'port_id']:
            self.assertEqual(fip[attr], getattr(ret, attr))
        self.assertEqual(assoc_port['device_id'], ret.instance_id)
        self.assertEqual(exp_instance_type, ret.instance_type)

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

        self.qclient.show_floatingip(fip['id']).AndReturn({'floatingip': fip})
        self.mox.ReplayAll()

        ret = api.neutron.tenant_floating_ip_get(self.request, fip['id'])
        for attr in ['id', 'ip', 'pool', 'fixed_ip', 'port_id']:
            self.assertEqual(fip[attr], getattr(ret, attr))
        self.assertIsNone(ret.instance_id)
        self.assertIsNone(ret.instance_type)

    def test_floating_ip_allocate(self):
        ext_nets = [n for n in self.api_networks.list()
                    if n['router:external']]
        ext_net = ext_nets[0]
        fip = self.api_floating_ips.first()
        self.qclient.create_floatingip(
            {'floatingip': {'floating_network_id': ext_net['id'],
                            'tenant_id': self.request.user.project_id}}) \
            .AndReturn({'floatingip': fip})
        self.mox.ReplayAll()

        ret = api.neutron.tenant_floating_ip_allocate(self.request,
                                                      ext_net['id'])
        for attr in ['id', 'ip', 'pool', 'fixed_ip', 'port_id']:
            self.assertEqual(fip[attr], getattr(ret, attr))
        self.assertIsNone(ret.instance_id)
        self.assertIsNone(ret.instance_type)

    def test_floating_ip_release(self):
        fip = self.api_floating_ips.first()
        self.qclient.delete_floatingip(fip['id'])
        self.mox.ReplayAll()

        api.neutron.tenant_floating_ip_release(self.request, fip['id'])

    def test_floating_ip_associate(self):
        fip = self.api_floating_ips.list()[1]
        assoc_port = self.api_ports.list()[1]
        ip_address = assoc_port['fixed_ips'][0]['ip_address']
        target_id = '%s_%s' % (assoc_port['id'], ip_address)
        params = {'port_id': assoc_port['id'],
                  'fixed_ip_address': ip_address}
        self.qclient.update_floatingip(fip['id'],
                                       {'floatingip': params})
        self.mox.ReplayAll()

        api.neutron.floating_ip_associate(self.request, fip['id'], target_id)

    def test_floating_ip_disassociate(self):
        fip = self.api_floating_ips.list()[1]

        self.qclient.update_floatingip(fip['id'],
                                       {'floatingip': {'port_id': None}})
        self.mox.ReplayAll()

        api.neutron.floating_ip_disassociate(self.request, fip['id'])

    def _get_target_id(self, port):
        param = {'id': port['id'],
                 'addr': port['fixed_ips'][0]['ip_address']}
        return '%(id)s_%(addr)s' % param

    def _get_target_name(self, port):
        param = {'svrid': port['device_id'],
                 'addr': port['fixed_ips'][0]['ip_address']}
        return 'server_%(svrid)s: %(addr)s' % param

    def _subs_from_port(self, port):
        return [ip['subnet_id'] for ip in port['fixed_ips']]

    @override_settings(
        OPENSTACK_NEUTRON_NETWORK={
            'enable_fip_topology_check': True,
        }
    )
    def test_floating_ip_target_list(self):
        ports = self.api_ports.list()
        # Port on the first subnet is connected to a router
        # attached to external network in neutron_data.
        subnet_id = self.subnets.first().id
        shared_nets = [n for n in self.api_networks.list() if n['shared']]
        shared_subnet_ids = [s for n in shared_nets for s in n['subnets']]
        target_ports = [
            (self._get_target_id(p), self._get_target_name(p)) for p in ports
            if (not p['device_owner'].startswith('network:') and
                (subnet_id in self._subs_from_port(p) or
                 (set(shared_subnet_ids) & set(self._subs_from_port(p)))))
        ]
        filters = {'tenant_id': self.request.user.tenant_id}
        self.qclient.list_ports(**filters).AndReturn({'ports': ports})
        servers = self.servers.list()
        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn("2.45")
        search_opts = {'project_id': self.request.user.tenant_id}
        novaclient.servers.list(False, search_opts).AndReturn(servers)

        search_opts = {'router:external': True}
        ext_nets = [n for n in self.api_networks.list()
                    if n['router:external']]
        self.qclient.list_networks(**search_opts) \
            .AndReturn({'networks': ext_nets})
        self.qclient.list_routers().AndReturn({'routers':
                                               self.api_routers.list()})
        self.qclient.list_networks(shared=True).AndReturn({'networks':
                                                           shared_nets})
        shared_subs = [s for s in self.api_subnets.list()
                       if s['id'] in shared_subnet_ids]
        self.qclient.list_subnets().AndReturn({'subnets': shared_subs})

        self.mox.ReplayAll()

        rets = api.neutron.floating_ip_target_list(self.request)
        self.assertEqual(len(target_ports), len(rets))
        for ret, exp in zip(rets, target_ports):
            self.assertEqual(exp[0], ret.id)
            self.assertEqual(exp[1], ret.name)

    def test_floating_ip_target_get_by_instance(self):
        ports = self.api_ports.list()
        candidates = [p for p in ports if p['device_id'] == '1']
        search_opts = {'device_id': '1'}
        self.qclient.list_ports(**search_opts).AndReturn({'ports': candidates})
        self.mox.ReplayAll()

        ret = api.neutron.floating_ip_target_get_by_instance(self.request, '1')
        self.assertEqual(self._get_target_id(candidates[0]), ret)

    def test_target_floating_ip_port_by_instance(self):
        ports = self.api_ports.list()
        candidates = [p for p in ports if p['device_id'] == '1']
        search_opts = {'device_id': '1'}
        self.qclient.list_ports(**search_opts).AndReturn({'ports': candidates})
        self.mox.ReplayAll()

        ret = api.neutron.floating_ip_target_list_by_instance(self.request,
                                                              '1')
        self.assertEqual(self._get_target_id(candidates[0]), ret[0])
        self.assertEqual(len(candidates), len(ret))

    def test_floating_ip_target_get_by_instance_with_preloaded_target(self):
        target_list = [{'name': 'name11', 'id': 'id11', 'instance_id': 'vm1'},
                       {'name': 'name21', 'id': 'id21', 'instance_id': 'vm2'},
                       {'name': 'name22', 'id': 'id22', 'instance_id': 'vm2'}]
        self.mox.ReplayAll()

        ret = api.neutron.floating_ip_target_get_by_instance(
            self.request, 'vm2', target_list)
        self.assertEqual('id21', ret)

    def test_target_floating_ip_port_by_instance_with_preloaded_target(self):
        target_list = [{'name': 'name11', 'id': 'id11', 'instance_id': 'vm1'},
                       {'name': 'name21', 'id': 'id21', 'instance_id': 'vm2'},
                       {'name': 'name22', 'id': 'id22', 'instance_id': 'vm2'}]
        self.mox.ReplayAll()

        ret = api.neutron.floating_ip_target_list_by_instance(
            self.request, 'vm2', target_list)
        self.assertEqual(['id21', 'id22'], ret)
