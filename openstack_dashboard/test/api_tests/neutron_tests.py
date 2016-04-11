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
import uuid

from mox3.mox import IsA  # noqa

from django import http
from django.test.utils import override_settings

from neutronclient.common import exceptions as neutron_exc

from openstack_dashboard import api
from openstack_dashboard import policy
from openstack_dashboard.test import helpers as test


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
    def _test_network_list_for_tenant(self, include_external):
        all_networks = self.networks.list()
        tenant_id = '1'
        api.neutron.network_list(
            IsA(http.HttpRequest),
            tenant_id=tenant_id,
            shared=False).AndReturn([
                network for network in all_networks
                if network['tenant_id'] == tenant_id
            ])
        api.neutron.network_list(
            IsA(http.HttpRequest),
            shared=True).AndReturn([
                network for network in all_networks
                if network.get('shared')
            ])
        if include_external:
            api.neutron.network_list(
                IsA(http.HttpRequest),
                **{'router:external': True}).AndReturn([
                    network for network in all_networks
                    if network.get('router:external')
                ])
        self.mox.ReplayAll()

        ret_val = api.neutron.network_list_for_tenant(
            self.request, tenant_id,
            include_external=include_external)
        expected = [n for n in all_networks
                    if (n['tenant_id'] == tenant_id or
                        n['shared'] or
                        (include_external and n['router:external']))]
        self.assertEqual(set(n.id for n in expected),
                         set(n.id for n in ret_val))

    def test_network_list_for_tenant(self):
        self._test_network_list_for_tenant(include_external=False)

    def test_network_list_for_tenant_with_external(self):
        self._test_network_list_for_tenant(include_external=True)

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

    def _test_network_create(self, with_n1kv=False):
        network = {'network': self.api_networks.first()}
        form_data = {'network': {'name': 'net1',
                                 'tenant_id': self.request.user.project_id}}
        neutronclient = self.stub_neutronclient()
        if with_n1kv:
            n1kv_profile = 'n1kv:profile'
            test_net_profile = 'test_net_profile'
            network['network'][n1kv_profile] = test_net_profile
            form_data['network'][n1kv_profile] = test_net_profile
            neutronclient.create_network(body=form_data).AndReturn(network)
            self.mox.ReplayAll()
            ret_val = api.neutron.network_create(
                self.request,
                name='net1',
                net_profile_id=test_net_profile)
            # assert that when 'net_profile_id' is passed as a param to
            # network_create function, 'n1kv:profile' is appended as a key to
            # the returned network dictionary with value TEST_NET_PROFILE
            self.assertEqual(test_net_profile, ret_val[n1kv_profile])
            # also assert that 'net_profile_id' isn't there in the returned
            # network dictionary
            self.assertNotIn('net_profile_id', [k for k, _ in ret_val.items()])
        else:
            neutronclient.create_network(body=form_data).AndReturn(network)
            self.mox.ReplayAll()
            ret_val = api.neutron.network_create(self.request, name='net1')
        self.assertIsInstance(ret_val, api.neutron.Network)

    def test_network_create(self):
        self._test_network_create()

    def test_network_create_with_net_profile(self):
        self._test_network_create(with_n1kv=True)

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
        neutronclient.update_subnetpool(subnetpool_id, body={'subnetpool': params})\
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

    def _test_port_create(self, with_n1kv=False):
        port = {'port': self.api_ports.first()}
        params = {'network_id': port['port']['network_id'],
                  'tenant_id': port['port']['tenant_id'],
                  'name': port['port']['name'],
                  'device_id': port['port']['device_id']}

        neutronclient = self.stub_neutronclient()
        if with_n1kv:
            n1kv_profile = 'n1kv:profile'
            test_policy_profile = 'test_policy_profile'
            port['port'][n1kv_profile] = test_policy_profile
            body = {k: v for (k, v) in params.items()}
            body[n1kv_profile] = port['port'][n1kv_profile]
            neutronclient.create_port(body={'port': body}).AndReturn(port)
            self.mox.ReplayAll()
            ret_val = api.neutron.port_create(
                self.request,
                policy_profile_id=test_policy_profile,
                **params)
            # assert that when 'policy_profile_id' is passed as a param to
            # port_create function, 'n1kv:profile' is appended as a key to the
            # returned port dictionary with value TEST_POLICY_PROFILE
            self.assertEqual(test_policy_profile, ret_val[n1kv_profile])
            # also assert that 'policy_profile_id' isn't there in the returned
            # port dictionary
            self.assertNotIn('policy_profile_id',
                             [k for k, _ in ret_val.items()])
        else:
            neutronclient.create_port(body={'port': params}).AndReturn(port)
            self.mox.ReplayAll()
            ret_val = api.neutron.port_create(self.request, **params)
        self.assertIsInstance(ret_val, api.neutron.Port)
        self.assertEqual(api.neutron.Port(port['port']).id, ret_val.id)

    def test_port_create(self):
        self._test_port_create()

    def test_port_create_with_policy_profile(self):
        self._test_port_create(with_n1kv=True)

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
        neutronclient.list_extensions().MultipleTimes() \
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
    def _test_get_dvr_permission_dvr_supported(self, dvr_enabled):
        neutronclient = self.stub_neutronclient()
        extensions = self.api_extensions.list()
        if not dvr_enabled:
            extensions = [ext for ext in extensions if ext['alias'] != 'dvr']
        neutronclient.list_extensions() \
            .AndReturn({'extensions': extensions})
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
                       POLICY_CHECK_FUNCTION=policy.check)
    def _test_get_dvr_permission_with_policy_check(self, policy_check_allowed,
                                                   operation):
        self.mox.StubOutWithMock(policy, 'check')
        if operation == "create":
            role = (("network", "create_router:distributed"),)
        elif operation == "get":
            role = (("network", "get_router:distributed"),)
        policy.check(role, self.request).AndReturn(policy_check_allowed)
        if policy_check_allowed:
            neutronclient = self.stub_neutronclient()
            neutronclient.list_extensions() \
                .AndReturn({'extensions': self.api_extensions.list()})
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
                       POLICY_CHECK_FUNCTION=policy.check)
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
                       POLICY_CHECK_FUNCTION=policy.check)
    def _test_get_router_ha_permission_with_policy_check(self, ha_enabled):
        self.mox.StubOutWithMock(policy, 'check')
        role = (("network", "create_router:ha"),)
        policy.check(role, self.request).AndReturn(True)
        neutronclient = self.stub_neutronclient()
        if ha_enabled:
            extensions = self.api_extensions.list()
        else:
            extensions = {}
        neutronclient.list_extensions().AndReturn({'extensions': extensions})
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

        ports = [{'id': str(uuid.uuid4()),
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
