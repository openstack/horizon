# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class QuantumApiTests(test.APITestCase):
    def test_network_list(self):
        networks = {'networks': self.api_networks.list()}
        subnets = {'subnets': self.api_subnets.list()}

        quantumclient = self.stub_quantumclient()
        quantumclient.list_networks().AndReturn(networks)
        quantumclient.list_subnets().AndReturn(subnets)
        self.mox.ReplayAll()

        ret_val = api.quantum.network_list(self.request)
        for n in ret_val:
            self.assertIsInstance(n, api.quantum.Network)

    def test_network_get(self):
        network = {'network': self.api_networks.first()}
        subnet = {'subnet': self.api_subnets.first()}
        network_id = self.api_networks.first()['id']
        subnet_id = self.api_networks.first()['subnets'][0]

        quantumclient = self.stub_quantumclient()
        quantumclient.show_network(network_id).AndReturn(network)
        quantumclient.show_subnet(subnet_id).AndReturn(subnet)
        self.mox.ReplayAll()

        ret_val = api.quantum.network_get(self.request, network_id)
        self.assertIsInstance(ret_val, api.quantum.Network)

    def test_network_create(self):
        network = {'network': self.api_networks.first()}

        quantumclient = self.stub_quantumclient()
        form_data = {'network': {'name': 'net1'}}
        quantumclient.create_network(body=form_data).AndReturn(network)
        self.mox.ReplayAll()

        ret_val = api.quantum.network_create(self.request, name='net1')
        self.assertIsInstance(ret_val, api.quantum.Network)

    def test_network_modify(self):
        network = {'network': self.api_networks.first()}
        network_id = self.api_networks.first()['id']

        quantumclient = self.stub_quantumclient()
        form_data = {'network': {'name': 'net1'}}
        quantumclient.update_network(network_id, body=form_data)\
            .AndReturn(network)
        self.mox.ReplayAll()

        ret_val = api.quantum.network_modify(self.request, network_id,
                                             name='net1')
        self.assertIsInstance(ret_val, api.quantum.Network)

    def test_network_delete(self):
        network_id = self.api_networks.first()['id']

        quantumclient = self.stub_quantumclient()
        quantumclient.delete_network(network_id)
        self.mox.ReplayAll()

        api.quantum.network_delete(self.request, network_id)

    def test_subnet_list(self):
        subnets = {'subnets': self.api_subnets.list()}

        quantumclient = self.stub_quantumclient()
        quantumclient.list_subnets().AndReturn(subnets)
        self.mox.ReplayAll()

        ret_val = api.quantum.subnet_list(self.request)
        for n in ret_val:
            self.assertIsInstance(n, api.quantum.Subnet)

    def test_subnet_get(self):
        subnet = {'subnet': self.api_subnets.first()}
        subnet_id = self.api_subnets.first()['id']

        quantumclient = self.stub_quantumclient()
        quantumclient.show_subnet(subnet_id).AndReturn(subnet)
        self.mox.ReplayAll()

        ret_val = api.quantum.subnet_get(self.request, subnet_id)
        self.assertIsInstance(ret_val, api.quantum.Subnet)

    def test_subnet_create(self):
        subnet_data = self.api_subnets.first()
        params = {'network_id': subnet_data['network_id'],
                  'tenant_id': subnet_data['tenant_id'],
                  'name': subnet_data['name'],
                  'cidr': subnet_data['cidr'],
                  'ip_version': subnet_data['ip_version'],
                  'gateway_ip': subnet_data['gateway_ip']}

        quantumclient = self.stub_quantumclient()
        quantumclient.create_subnet(body={'subnet': params})\
            .AndReturn({'subnet': subnet_data})
        self.mox.ReplayAll()

        ret_val = api.quantum.subnet_create(self.request, **params)
        self.assertIsInstance(ret_val, api.quantum.Subnet)

    def test_subnet_modify(self):
        subnet_data = self.api_subnets.first()
        subnet_id = subnet_data['id']
        params = {'name': subnet_data['name'],
                  'gateway_ip': subnet_data['gateway_ip']}

        quantumclient = self.stub_quantumclient()
        quantumclient.update_subnet(subnet_id, body={'subnet': params})\
            .AndReturn({'subnet': subnet_data})
        self.mox.ReplayAll()

        ret_val = api.quantum.subnet_modify(self.request, subnet_id, **params)
        self.assertIsInstance(ret_val, api.quantum.Subnet)

    def test_subnet_delete(self):
        subnet_id = self.api_subnets.first()['id']

        quantumclient = self.stub_quantumclient()
        quantumclient.delete_subnet(subnet_id)
        self.mox.ReplayAll()

        api.quantum.subnet_delete(self.request, subnet_id)

    def test_port_list(self):
        ports = {'ports': self.api_ports.list()}

        quantumclient = self.stub_quantumclient()
        quantumclient.list_ports().AndReturn(ports)
        self.mox.ReplayAll()

        ret_val = api.quantum.port_list(self.request)
        for p in ret_val:
            self.assertIsInstance(p, api.quantum.Port)

    def test_port_get(self):
        port = {'port': self.api_ports.first()}
        port_id = self.api_ports.first()['id']

        quantumclient = self.stub_quantumclient()
        quantumclient.show_port(port_id).AndReturn(port)
        self.mox.ReplayAll()

        ret_val = api.quantum.port_get(self.request, port_id)
        self.assertIsInstance(ret_val, api.quantum.Port)

    def test_port_create(self):
        port_data = self.api_ports.first()
        params = {'network_id': port_data['network_id'],
                  'tenant_id': port_data['tenant_id'],
                  'name': port_data['name'],
                  'device_id': port_data['device_id']}

        quantumclient = self.stub_quantumclient()
        quantumclient.create_port(body={'port': params})\
            .AndReturn({'port': port_data})
        self.mox.ReplayAll()

        ret_val = api.quantum.port_create(self.request, **params)
        self.assertIsInstance(ret_val, api.quantum.Port)
        self.assertEqual(ret_val.id, api.quantum.Port(port_data).id)

    def test_port_modify(self):
        port_data = self.api_ports.first()
        port_id = port_data['id']
        params = {'name': port_data['name'],
                  'device_id': port_data['device_id']}

        quantumclient = self.stub_quantumclient()
        quantumclient.update_port(port_id, body={'port': params})\
            .AndReturn({'port': port_data})
        self.mox.ReplayAll()

        ret_val = api.quantum.port_modify(self.request, port_id, **params)
        self.assertIsInstance(ret_val, api.quantum.Port)
        self.assertEqual(ret_val.id, api.quantum.Port(port_data).id)

    def test_port_delete(self):
        port_id = self.api_ports.first()['id']

        quantumclient = self.stub_quantumclient()
        quantumclient.delete_port(port_id)
        self.mox.ReplayAll()

        api.quantum.port_delete(self.request, port_id)

    def test_router_list(self):
        routers = {'routers': self.api_routers.list()}

        quantumclient = self.stub_quantumclient()
        quantumclient.list_routers().AndReturn(routers)
        self.mox.ReplayAll()

        ret_val = api.quantum.router_list(self.request)
        for n in ret_val:
            self.assertIsInstance(n, api.quantum.Router)

    def test_router_get(self):
        router = {'router': self.api_routers.first()}
        router_id = self.api_routers.first()['id']

        quantumclient = self.stub_quantumclient()
        quantumclient.show_router(router_id).AndReturn(router)
        self.mox.ReplayAll()

        ret_val = api.quantum.router_get(self.request, router_id)
        self.assertIsInstance(ret_val, api.quantum.Router)

    def test_router_create(self):
        router = {'router': self.api_routers.first()}

        quantumclient = self.stub_quantumclient()
        form_data = {'router': {'name': 'router1'}}
        quantumclient.create_router(body=form_data).AndReturn(router)
        self.mox.ReplayAll()

        ret_val = api.quantum.router_create(self.request, name='router1')
        self.assertIsInstance(ret_val, api.quantum.Router)

    def test_router_delete(self):
        router_id = self.api_routers.first()['id']

        quantumclient = self.stub_quantumclient()
        quantumclient.delete_router(router_id)
        self.mox.ReplayAll()

        api.quantum.router_delete(self.request, router_id)

    def test_router_add_interface(self):
        subnet_id = self.api_subnets.first()['id']
        router_id = self.api_routers.first()['id']

        quantumclient = self.stub_quantumclient()
        form_data = {'subnet_id': subnet_id}
        quantumclient.add_interface_router(
            router_id, form_data).AndReturn(None)
        self.mox.ReplayAll()

        api.quantum.router_add_interface(
            self.request, router_id, subnet_id=subnet_id)

    def test_router_remove_interface(self):
        router_id = self.api_routers.first()['id']
        fake_port = self.api_ports.first()['id']

        quantumclient = self.stub_quantumclient()
        quantumclient.remove_interface_router(
            router_id, {'port_id': fake_port})
        self.mox.ReplayAll()

        api.quantum.router_remove_interface(
            self.request, router_id, port_id=fake_port)
