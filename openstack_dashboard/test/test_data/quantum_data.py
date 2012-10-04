# Copyright 2012 Nebula, Inc.
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

from openstack_dashboard.api.quantum import Network, Subnet, Port

from .utils import TestDataContainer


def data(TEST):
    # data returned by openstack_dashboard.api.quantum wrapper
    TEST.networks = TestDataContainer()
    TEST.subnets = TestDataContainer()
    TEST.ports = TestDataContainer()

    # data return by quantumclient
    TEST.api_networks = TestDataContainer()
    TEST.api_subnets = TestDataContainer()
    TEST.api_ports = TestDataContainer()

    # 1st network
    network_dict = {'admin_state_up': True,
                    'id': '82288d84-e0a5-42ac-95be-e6af08727e42',
                    'name': 'net1',
                    'status': 'ACTIVE',
                    'subnets': ['e8abc972-eb0c-41f1-9edd-4bc6e3bcd8c9'],
                    'tenant_id': '1',
                    'shared': False}
    subnet_dict = {'allocation_pools': [{'end': '10.0.0.254',
                                         'start': '10.0.0.2'}],
                   'cidr': '10.0.0.0/24',
                   'enable_dhcp': True,
                   'gateway_ip': '10.0.0.1',
                   'id': network_dict['subnets'][0],
                   'ip_version': 4,
                   'name': 'mysubnet1',
                   'network_id': network_dict['id'],
                   'tenant_id': network_dict['tenant_id']}
    port_dict = {'admin_state_up': True,
                 'device_id': 'af75c8e5-a1cc-4567-8d04-44fcd6922890',
                 'fixed_ips': [{'ip_address': '10.0.0.3',
                                'subnet_id': subnet_dict['id']}],
                 'id': '3ec7f3db-cb2f-4a34-ab6b-69a64d3f008c',
                 'mac_address': 'fa:16:3e:9c:d5:7e',
                 'name': '',
                 'network_id': network_dict['id'],
                 'status': 'ACTIVE',
                 'tenant_id': network_dict['tenant_id']}

    TEST.api_networks.add(network_dict)
    TEST.api_subnets.add(subnet_dict)
    TEST.api_ports.add(port_dict)

    network = copy.deepcopy(network_dict)
    subnet = Subnet(subnet_dict)
    network['subnets'] = [subnet]
    TEST.networks.add(Network(network))
    TEST.subnets.add(subnet)
    TEST.ports.add(Port(port_dict))

    # 2nd network
    network_dict = {'admin_state_up': True,
                    'id': '72c3ab6c-c80f-4341-9dc5-210fa31ac6c2',
                    'name': 'net2',
                    'status': 'ACTIVE',
                    'subnets': ['3f7c5d79-ee55-47b0-9213-8e669fb03009'],
                    'tenant_id': '2',
                    'shared': True}
    subnet_dict = {'allocation_pools': [{'end': '172.16.88.254',
                                          'start': '172.16.88.2'}],
                   'cidr': '172.16.88.0/24',
                   'enable_dhcp': True,
                   'gateway_ip': '172.16.88.1',
                   'id': '3f7c5d79-ee55-47b0-9213-8e669fb03009',
                   'ip_version': 4,
                   'name': 'aaaa',
                   'network_id': network_dict['id'],
                   'tenant_id': network_dict['tenant_id']}
    port_dict = {'admin_state_up': True,
                 'device_id': '40e536b1-b9fd-4eb7-82d6-84db5d65a2ac',
                 'fixed_ips': [{'ip_address': '172.16.88.3',
                                'subnet_id': subnet_dict['id']}],
                 'id': '7e6ce62c-7ea2-44f8-b6b4-769af90a8406',
                 'mac_address': 'fa:16:3e:56:e6:2f',
                 'name': '',
                 'network_id': network_dict['id'],
                 'status': 'ACTIVE',
                 'tenant_id': network_dict['tenant_id']}

    TEST.api_networks.add(network_dict)
    TEST.api_subnets.add(subnet_dict)
    TEST.api_ports.add(port_dict)

    network = copy.deepcopy(network_dict)
    subnet = Subnet(subnet_dict)
    network['subnets'] = [subnet]
    TEST.networks.add(Network(network))
    TEST.subnets.add(subnet)
    TEST.ports.add(Port(port_dict))
