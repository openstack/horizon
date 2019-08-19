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

from oslo_utils import uuidutils

from openstack_dashboard.api import base
from openstack_dashboard.api import neutron
from openstack_dashboard.test.test_data import utils
from openstack_dashboard.usage import quotas as usage_quotas


def data(TEST):
    # Data returned by openstack_dashboard.api.neutron wrapper.
    TEST.agents = utils.TestDataContainer()
    TEST.networks = utils.TestDataContainer()
    TEST.subnets = utils.TestDataContainer()
    TEST.subnetpools = utils.TestDataContainer()
    TEST.ports = utils.TestDataContainer()
    TEST.trunks = utils.TestDataContainer()
    TEST.routers = utils.TestDataContainer()
    TEST.routers_with_rules = utils.TestDataContainer()
    TEST.routers_with_routes = utils.TestDataContainer()
    TEST.floating_ips = utils.TestDataContainer()
    TEST.security_groups = utils.TestDataContainer()
    TEST.security_group_rules = utils.TestDataContainer()
    TEST.providers = utils.TestDataContainer()
    TEST.pools = utils.TestDataContainer()
    TEST.vips = utils.TestDataContainer()
    TEST.members = utils.TestDataContainer()
    TEST.monitors = utils.TestDataContainer()
    TEST.neutron_quotas = utils.TestDataContainer()
    TEST.neutron_quota_usages = utils.TestDataContainer()
    TEST.ip_availability = utils.TestDataContainer()
    TEST.qos_policies = utils.TestDataContainer()
    TEST.rbac_policies = utils.TestDataContainer()
    TEST.tp_ports = utils.TestDataContainer()
    TEST.neutron_availability_zones = utils.TestDataContainer()

    # Data return by neutronclient.
    TEST.api_agents = utils.TestDataContainer()
    TEST.api_networks = utils.TestDataContainer()
    TEST.api_subnets = utils.TestDataContainer()
    TEST.api_subnetpools = utils.TestDataContainer()
    TEST.api_ports = utils.TestDataContainer()
    TEST.api_trunks = utils.TestDataContainer()
    TEST.api_routers = utils.TestDataContainer()
    TEST.api_routers_with_routes = utils.TestDataContainer()
    TEST.api_floating_ips = utils.TestDataContainer()
    TEST.api_security_groups = utils.TestDataContainer()
    TEST.api_security_group_rules = utils.TestDataContainer()
    TEST.api_pools = utils.TestDataContainer()
    TEST.api_vips = utils.TestDataContainer()
    TEST.api_members = utils.TestDataContainer()
    TEST.api_monitors = utils.TestDataContainer()
    TEST.api_extensions = utils.TestDataContainer()
    TEST.api_ip_availability = utils.TestDataContainer()
    TEST.api_rbac_policies = utils.TestDataContainer()
    TEST.api_qos_policies = utils.TestDataContainer()
    TEST.api_tp_trunks = utils.TestDataContainer()
    TEST.api_tp_ports = utils.TestDataContainer()

    # 1st network.
    network_dict = {'admin_state_up': True,
                    'id': '82288d84-e0a5-42ac-95be-e6af08727e42',
                    'name': 'net1',
                    'status': 'ACTIVE',
                    'subnets': ['e8abc972-eb0c-41f1-9edd-4bc6e3bcd8c9',
                                '41e53a49-442b-4307-9e9a-88967a6b6657'],
                    'tenant_id': '1',
                    'router:external': False,
                    'shared': False}
    subnet_dict = {'allocation_pools': [{'end': '10.0.0.254',
                                         'start': '10.0.0.2'}],
                   'dns_nameservers': [],
                   'host_routes': [],
                   'cidr': '10.0.0.0/24',
                   'enable_dhcp': True,
                   'gateway_ip': '10.0.0.1',
                   'id': network_dict['subnets'][0],
                   'ip_version': 4,
                   'name': 'mysubnet1',
                   'network_id': network_dict['id'],
                   'tenant_id': network_dict['tenant_id']}
    subnetv6_dict = {
        'allocation_pools': [{'start': 'fdb6:b88a:488e::2',
                              'end': 'fdb6:b88a:488e:0:ffff:ffff:ffff:ffff'}],
        'dns_nameservers': [],
        'host_routes': [],
        'cidr': 'fdb6:b88a:488e::/64',
        'enable_dhcp': True,
        'gateway_ip': 'fdb6:b88a:488e::1',
        'id': network_dict['subnets'][1],
        'ip_version': 6,
        'name': 'myv6subnet',
        'network_id': network_dict['id'],
        'tenant_id': network_dict['tenant_id'],
        'ipv6_ra_mode': 'slaac',
        'ipv6_address_mode': 'slaac'
    }

    TEST.api_networks.add(network_dict)
    TEST.api_subnets.add(subnet_dict)
    TEST.api_subnets.add(subnetv6_dict)

    network = copy.deepcopy(network_dict)
    subnet = neutron.Subnet(subnet_dict)
    subnetv6 = neutron.Subnet(subnetv6_dict)
    network['subnets'] = [subnet, subnetv6]
    TEST.networks.add(neutron.Network(network))
    TEST.subnets.add(subnet)
    TEST.subnets.add(subnetv6)

    # Ports on 1st network.
    port_dict = {
        'admin_state_up': True,
        'device_id': 'af75c8e5-a1cc-4567-8d04-44fcd6922890',
        'device_owner': 'network:dhcp',
        'fixed_ips': [{'ip_address': '10.0.0.3',
                       'subnet_id': subnet_dict['id']}],
        'id': '063cf7f3-ded1-4297-bc4c-31eae876cc91',
        'mac_address': 'fa:16:3e:9c:d5:7e',
        'name': '',
        'network_id': network_dict['id'],
        'status': 'ACTIVE',
        'tenant_id': network_dict['tenant_id'],
        'binding:vnic_type': 'normal',
        'binding:host_id': 'host',
        'allowed_address_pairs': [
            {'ip_address': '174.0.0.201',
             'mac_address': 'fa:16:3e:7a:7b:18'}
        ],
        'port_security_enabled': True,
        'security_groups': [],
    }

    TEST.api_ports.add(port_dict)
    TEST.ports.add(neutron.Port(port_dict))

    port_dict = {
        'admin_state_up': True,
        'device_id': '1',
        'device_owner': 'compute:nova',
        'fixed_ips': [{'ip_address': '10.0.0.4',
                       'subnet_id': subnet_dict['id']},
                      {'ip_address': 'fdb6:b88a:488e:0:f816:3eff:fe9d:e62f',
                       'subnet_id': subnetv6_dict['id']}],
        'id': '7e6ce62c-7ea2-44f8-b6b4-769af90a8406',
        'mac_address': 'fa:16:3e:9d:e6:2f',
        'name': '',
        'network_id': network_dict['id'],
        'status': 'ACTIVE',
        'tenant_id': network_dict['tenant_id'],
        'binding:vnic_type': 'normal',
        'binding:host_id': 'host',
        'port_security_enabled': True,
        'security_groups': [
            # sec_group_1 ID below
            'faad7c80-3b62-4440-967c-13808c37131d',
            # sec_group_2 ID below
            '27a5c9a1-bdbb-48ac-833a-2e4b5f54b31d'
        ],
    }
    TEST.api_ports.add(port_dict)
    TEST.ports.add(neutron.Port(port_dict))
    assoc_port = port_dict

    port_dict = {
        'admin_state_up': True,
        'device_id': '279989f7-54bb-41d9-ba42-0d61f12fda61',
        'device_owner': 'network:router_interface',
        'fixed_ips': [{'ip_address': '10.0.0.1',
                       'subnet_id': subnet_dict['id']}],
        'id': '9036eedb-e7fa-458e-bc6e-d9d06d9d1bc4',
        'mac_address': 'fa:16:3e:9c:d5:7f',
        'name': '',
        'network_id': network_dict['id'],
        'status': 'ACTIVE',
        'tenant_id': network_dict['tenant_id'],
        'binding:vnic_type': 'normal',
        'binding:host_id': 'host',
        'security_groups': [],
    }
    TEST.api_ports.add(port_dict)
    TEST.ports.add(neutron.Port(port_dict))
    port_dict = {
        'admin_state_up': True,
        'device_id': '279989f7-54bb-41d9-ba42-0d61f12fda61',
        'device_owner': 'network:router_interface',
        'fixed_ips': [{'ip_address': 'fdb6:b88a:488e::1',
                       'subnet_id': subnetv6_dict['id']}],
        'id': '8047e0d5-5ef5-4b6e-a1a7-d3a52ad980f7',
        'mac_address': 'fa:16:3e:69:6e:e9',
        'name': '',
        'network_id': network_dict['id'],
        'status': 'ACTIVE',
        'tenant_id': network_dict['tenant_id'],
        'binding:vnic_type': 'normal',
        'binding:host_id': 'host',
        'security_groups': [],
    }
    TEST.api_ports.add(port_dict)
    TEST.ports.add(neutron.Port(port_dict))

    # 2nd network.
    network_dict = {'admin_state_up': True,
                    'id': '72c3ab6c-c80f-4341-9dc5-210fa31ac6c2',
                    'name': 'net2',
                    'status': 'ACTIVE',
                    'subnets': ['3f7c5d79-ee55-47b0-9213-8e669fb03009'],
                    'tenant_id': '2',
                    'router:external': False,
                    'shared': True}
    subnet_dict = {'allocation_pools': [{'end': '172.16.88.254',
                                         'start': '172.16.88.2'}],
                   'dns_nameservers': ['10.56.1.20', '10.56.1.21'],
                   'host_routes': [{'destination': '192.168.20.0/24',
                                    'nexthop': '172.16.88.253'},
                                   {'destination': '192.168.21.0/24',
                                    'nexthop': '172.16.88.252'}],
                   'cidr': '172.16.88.0/24',
                   'enable_dhcp': True,
                   'gateway_ip': '172.16.88.1',
                   'id': '3f7c5d79-ee55-47b0-9213-8e669fb03009',
                   'ip_version': 4,
                   'name': 'aaaa',
                   'network_id': network_dict['id'],
                   'tenant_id': network_dict['tenant_id']}

    TEST.api_networks.add(network_dict)
    TEST.api_subnets.add(subnet_dict)

    network = copy.deepcopy(network_dict)
    subnet = neutron.Subnet(subnet_dict)
    network['subnets'] = [subnet]
    TEST.networks.add(neutron.Network(network))
    TEST.subnets.add(subnet)

    port_dict = {
        'admin_state_up': True,
        'device_id': '2',
        'device_owner': 'compute:nova',
        'fixed_ips': [{'ip_address': '172.16.88.3',
                       'subnet_id': subnet_dict['id']}],
        'id': '1db2cc37-3553-43fa-b7e2-3fc4eb4f9905',
        'mac_address': 'fa:16:3e:56:e6:2f',
        'name': '',
        'network_id': network_dict['id'],
        'status': 'ACTIVE',
        'tenant_id': network_dict['tenant_id'],
        'binding:vnic_type': 'normal',
        'binding:host_id': 'host',
        'security_groups': [
            # sec_group_1 ID below
            'faad7c80-3b62-4440-967c-13808c37131d',
        ],
    }

    TEST.api_ports.add(port_dict)
    TEST.ports.add(neutron.Port(port_dict))

    # External network.
    network_dict = {'admin_state_up': True,
                    'id': '9b466b94-213a-4cda-badf-72c102a874da',
                    'name': 'ext_net',
                    'status': 'ACTIVE',
                    'subnets': ['d6bdc71c-7566-4d32-b3ff-36441ce746e8'],
                    'tenant_id': '3',
                    'router:external': True,
                    'shared': False}
    subnet_dict = {'allocation_pools': [{'start': '172.24.4.226.',
                                         'end': '172.24.4.238'}],
                   'dns_nameservers': [],
                   'host_routes': [],
                   'cidr': '172.24.4.0/28',
                   'enable_dhcp': False,
                   'gateway_ip': '172.24.4.225',
                   'id': 'd6bdc71c-7566-4d32-b3ff-36441ce746e8',
                   'ip_version': 4,
                   'name': 'ext_subnet',
                   'network_id': network_dict['id'],
                   'tenant_id': network_dict['tenant_id']}
    ext_net = network_dict

    TEST.api_networks.add(network_dict)
    TEST.api_subnets.add(subnet_dict)

    network = copy.deepcopy(network_dict)
    subnet = neutron.Subnet(subnet_dict)
    network['subnets'] = [subnet]
    TEST.networks.add(neutron.Network(network))
    TEST.subnets.add(subnet)

    # 1st v6 network.
    network_dict = {'admin_state_up': True,
                    'id': '96688ea1-ffa5-78ec-22ca-33aaabfaf775',
                    'name': 'v6_net1',
                    'status': 'ACTIVE',
                    'subnets': ['88ddd443-4377-ab1f-87dd-4bc4a662dbb6'],
                    'tenant_id': '1',
                    'router:external': False,
                    'shared': False}
    subnet_dict = {'allocation_pools': [{'end': 'ff09::ff',
                                         'start': 'ff09::02'}],
                   'dns_nameservers': [],
                   'host_routes': [],
                   'cidr': 'ff09::/64',
                   'enable_dhcp': True,
                   'gateway_ip': 'ff09::1',
                   'id': network_dict['subnets'][0],
                   'ip_version': 6,
                   'name': 'v6_subnet1',
                   'network_id': network_dict['id'],
                   'tenant_id': network_dict['tenant_id'],
                   'ipv6_modes': 'none/none'}

    TEST.api_networks.add(network_dict)
    TEST.api_subnets.add(subnet_dict)

    network = copy.deepcopy(network_dict)
    subnet = neutron.Subnet(subnet_dict)
    network['subnets'] = [subnet]
    TEST.networks.add(neutron.Network(network))
    TEST.subnets.add(subnet)

    # 2nd v6 network - slaac.
    network_dict = {'admin_state_up': True,
                    'id': 'c62e4bb3-296a-4cd1-8f6b-aaa7a0092326',
                    'name': 'v6_net2',
                    'status': 'ACTIVE',
                    'subnets': ['5d736a21-0036-4779-8f8b-eed5f98077ec'],
                    'tenant_id': '1',
                    'router:external': False,
                    'shared': False}
    subnet_dict = {'allocation_pools': [{'end': 'ff09::ff',
                                         'start': 'ff09::02'}],
                   'dns_nameservers': [],
                   'host_routes': [],
                   'cidr': 'ff09::/64',
                   'enable_dhcp': True,
                   'gateway_ip': 'ff09::1',
                   'id': network_dict['subnets'][0],
                   'ip_version': 6,
                   'name': 'v6_subnet2',
                   'network_id': network_dict['id'],
                   'tenant_id': network_dict['tenant_id'],
                   'ipv6_modes': 'slaac/slaac'}

    TEST.api_networks.add(network_dict)
    TEST.api_subnets.add(subnet_dict)

    network = copy.deepcopy(network_dict)
    subnet = neutron.Subnet(subnet_dict)
    network['subnets'] = [subnet]
    TEST.networks.add(neutron.Network(network))
    TEST.subnets.add(subnet)

    # Set up router data.
    port_dict = {
        'admin_state_up': True,
        'device_id': '7180cede-bcd8-4334-b19f-f7ef2f331f53',
        'device_owner': 'network:router_gateway',
        'fixed_ips': [{'ip_address': '10.0.0.3',
                       'subnet_id': subnet_dict['id']}],
        'id': '44ec6726-4bdc-48c5-94d4-df8d1fbf613b',
        'mac_address': 'fa:16:3e:9c:d5:7e',
        'name': '',
        'network_id': TEST.networks.get(name="ext_net")['id'],
        'status': 'ACTIVE',
        'tenant_id': '1',
        'binding:vnic_type': 'normal',
        'binding:host_id': 'host',
        'security_groups': [],
    }
    TEST.api_ports.add(port_dict)
    TEST.ports.add(neutron.Port(port_dict))

    trunk_dict = {'status': 'UP',
                  'sub_ports': [],
                  'name': 'trunk1',
                  'description': 'blah',
                  'admin_state_up': True,
                  'tenant_id': '1',
                  'project_id': '1',
                  'port_id': '895d375c-1447-11e7-a52f-f7f280bbc809',
                  'id': '94fcb9e8-1447-11e7-bed6-8b8c4ac74491'}

    TEST.api_trunks.add(trunk_dict)
    TEST.trunks.add(neutron.Trunk(trunk_dict))

    router_dict = {'id': '279989f7-54bb-41d9-ba42-0d61f12fda61',
                   'name': 'router1',
                   'status': 'ACTIVE',
                   'admin_state_up': True,
                   'distributed': True,
                   'external_gateway_info':
                       {'network_id': ext_net['id']},
                   'tenant_id': '1',
                   'availability_zone_hints': ['nova']}
    TEST.api_routers.add(router_dict)
    TEST.routers.add(neutron.Router(router_dict))
    router_dict = {'id': '10e3dc42-1ce1-4d48-87cf-7fc333055d6c',
                   'name': 'router2',
                   'status': 'ACTIVE',
                   'admin_state_up': False,
                   'distributed': False,
                   'external_gateway_info': None,
                   'tenant_id': '1'}
    TEST.api_routers.add(router_dict)
    TEST.routers.add(neutron.Router(router_dict))
    router_dict = {'id': '7180cede-bcd8-4334-b19f-f7ef2f331f53',
                   'name': 'rulerouter',
                   'status': 'ACTIVE',
                   'admin_state_up': True,
                   'distributed': False,
                   'external_gateway_info':
                       {'network_id': ext_net['id']},
                   'tenant_id': '1',
                   'router_rules': [{'id': '101',
                                     'action': 'deny',
                                     'source': 'any',
                                     'destination': 'any',
                                     'nexthops': []},
                                    {'id': '102',
                                     'action': 'permit',
                                     'source': 'any',
                                     'destination': '8.8.8.8/32',
                                     'nexthops': ['1.0.0.2', '1.0.0.1']}]}
    TEST.api_routers.add(router_dict)
    TEST.routers_with_rules.add(neutron.Router(router_dict))
    router_dict_with_route = {'id': '725c24c9-061b-416b-b9d4-012392b32fd9',
                              'name': 'routerouter',
                              'status': 'ACTIVE',
                              'admin_state_up': True,
                              'distributed': False,
                              'external_gateway_info':
                                  {'network_id': ext_net['id']},
                              'tenant_id': '1',
                              'routes': [{'nexthop': '10.0.0.1',
                                          'destination': '172.0.0.0/24'},
                                         {'nexthop': '10.0.0.2',
                                          'destination': '172.1.0.0/24'}]}
    TEST.api_routers_with_routes.add(router_dict_with_route)
    TEST.routers_with_routes.add(neutron.Router(router_dict_with_route))

    # Floating IP.
    # Unassociated.
    fip_dict = {'tenant_id': '1',
                'floating_ip_address': '172.16.88.227',
                'floating_network_id': ext_net['id'],
                'id': '9012cd70-cfae-4e46-b71e-6a409e9e0063',
                'fixed_ip_address': None,
                'port_id': None,
                'router_id': None}
    TEST.api_floating_ips.add(fip_dict)
    fip_with_instance = copy.deepcopy(fip_dict)
    fip_with_instance.update({'instance_id': None,
                              'instance_type': None})
    TEST.floating_ips.add(neutron.FloatingIp(fip_with_instance))

    # Associated (with compute port on 1st network).
    fip_dict = {'tenant_id': '1',
                'floating_ip_address': '172.16.88.228',
                'floating_network_id': ext_net['id'],
                'id': 'a97af8f2-3149-4b97-abbd-e49ad19510f7',
                'fixed_ip_address': assoc_port['fixed_ips'][0]['ip_address'],
                'port_id': assoc_port['id'],
                'router_id': router_dict['id']}
    TEST.api_floating_ips.add(fip_dict)
    fip_with_instance = copy.deepcopy(fip_dict)
    fip_with_instance.update({'instance_id': '1',
                              'instance_type': 'compute'})
    TEST.floating_ips.add(neutron.FloatingIp(fip_with_instance))

    # Security group.

    sec_group_1 = {'tenant_id': '1',
                   'description': 'default',
                   'id': 'faad7c80-3b62-4440-967c-13808c37131d',
                   'name': 'default'}
    sec_group_2 = {'tenant_id': '1',
                   'description': 'NotDefault',
                   'id': '27a5c9a1-bdbb-48ac-833a-2e4b5f54b31d',
                   'name': 'other_group'}
    sec_group_3 = {'tenant_id': '1',
                   'description': 'NotDefault',
                   'id': '443a4d7a-4bd2-4474-9a77-02b35c9f8c95',
                   'name': 'another_group'}
    sec_group_empty = {'tenant_id': '1',
                       'description': 'SG without rules',
                       'id': 'f205f3bc-d402-4e40-b004-c62401e19b4b',
                       'name': 'empty_group'}

    def add_rule_to_group(secgroup, default_only=True):
        rule_egress_ipv4 = {
            'id': uuidutils.generate_uuid(),
            'direction': u'egress', 'ethertype': u'IPv4',
            'port_range_min': None, 'port_range_max': None,
            'protocol': None, 'remote_group_id': None,
            'remote_ip_prefix': None,
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id'],
            'description': "Egrress IPv4 rule",
        }
        rule_egress_ipv6 = {
            'id': uuidutils.generate_uuid(),
            'direction': u'egress', 'ethertype': u'IPv6',
            'port_range_min': None, 'port_range_max': None,
            'protocol': None, 'remote_group_id': None,
            'remote_ip_prefix': None,
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id'],
            'description': 'Egress IPv6 rule',
        }
        rule_tcp_80 = {
            'id': uuidutils.generate_uuid(),
            'direction': u'ingress', 'ethertype': u'IPv4',
            'port_range_min': 80, 'port_range_max': 80,
            'protocol': u'tcp', 'remote_group_id': None,
            'remote_ip_prefix': u'0.0.0.0/0',
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id'],
            'description': 'Ingress HTTP',
        }
        rule_icmp = {
            'id': uuidutils.generate_uuid(),
            'direction': u'ingress', 'ethertype': u'IPv4',
            'port_range_min': 5, 'port_range_max': 8,
            'protocol': u'icmp', 'remote_group_id': None,
            'remote_ip_prefix': u'0.0.0.0/0',
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id'],
            'description': 'Ingress IPv4 ICMP',
        }
        rule_group = {
            'id': uuidutils.generate_uuid(),
            'direction': u'ingress', 'ethertype': u'IPv4',
            'port_range_min': 80, 'port_range_max': 80,
            'protocol': u'tcp', 'remote_group_id': sec_group_1['id'],
            'remote_ip_prefix': None,
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id'],
            'description': 'Ingress HTTP from SG #1',
        }
        rule_ip_proto = {
            'id': uuidutils.generate_uuid(),
            'direction': u'ingress', 'ethertype': u'IPv4',
            'port_range_min': None, 'port_range_max': None,
            'protocol': u'99', 'remote_group_id': None,
            'remote_ip_prefix': u'0.0.0.0/24',
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id'],
            'description': 'Ingress custom IP protocol 99',
        }
        rule_all_tcp = {
            'id': uuidutils.generate_uuid(),
            'direction': u'egress', 'ethertype': u'IPv4',
            'port_range_min': 1, 'port_range_max': 65535,
            'protocol': u'tcp', 'remote_group_id': None,
            'remote_ip_prefix': u'0.0.0.0/24',
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id'],
            'description': 'Egress all TCP',
        }

        rules = []
        if not default_only:
            rules += [rule_tcp_80, rule_icmp, rule_group, rule_all_tcp,
                      rule_ip_proto]
        rules += [rule_egress_ipv4, rule_egress_ipv6]
        secgroup['security_group_rules'] = rules

    add_rule_to_group(sec_group_1, default_only=False)
    add_rule_to_group(sec_group_2)
    add_rule_to_group(sec_group_3)
    # NOTE: sec_group_empty is a SG without rules,
    # so we don't call add_rule_to_group.

    groups = [sec_group_1, sec_group_2, sec_group_3, sec_group_empty]
    sg_name_dict = dict([(sg['id'], sg['name']) for sg in groups])
    for sg in groups:
        # Neutron API.
        TEST.api_security_groups.add(sg)
        for rule in sg.get('security_group_rules', []):
            TEST.api_security_group_rules.add(copy.copy(rule))
        # OpenStack Dashboard internaly API.
        TEST.security_groups.add(
            neutron.SecurityGroup(copy.deepcopy(sg), sg_name_dict))
        for rule in sg.get('security_group_rules', []):
            TEST.security_group_rules.add(
                neutron.SecurityGroupRule(copy.copy(rule), sg_name_dict))

    # Subnetpools

    # 1st subnetpool
    subnetpool_dict = {'default_prefixlen': 24,
                       'default_quota': None,
                       'id': '419eb314-e244-4088-aed7-851af9d9500d',
                       'ip_version': 4,
                       'max_prefixlen': 32,
                       'min_prefixlen': 12,
                       'name': 'mysubnetpool1',
                       'prefixes': ['172.16.0.0/12'],
                       'shared': False,
                       'tenant_id': '1'}

    TEST.api_subnetpools.add(subnetpool_dict)
    subnetpool = neutron.SubnetPool(subnetpool_dict)
    TEST.subnetpools.add(subnetpool)

    # 2nd subnetpool (v6)
    subnetpool_dict = {'default_prefixlen': 64,
                       'default_quota': None,
                       'id': 'dcdad289-46f3-4298-bec6-41d91c942efa',
                       'ip_version': 6,
                       'max_prefixlen': 64,
                       'min_prefixlen': 60,
                       'name': 'mysubnetpool2',
                       'prefixes': ['2001:db8:42::/48'],
                       'shared': False,
                       'tenant_id': '1'}

    TEST.api_subnetpools.add(subnetpool_dict)
    subnetpool = neutron.SubnetPool(subnetpool_dict)
    TEST.subnetpools.add(subnetpool)

    # Quotas.
    quota_data = {'network': '10',
                  'subnet': '10',
                  'port': '50',
                  'router': '10',
                  'floatingip': '50',
                  'security_group': '20',
                  'security_group_rule': '100',
                  }
    TEST.neutron_quotas.add(base.QuotaSet(quota_data))

    # Quota Usages
    quota_usage_data = {
        'network': {'used': 0, 'quota': 5},
        'subnet': {'used': 0, 'quota': 5},
        'port': {'used': 0, 'quota': 5},
        'router': {'used': 0, 'quota': 5},
        'floatingip': {'used': 0, 'quota': 50},
        'security_group': {'used': 0, 'quota': 20},
        'security_group_rule': {'used': 0, 'quota': 100},
    }
    quota_usage = usage_quotas.QuotaUsage()
    for k, v in quota_usage_data.items():
        quota_usage.add_quota(base.Quota(k, v['quota']))
        quota_usage.tally(k, v['used'])

    TEST.neutron_quota_usages.add(quota_usage)

    # Extensions.
    extension_1 = {"name": "security-group",
                   "alias": "security-group",
                   "description": "The security groups extension."}
    extension_2 = {"name": "Quota management support",
                   "alias": "quotas",
                   "description": "Expose functions for quotas management"}
    extension_3 = {"name": "Provider network",
                   "alias": "provider",
                   "description": "Provider network extension"}
    extension_4 = {"name": "Distributed Virtual Router",
                   "alias": "dvr",
                   "description":
                   "Enables configuration of Distributed Virtual Routers."}
    extension_5 = {"name": "HA Router extension",
                   "alias": "l3-ha",
                   "description": "Add HA capability to routers."}
    extension_6 = {"name": "Trunks",
                   "alias": "trunk",
                   "description": "Provides support for trunk ports."}
    TEST.api_extensions.add(extension_1)
    TEST.api_extensions.add(extension_2)
    TEST.api_extensions.add(extension_3)
    TEST.api_extensions.add(extension_4)
    TEST.api_extensions.add(extension_5)
    TEST.api_extensions.add(extension_6)

    # 1st agent.
    agent_dict = {"binary": "neutron-openvswitch-agent",
                  "description": None,
                  "admin_state_up": True,
                  "heartbeat_timestamp": "2013-07-26 06:51:47",
                  "alive": True,
                  "id": "c876ff05-f440-443e-808c-1d34cda3e88a",
                  "topic": "N/A",
                  "host": "devstack001",
                  "agent_type": "Open vSwitch agent",
                  "started_at": "2013-07-26 05:23:28",
                  "created_at": "2013-07-26 05:23:28",
                  "configurations": {"devices": 2}}
    TEST.api_agents.add(agent_dict)
    TEST.agents.add(neutron.Agent(agent_dict))

    # 2nd agent.
    agent_dict = {"binary": "neutron-dhcp-agent",
                  "description": None,
                  "admin_state_up": True,
                  "heartbeat_timestamp": "2013-07-26 06:51:48",
                  "alive": True,
                  "id": "f0d12e3d-1973-41a2-b977-b95693f9a8aa",
                  "topic": "dhcp_agent",
                  "host": "devstack001",
                  "agent_type": "DHCP agent",
                  "started_at": "2013-07-26 05:23:30",
                  "created_at": "2013-07-26 05:23:30",
                  "configurations": {
                      "subnets": 1,
                      "use_namespaces": True,
                      "dhcp_lease_duration": 120,
                      "dhcp_driver": "neutron.agent.linux.dhcp.Dnsmasq",
                      "networks": 1,
                      "ports": 1}}
    TEST.api_agents.add(agent_dict)
    TEST.agents.add(neutron.Agent(agent_dict))

    # Service providers.
    provider_1 = {"service_type": "LOADBALANCER",
                  "name": "haproxy",
                  "default": True}
    TEST.providers.add(provider_1)

    # ports on 4th network
    port_dict = {
        'admin_state_up': True,
        'device_id': '9872faaa-b2b2-eeee-9911-21332eedaa77',
        'device_owner': 'network:dhcp',
        'fixed_ips': [{'ip_address': '11.10.0.3',
                       'subnet_id':
                       TEST.subnets.first().id}],
        'id': 'a21dcd22-6733-cccc-aa32-22adafaf16a2',
        'mac_address': '78:22:ff:1a:ba:23',
        'name': 'port5',
        'network_id': TEST.networks.first().id,
        'status': 'ACTIVE',
        'tenant_id': TEST.networks.first().tenant_id,
        'binding:vnic_type': 'normal',
        'binding:host_id': 'host',
        'security_groups': [],
    }
    TEST.api_ports.add(port_dict)
    TEST.ports.add(neutron.Port(port_dict))

    availability = {'network_ip_availability': {
        'used_ips': 2,
        'subnet_ip_availability': [{
            'used_ips': 1,
            'subnet_id': '2c90f321-9cc7-41b4-a3cf-88110f120a94',
            'subnet_name': 'ipv6-public-subnet',
            'ip_version': 6,
            'cidr': '2001:db8::/64',
            'total_ips': 18446744073709551614},
            {'used_ips': 1,
             'subnet_id': '4d77d5fb-c26c-4ac5-b2ca-fca2f89b0fc1',
             'subnet_name': 'public-subnet',
             'ip_version': 4,
             'cidr': '172.24.4.0/24',
             'total_ips': 253}],
        'network_id': 'd87d5be5-cfca-486f-8db5-a446330e4513',
        'tenant_id': 'd564b2a4fc0544fb89f8a0434dd96863',
        'network_name': 'public',
        'total_ips': 18446744073709551867}
    }

    TEST.ip_availability.add(availability)
    TEST.api_ip_availability.add(availability)

    # qos policies
    policy_dict = {'id': 'a21dcd22-7189-cccc-aa32-22adafaf16a7',
                   'name': 'policy 1',
                   'tenant_id': '1'}
    TEST.api_qos_policies.add(policy_dict)
    TEST.qos_policies.add(neutron.QoSPolicy(policy_dict))
    policy_dict1 = {'id': 'a21dcd22-7189-ssss-aa32-22adafaf16a7',
                    'name': 'policy 2',
                    'tenant_id': '1'}
    TEST.api_qos_policies.add(policy_dict1)
    TEST.qos_policies.add(neutron.QoSPolicy(policy_dict1))

    # rbac policies
    rbac_policy_dict = {"project_id": "1",
                        "object_type": "network",
                        "id": "7f27e61a-9863-448a-a769-eb922fdef3f8",
                        "object_id": "82288d84-e0a5-42ac-95be-e6af08727e42",
                        "target_tenant": "2",
                        "action": "access_as_external",
                        "tenant_id": "1"}
    TEST.api_rbac_policies.add(rbac_policy_dict)
    TEST.rbac_policies.add(neutron.RBACPolicy(rbac_policy_dict))
    rbac_policy_dict1 = {"project_id": "1",
                         "object_type": "qos_policy",
                         "id": "7f27e61a-9863-448a-a769-eb922fdef3f8",
                         "object_id": "a21dcd22-7189-cccc-aa32-22adafaf16a7",
                         "target_tenant": "2",
                         "action": "access_as_shared",
                         "tenant_id": "1"}
    TEST.api_rbac_policies.add(rbac_policy_dict1)
    TEST.rbac_policies.add(neutron.RBACPolicy(rbac_policy_dict1))

    # TRUNKPORT
    #
    #  The test setup was created by the following command sequence:
    #    openstack network create tst
    #    openstack subnet create tstsub --network tst\
    #    --subnet-range 10.10.16.128/26
    #    openstack network create tstalt
    #    openstack subnet create tstaltsub --network tstalt\
    #    --subnet-range 10.10.17.128/26
    #    openstack port create --network tst plain
    #    openstack port create --network tst parent
    #    openstack port create --network tst child1
    #    openstack port create --network tstalt child2
    #    openstack network trunk create --parent-port parent trunk
    #    openstack network trunk set\
    #    --subport port=child1,segmentation-type=vlan,segmentation-id=100 trunk
    #    openstack network trunk set\
    #    --subport port=child2,segmentation-type=vlan,segmentation-id=200 trunk
    #   ids/uuids are captured from a live setup.

    # This collection holds the test setup.
    tdata = {'tenant_id': '19c9123a944644cb9e923497a018d0b7',
             'trunk_id': '920625a3-13de-46b4-b6c9-8b35f29b3cfe',
             'security_group': '3fd8c007-9093-4aa3-b475-a0c178d4e1e4',
             'tag_1': 100,
             'tag_2': 200,
             'net': {'tst_id': '5a340332-cc92-42aa-8980-15f47c0d0f3d',
                     'tstalt_id': '0fb41ffd-3933-4da4-8a83-025d328aedf3'},
             'subnet': {'tst_id': '0b883baf-5a21-4605-ab56-229a24ec585b',
                        'tstalt_id': '0e184cf2-97dc-4738-b4b3-1871faf5d685'},
             'child1': {'id': '9c151ffb-d7a6-4f15-8eae-d0950999fdfe',
                        'ip': '10.10.16.140',
                        'mac': 'fa:16:3e:22:63:6f',
                        'device_id': '279989f7-54bb-41d9-ba42-0d61f12fda61'},
             'child2': {'id': 'cedb145f-c163-4630-98a3-e1990744bdef',
                        'ip': '10.10.17.137',
                        'mac': 'fa:16:3e:0d:ca:eb',
                        'device_id': '9872faaa-b2b2-eeee-9911-21332eedaa77'},
             'parent': {'id': '5b27429d-048b-40fa-88f9-8e2c4ff7d28b',
                        'ip': '10.10.16.141',
                        'mac': 'fa:16:3e:ab:a8:22',
                        'device_id': 'af75c8e5-a1cc-4567-8d04-44fcd6922890'},
             'plain': {'id': 'bc04da56-d7fc-461e-b95d-a2c66e77ad9a',
                       'ip': '10.10.16.135',
                       'mac': 'fa:16:3e:9c:d5:7f',
                       'device_id': '7180cede-bcd8-4334-b19f-f7ef2f331f53'}}

    #  network tst

    #    trunk
    tp_trunk_dict = {
        'status': 'UP',
        'sub_ports': [{'segmentation_type': 'vlan',
                       'segmentation_id': tdata['tag_1'],
                       'port_id': tdata['child1']['id']},
                      {'segmentation_type': u'vlan',
                       'segmentation_id': tdata['tag_2'],
                       'port_id': tdata['child2']['id']}],
        'name': 'trunk',
        'admin_state_up': True,
        'tenant_id': tdata['tenant_id'],
        'project_id': tdata['tenant_id'],
        'port_id': tdata['parent']['id'],
        'id': tdata['trunk_id']
    }
    TEST.api_tp_trunks.add(tp_trunk_dict)

    #    port parent
    parent_port_dict = {
        'admin_state_up': True,
        'device_id': tdata['parent']['device_id'],
        'device_owner': 'compute:nova',
        'fixed_ips': [{'ip_address': tdata['parent']['ip'],
                       'subnet_id': tdata['subnet']['tst_id']}],
        'id': tdata['parent']['id'],
        'mac_address': tdata['parent']['mac'],
        'name': 'parent',
        'network_id': tdata['net']['tst_id'],
        'status': 'ACTIVE',
        'tenant_id': tdata['tenant_id'],
        'binding:vnic_type': 'normal',
        'binding:host_id': 'host',
        'security_groups': [tdata['security_group']],
        'trunk_details': {
            'sub_ports': [{'segmentation_type': 'vlan',
                           'mac_address': tdata['child1']['mac'],
                           'segmentation_id': tdata['tag_1'],
                           'port_id': tdata['child1']['id']},
                          {'segmentation_type': 'vlan',
                           'mac_address': tdata['child2']['mac'],
                           'segmentation_id': tdata['tag_2'],
                           'port_id': tdata['child2']['id']}],
            'trunk_id': tdata['trunk_id']}
    }
    TEST.api_tp_ports.add(parent_port_dict)
    TEST.tp_ports.add(neutron.PortTrunkParent(parent_port_dict))

    #    port child1
    child1_port_dict = {
        'admin_state_up': True,
        'device_id': tdata['child1']['device_id'],
        'device_owner': 'compute:nova',
        'fixed_ips': [{'ip_address': tdata['child1']['ip'],
                       'subnet_id': tdata['subnet']['tst_id']}],
        'id': tdata['child1']['id'],
        'mac_address': tdata['child1']['mac'],
        'name': 'child1',
        'network_id': tdata['net']['tst_id'],
        'status': 'ACTIVE',
        'tenant_id': tdata['tenant_id'],
        'binding:vnic_type': 'normal',
        'binding:host_id': 'host',
        'security_groups': [tdata['security_group']]
    }
    TEST.api_tp_ports.add(child1_port_dict)
    TEST.tp_ports.add(neutron.PortTrunkSubport(
        child1_port_dict,
        {'trunk_id': tdata['trunk_id'],
         'segmentation_type': 'vlan',
         'segmentation_id': tdata['tag_1']}))

    #    port plain
    port_dict = {
        'admin_state_up': True,
        'device_id': tdata['plain']['device_id'],
        'device_owner': 'compute:nova',
        'fixed_ips': [{'ip_address': tdata['plain']['ip'],
                       'subnet_id': tdata['subnet']['tst_id']}],
        'id': tdata['plain']['id'],
        'mac_address': tdata['plain']['mac'],
        'name': 'plain',
        'network_id': tdata['net']['tst_id'],
        'status': 'ACTIVE',
        'tenant_id': tdata['tenant_id'],
        'binding:vnic_type': 'normal',
        'binding:host_id': 'host',
        'security_groups': [tdata['security_group']]
    }
    TEST.api_tp_ports.add(port_dict)
    TEST.tp_ports.add(neutron.Port(port_dict))

    #  network tstalt

    #    port child2
    child2_port_dict = {
        'admin_state_up': True,
        'device_id': tdata['child2']['device_id'],
        'device_owner': 'compute:nova',
        'fixed_ips': [{'ip_address': tdata['child2']['ip'],
                       'subnet_id': tdata['subnet']['tstalt_id']}],
        'id': tdata['child2']['id'],
        'mac_address': tdata['child2']['mac'],
        'name': 'child2',
        'network_id': tdata['net']['tstalt_id'],
        'status': 'ACTIVE',
        'tenant_id': tdata['tenant_id'],
        'binding:vnic_type': 'normal',
        'binding:host_id': 'host',
        'security_groups': [tdata['security_group']]
    }
    TEST.api_tp_ports.add(child2_port_dict)
    TEST.tp_ports.add(neutron.PortTrunkSubport(
        child2_port_dict,
        {'trunk_id': tdata['trunk_id'],
         'segmentation_type': 'vlan',
         'segmentation_id': tdata['tag_2']}))

    # Availability Zones
    TEST.neutron_availability_zones.add(
        {
            'state': 'available',
            'resource': 'router',
            'name': 'nova'
        }
    )
