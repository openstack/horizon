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
import uuid

from openstack_dashboard.api import base
from openstack_dashboard.api import fwaas
from openstack_dashboard.api import lbaas
from openstack_dashboard.api import neutron
from openstack_dashboard.api import vpn
from openstack_dashboard.test.test_data import utils
from openstack_dashboard.usage import quotas as usage_quotas


def data(TEST):
    # Data returned by openstack_dashboard.api.neutron wrapper.
    TEST.agents = utils.TestDataContainer()
    TEST.networks = utils.TestDataContainer()
    TEST.subnets = utils.TestDataContainer()
    TEST.subnetpools = utils.TestDataContainer()
    TEST.ports = utils.TestDataContainer()
    TEST.routers = utils.TestDataContainer()
    TEST.routers_with_rules = utils.TestDataContainer()
    TEST.routers_with_routes = utils.TestDataContainer()
    TEST.q_floating_ips = utils.TestDataContainer()
    TEST.q_secgroups = utils.TestDataContainer()
    TEST.q_secgroup_rules = utils.TestDataContainer()
    TEST.providers = utils.TestDataContainer()
    TEST.pools = utils.TestDataContainer()
    TEST.vips = utils.TestDataContainer()
    TEST.members = utils.TestDataContainer()
    TEST.monitors = utils.TestDataContainer()
    TEST.neutron_quotas = utils.TestDataContainer()
    TEST.neutron_quota_usages = utils.TestDataContainer()
    TEST.net_profiles = utils.TestDataContainer()
    TEST.policy_profiles = utils.TestDataContainer()
    TEST.network_profile_binding = utils.TestDataContainer()
    TEST.policy_profile_binding = utils.TestDataContainer()
    TEST.vpnservices = utils.TestDataContainer()
    TEST.ikepolicies = utils.TestDataContainer()
    TEST.ipsecpolicies = utils.TestDataContainer()
    TEST.ipsecsiteconnections = utils.TestDataContainer()
    TEST.firewalls = utils.TestDataContainer()
    TEST.fw_policies = utils.TestDataContainer()
    TEST.fw_rules = utils.TestDataContainer()

    # Data return by neutronclient.
    TEST.api_agents = utils.TestDataContainer()
    TEST.api_networks = utils.TestDataContainer()
    TEST.api_subnets = utils.TestDataContainer()
    TEST.api_subnetpools = utils.TestDataContainer()
    TEST.api_ports = utils.TestDataContainer()
    TEST.api_routers = utils.TestDataContainer()
    TEST.api_routers_with_routes = utils.TestDataContainer()
    TEST.api_q_floating_ips = utils.TestDataContainer()
    TEST.api_q_secgroups = utils.TestDataContainer()
    TEST.api_q_secgroup_rules = utils.TestDataContainer()
    TEST.api_pools = utils.TestDataContainer()
    TEST.api_vips = utils.TestDataContainer()
    TEST.api_members = utils.TestDataContainer()
    TEST.api_monitors = utils.TestDataContainer()
    TEST.api_extensions = utils.TestDataContainer()
    TEST.api_net_profiles = utils.TestDataContainer()
    TEST.api_policy_profiles = utils.TestDataContainer()
    TEST.api_network_profile_binding = utils.TestDataContainer()
    TEST.api_policy_profile_binding = utils.TestDataContainer()
    TEST.api_vpnservices = utils.TestDataContainer()
    TEST.api_ikepolicies = utils.TestDataContainer()
    TEST.api_ipsecpolicies = utils.TestDataContainer()
    TEST.api_ipsecsiteconnections = utils.TestDataContainer()
    TEST.api_firewalls = utils.TestDataContainer()
    TEST.api_fw_policies = utils.TestDataContainer()
    TEST.api_fw_rules = utils.TestDataContainer()

    # 1st network.
    network_dict = {'admin_state_up': True,
                    'id': '82288d84-e0a5-42ac-95be-e6af08727e42',
                    'name': 'net1',
                    'status': 'ACTIVE',
                    'subnets': ['e8abc972-eb0c-41f1-9edd-4bc6e3bcd8c9'],
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

    TEST.api_networks.add(network_dict)
    TEST.api_subnets.add(subnet_dict)

    network = copy.deepcopy(network_dict)
    subnet = neutron.Subnet(subnet_dict)
    network['subnets'] = [subnet]
    TEST.networks.add(neutron.Network(network))
    TEST.subnets.add(subnet)

    # Network profile for network when using the cisco n1k plugin.
    net_profile_dict = {'name': 'net_profile_test1',
                        'segment_type': 'vlan',
                        'physical_network': 'phys1',
                        'segment_range': '3000-3100',
                        'id':
                        '00000000-1111-1111-1111-000000000000',
                        'project': TEST.networks.get(name="net1")['tenant_id'],
                        # vlan profiles have no sub_type or multicast_ip_range
                        'multicast_ip_range': None,
                        'sub_type': None}

    TEST.api_net_profiles.add(net_profile_dict)
    TEST.net_profiles.add(neutron.Profile(net_profile_dict))

    # Policy profile for port when using the cisco n1k plugin.
    policy_profile_dict = {'name': 'policy_profile_test1',
                           'id':
                           '00000000-9999-9999-9999-000000000000'}

    TEST.api_policy_profiles.add(policy_profile_dict)
    TEST.policy_profiles.add(neutron.Profile(policy_profile_dict))

    # Network profile binding.
    network_profile_binding_dict = {'profile_id':
                                    '00000000-1111-1111-1111-000000000000',
                                    'tenant_id': network_dict['tenant_id']}

    TEST.api_network_profile_binding.add(network_profile_binding_dict)
    TEST.network_profile_binding.add(neutron.Profile(
        network_profile_binding_dict))

    # Policy profile binding.
    policy_profile_binding_dict = {'profile_id':
                                   '00000000-9999-9999-9999-000000000000',
                                   'tenant_id': network_dict['tenant_id']}

    TEST.api_policy_profile_binding.add(policy_profile_binding_dict)
    TEST.policy_profile_binding.add(neutron.Profile(
        policy_profile_binding_dict))

    # Ports on 1st network.
    port_dict = {'admin_state_up': True,
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
                 'allowed_address_pairs': [{'ip_address': '174.0.0.201',
                                           'mac_address': 'fa:16:3e:7a:7b:18'}]
                 }

    TEST.api_ports.add(port_dict)
    TEST.ports.add(neutron.Port(port_dict))

    port_dict = {'admin_state_up': True,
                 'device_id': '1',
                 'device_owner': 'compute:nova',
                 'fixed_ips': [{'ip_address': '10.0.0.4',
                                'subnet_id': subnet_dict['id']}],
                 'id': '7e6ce62c-7ea2-44f8-b6b4-769af90a8406',
                 'mac_address': 'fa:16:3e:9d:e6:2f',
                 'name': '',
                 'network_id': network_dict['id'],
                 'status': 'ACTIVE',
                 'tenant_id': network_dict['tenant_id'],
                 'binding:vnic_type': 'normal',
                 'binding:host_id': 'host'}
    TEST.api_ports.add(port_dict)
    TEST.ports.add(neutron.Port(port_dict))
    assoc_port = port_dict

    port_dict = {'admin_state_up': True,
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
                 'binding:host_id': 'host'}
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

    port_dict = {'admin_state_up': True,
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
                 'binding:host_id': 'host'}

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
    port_dict = {'admin_state_up': True,
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
                 'binding:host_id': 'host'}
    TEST.api_ports.add(port_dict)
    TEST.ports.add(neutron.Port(port_dict))

    router_dict = {'id': '279989f7-54bb-41d9-ba42-0d61f12fda61',
                   'name': 'router1',
                   'status': 'ACTIVE',
                   'admin_state_up': True,
                   'distributed': True,
                   'external_gateway_info':
                       {'network_id': ext_net['id']},
                   'tenant_id': '1'}
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
    TEST.api_q_floating_ips.add(fip_dict)
    TEST.q_floating_ips.add(neutron.FloatingIp(fip_dict))

    # Associated (with compute port on 1st network).
    fip_dict = {'tenant_id': '1',
                'floating_ip_address': '172.16.88.228',
                'floating_network_id': ext_net['id'],
                'id': 'a97af8f2-3149-4b97-abbd-e49ad19510f7',
                'fixed_ip_address': assoc_port['fixed_ips'][0]['ip_address'],
                'port_id': assoc_port['id'],
                'router_id': router_dict['id']}
    TEST.api_q_floating_ips.add(fip_dict)
    TEST.q_floating_ips.add(neutron.FloatingIp(fip_dict))

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

    def add_rule_to_group(secgroup, default_only=True):
        rule_egress_ipv4 = {
            'id': str(uuid.uuid4()),
            'direction': u'egress', 'ethertype': u'IPv4',
            'port_range_min': None, 'port_range_max': None,
            'protocol': None, 'remote_group_id': None,
            'remote_ip_prefix': None,
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id']}
        rule_egress_ipv6 = {
            'id': str(uuid.uuid4()),
            'direction': u'egress', 'ethertype': u'IPv6',
            'port_range_min': None, 'port_range_max': None,
            'protocol': None, 'remote_group_id': None,
            'remote_ip_prefix': None,
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id']}

        rule_tcp_80 = {
            'id': str(uuid.uuid4()),
            'direction': u'ingress', 'ethertype': u'IPv4',
            'port_range_min': 80, 'port_range_max': 80,
            'protocol': u'tcp', 'remote_group_id': None,
            'remote_ip_prefix': u'0.0.0.0/0',
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id']}
        rule_icmp = {
            'id': str(uuid.uuid4()),
            'direction': u'ingress', 'ethertype': u'IPv4',
            'port_range_min': 5, 'port_range_max': 8,
            'protocol': u'icmp', 'remote_group_id': None,
            'remote_ip_prefix': u'0.0.0.0/0',
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id']}
        rule_group = {
            'id': str(uuid.uuid4()),
            'direction': u'ingress', 'ethertype': u'IPv4',
            'port_range_min': 80, 'port_range_max': 80,
            'protocol': u'tcp', 'remote_group_id': sec_group_1['id'],
            'remote_ip_prefix': None,
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id']}
        rule_all_tcp = {
            'id': str(uuid.uuid4()),
            'direction': u'egress', 'ethertype': u'IPv4',
            'port_range_min': 1, 'port_range_max': 65535,
            'protocol': u'tcp', 'remote_group_id': None,
            'remote_ip_prefix': u'0.0.0.0/24',
            'security_group_id': secgroup['id'],
            'tenant_id': secgroup['tenant_id']}

        rules = []
        if not default_only:
            rules += [rule_tcp_80, rule_icmp, rule_group, rule_all_tcp]
        rules += [rule_egress_ipv4, rule_egress_ipv6]
        secgroup['security_group_rules'] = rules

    add_rule_to_group(sec_group_1, default_only=False)
    add_rule_to_group(sec_group_2)
    add_rule_to_group(sec_group_3)

    groups = [sec_group_1, sec_group_2, sec_group_3]
    sg_name_dict = dict([(sg['id'], sg['name']) for sg in groups])
    for sg in groups:
        # Neutron API.
        TEST.api_q_secgroups.add(sg)
        for rule in sg['security_group_rules']:
            TEST.api_q_secgroup_rules.add(copy.copy(rule))
        # OpenStack Dashboard internaly API.
        TEST.q_secgroups.add(
            neutron.SecurityGroup(copy.deepcopy(sg), sg_name_dict))
        for rule in sg['security_group_rules']:
            TEST.q_secgroup_rules.add(
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

    # LBaaS.

    # 1st pool.
    pool_dict = {'id': '8913dde8-4915-4b90-8d3e-b95eeedb0d49',
                 'tenant_id': '1',
                 'vip_id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                 'name': 'pool1',
                 'description': 'pool description',
                 'subnet_id': TEST.subnets.first().id,
                 'protocol': 'HTTP',
                 'lb_method': 'ROUND_ROBIN',
                 'health_monitors': TEST.monitors.list(),
                 'members': ['78a46e5e-eb1a-418a-88c7-0e3f5968b08'],
                 'admin_state_up': True,
                 'status': 'ACTIVE',
                 'provider': 'haproxy'}
    TEST.api_pools.add(pool_dict)
    TEST.pools.add(lbaas.Pool(pool_dict))

    # 2nd pool.
    pool_dict = {'id': '8913dde8-4915-4b90-8d3e-b95eeedb0d50',
                 'tenant_id': '1',
                 'vip_id': 'f0881d38-c3eb-4fee-9763-12de3338041d',
                 'name': 'pool2',
                 'description': 'pool description',
                 'subnet_id': TEST.subnets.first().id,
                 'protocol': 'HTTPS',
                 'lb_method': 'ROUND_ROBIN',
                 'health_monitors': TEST.monitors.list()[0:1],
                 'members': [],
                 'status': 'PENDING_CREATE',
                 'admin_state_up': True}
    TEST.api_pools.add(pool_dict)
    TEST.pools.add(lbaas.Pool(pool_dict))

    # 1st vip.
    vip_dict = {'id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                'name': 'vip1',
                'address': '10.0.0.100',
                'description': 'vip description',
                'subnet_id': TEST.subnets.first().id,
                'port_id': TEST.ports.first().id,
                'subnet': TEST.subnets.first().cidr,
                'protocol_port': 80,
                'protocol': pool_dict['protocol'],
                'pool_id': pool_dict['id'],
                'session_persistence': {'type': 'APP_COOKIE',
                                        'cookie_name': 'jssessionid'},
                'connection_limit': 10,
                'admin_state_up': True}
    TEST.api_vips.add(vip_dict)
    TEST.vips.add(lbaas.Vip(vip_dict))
    setattr(TEST.pools.first(), 'vip', TEST.vips.first())

    # 2nd vip.
    vip_dict = {'id': 'f0881d38-c3eb-4fee-9763-12de3338041d',
                'name': 'vip2',
                'address': '10.0.0.110',
                'description': 'vip description',
                'subnet_id': TEST.subnets.first().id,
                'port_id': TEST.ports.list()[0].id,
                'subnet': TEST.subnets.first().cidr,
                'protocol_port': 80,
                'protocol': pool_dict['protocol'],
                'pool_id': pool_dict['id'],
                'session_persistence': {'type': 'APP_COOKIE',
                                        'cookie_name': 'jssessionid'},
                'connection_limit': 10,
                'admin_state_up': True}
    TEST.api_vips.add(vip_dict)
    TEST.vips.add(lbaas.Vip(vip_dict))

    # 1st member.
    member_dict = {'id': '78a46e5e-eb1a-418a-88c7-0e3f5968b08',
                   'tenant_id': '1',
                   'pool_id': pool_dict['id'],
                   'address': '10.0.0.11',
                   'protocol_port': 80,
                   'weight': 10,
                   'status': 'ACTIVE',
                   'admin_state_up': True}
    TEST.api_members.add(member_dict)
    TEST.members.add(lbaas.Member(member_dict))

    # 2nd member.
    member_dict = {'id': '41ac1f8d-6d9c-49a4-a1bf-41955e651f91',
                   'tenant_id': '1',
                   'pool_id': pool_dict['id'],
                   'address': '10.0.0.12',
                   'protocol_port': 80,
                   'weight': 10,
                   'status': 'ACTIVE',
                   'admin_state_up': True}
    TEST.api_members.add(member_dict)
    TEST.members.add(lbaas.Member(member_dict))

    # 1st v6 pool.
    pool_dict = {'id': 'c2983d70-8ac7-11e4-b116-123b93f75cba',
                 'tenant_id': '1',
                 'vip_id': 'b6598a5e-8ab4-11e4-b116-123b93f75cba',
                 'name': 'v6_pool1',
                 'description': 'pool description',
                 'subnet_id': TEST.subnets.get(name='v6_subnet1').id,
                 'protocol': 'HTTP',
                 'lb_method': 'ROUND_ROBIN',
                 'health_monitors': TEST.monitors.list(),
                 'members': ['78a46e5e-eb1a-418a-88c7-0e3f5968b08'],
                 'admin_state_up': True,
                 'status': 'ACTIVE',
                 'provider': 'haproxy'}
    TEST.api_pools.add(pool_dict)
    TEST.pools.add(lbaas.Pool(pool_dict))

    # 1st v6 vip.
    vip_dict = {'id': 'b6598a5e-8ab4-11e4-b116-123b93f75cba',
                'name': 'v6_vip1',
                'address': 'ff09::03',
                'description': 'vip description',
                'subnet_id': TEST.subnets.get(name="v6_subnet1").id,
                'port_id': TEST.ports.first().id,
                'subnet': TEST.subnets.get(name="v6_subnet1").cidr,
                'protocol_port': 80,
                'protocol': pool_dict['protocol'],
                'pool_id': pool_dict['id'],
                'session_persistence': {'type': 'APP_COOKIE',
                                        'cookie_name': 'jssessionid'},
                'connection_limit': 10,
                'admin_state_up': True}
    TEST.api_vips.add(vip_dict)
    TEST.vips.add(lbaas.Vip(vip_dict))

    # 2nd v6 vip.
    vip_dict = {'id': 'b6598cc0-8ab4-11e4-b116-123b93f75cba',
                'name': 'ff09::04',
                'address': '10.0.0.110',
                'description': 'vip description',
                'subnet_id': TEST.subnets.get(name="v6_subnet2").id,
                'port_id': TEST.ports.list()[0].id,
                'subnet': TEST.subnets.get(name="v6_subnet2").cidr,
                'protocol_port': 80,
                'protocol': pool_dict['protocol'],
                'pool_id': pool_dict['id'],
                'session_persistence': {'type': 'APP_COOKIE',
                                        'cookie_name': 'jssessionid'},
                'connection_limit': 10,
                'admin_state_up': True}
    TEST.api_vips.add(vip_dict)
    TEST.vips.add(lbaas.Vip(vip_dict))

    # 1st v6 monitor.
    monitor_dict = {'id': '0dc936f8-8aca-11e4-b116-123b93f75cba',
                    'type': 'http',
                    'delay': 10,
                    'timeout': 10,
                    'max_retries': 10,
                    'http_method': 'GET',
                    'url_path': '/',
                    'expected_codes': '200',
                    'admin_state_up': True,
                    "pools": [{"pool_id": TEST.pools.get(name='v6_pool1').id}],
                    }
    TEST.api_monitors.add(monitor_dict)
    TEST.monitors.add(lbaas.PoolMonitor(monitor_dict))

    # v6 member.
    member_dict = {'id': '6bc03d1e-8ad0-11e4-b116-123b93f75cba',
                   'tenant_id': '1',
                   'pool_id': TEST.pools.get(name='v6_pool1').id,
                   'address': 'ff09::03',
                   'protocol_port': 80,
                   'weight': 10,
                   'status': 'ACTIVE',
                   'member_type': 'server_list',
                   'admin_state_up': True}
    TEST.api_members.add(member_dict)
    TEST.members.add(lbaas.Member(member_dict))

    # 1st monitor.
    monitor_dict = {'id': 'd4a0500f-db2b-4cc4-afcf-ec026febff96',
                    'type': 'http',
                    'delay': 10,
                    'timeout': 10,
                    'max_retries': 10,
                    'http_method': 'GET',
                    'url_path': '/',
                    'expected_codes': '200',
                    'admin_state_up': True,
                    "pools": [{"pool_id": TEST.pools.list()[0].id},
                              {"pool_id": TEST.pools.list()[1].id}],
                    }
    TEST.api_monitors.add(monitor_dict)
    TEST.monitors.add(lbaas.PoolMonitor(monitor_dict))

    # 2nd monitor.
    monitor_dict = {'id': 'd4a0500f-db2b-4cc4-afcf-ec026febff97',
                    'type': 'ping',
                    'delay': 10,
                    'timeout': 10,
                    'max_retries': 10,
                    'admin_state_up': True,
                    'pools': [],
                    }
    TEST.api_monitors.add(monitor_dict)
    TEST.monitors.add(lbaas.PoolMonitor(monitor_dict))

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
    quota_usage_data = {'networks': {'used': 0, 'quota': 5},
                        'subnets': {'used': 0, 'quota': 5},
                        'routers': {'used': 0, 'quota': 5},
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
    extension_6 = {"name": "LoadBalancing service",
                   "alias": "lbaas",
                   "description": "Extension for LoadBalancing service"}
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

    # VPNaaS.

    # 1st VPNService.
    vpnservice_dict = {'id': '09a26949-6231-4f72-942a-0c8c0ddd4d61',
                       'tenant_id': '1',
                       'name': 'cloud_vpn1',
                       'description': 'vpn description',
                       'subnet_id': TEST.subnets.first().id,
                       'router_id': TEST.routers.first().id,
                       'vpn_type': 'ipsec',
                       'ipsecsiteconnections': [],
                       'admin_state_up': True,
                       'status': 'Active',
                       'ipsecsiteconns': TEST.ipsecsiteconnections.list()
                       }
    TEST.api_vpnservices.add(vpnservice_dict)
    TEST.vpnservices.add(vpn.VPNService(vpnservice_dict))

    # 2nd VPNService.
    vpnservice_dict = {'id': '09a26949-6231-4f72-942a-0c8c0ddd4d62',
                       'tenant_id': '1',
                       'name': 'cloud_vpn2',
                       'description': 'vpn description',
                       'subnet_id': TEST.subnets.first().id,
                       'router_id': TEST.routers.first().id,
                       'vpn_type': 'ipsec',
                       'ipsecsiteconnections': [],
                       'admin_state_up': True,
                       'status': 'Active',
                       'ipsecsiteconns': [],
                       'external_v4_ip': '10.0.0.0/24',
                       'external_v6_ip': 'fd4c:a535:831c::/64'
                       }
    TEST.api_vpnservices.add(vpnservice_dict)
    TEST.vpnservices.add(vpn.VPNService(vpnservice_dict))

    # 1st IKEPolicy
    ikepolicy_dict = {'id': 'a1f009b7-0ffa-43a7-ba19-dcabb0b4c981',
                      'tenant_id': '1',
                      'name': 'ikepolicy_1',
                      'description': 'ikepolicy description',
                      'auth_algorithm': 'sha1',
                      'encryption_algorithm': 'aes-256',
                      'ike_version': 'v1',
                      'lifetime': {'units': 'seconds', 'value': 3600},
                      'phase1_negotiation_mode': 'main',
                      'pfs': 'group5',
                      'ipsecsiteconns': TEST.ipsecsiteconnections.list()}
    TEST.api_ikepolicies.add(ikepolicy_dict)
    TEST.ikepolicies.add(vpn.IKEPolicy(ikepolicy_dict))

    # 2nd IKEPolicy
    ikepolicy_dict = {'id': 'a1f009b7-0ffa-43a7-ba19-dcabb0b4c982',
                      'tenant_id': '1',
                      'name': 'ikepolicy_2',
                      'description': 'ikepolicy description',
                      'auth_algorithm': 'sha1',
                      'encryption_algorithm': 'aes-256',
                      'ike_version': 'v1',
                      'lifetime': {'units': 'seconds', 'value': 3600},
                      'phase1_negotiation_mode': 'main',
                      'pfs': 'group5',
                      'ipsecsiteconns': []}
    TEST.api_ikepolicies.add(ikepolicy_dict)
    TEST.ikepolicies.add(vpn.IKEPolicy(ikepolicy_dict))

    # 1st IPSecPolicy
    ipsecpolicy_dict = {'id': '8376e1dd-2b1c-4346-b23c-6989e75ecdb8',
                        'tenant_id': '1',
                        'name': 'ipsecpolicy_1',
                        'description': 'ipsecpolicy description',
                        'auth_algorithm': 'sha1',
                        'encapsulation_mode': 'tunnel',
                        'encryption_algorithm': '3des',
                        'lifetime': {'units': 'seconds', 'value': 3600},
                        'pfs': 'group5',
                        'transform_protocol': 'esp',
                        'ipsecsiteconns': TEST.ipsecsiteconnections.list()}
    TEST.api_ipsecpolicies.add(ipsecpolicy_dict)
    TEST.ipsecpolicies.add(vpn.IPSecPolicy(ipsecpolicy_dict))

    # 2nd IPSecPolicy
    ipsecpolicy_dict = {'id': '8376e1dd-2b1c-4346-b23c-6989e75ecdb9',
                        'tenant_id': '1',
                        'name': 'ipsecpolicy_2',
                        'description': 'ipsecpolicy description',
                        'auth_algorithm': 'sha1',
                        'encapsulation_mode': 'tunnel',
                        'encryption_algorithm': '3des',
                        'lifetime': {'units': 'seconds', 'value': 3600},
                        'pfs': 'group5',
                        'transform_protocol': 'esp',
                        'ipsecsiteconns': []}
    TEST.api_ipsecpolicies.add(ipsecpolicy_dict)
    TEST.ipsecpolicies.add(vpn.IPSecPolicy(ipsecpolicy_dict))

    # 1st IPSecSiteConnection
    ipsecsiteconnection_dict = {'id': 'dd1dd3a0-f349-49be-b013-245e147763d6',
                                'tenant_id': '1',
                                'name': 'ipsec_connection_1',
                                'description': 'vpn connection description',
                                'dpd': {'action': 'hold',
                                        'interval': 30,
                                        'timeout': 120},
                                'ikepolicy_id': ikepolicy_dict['id'],
                                'initiator': 'bi-directional',
                                'ipsecpolicy_id': ipsecpolicy_dict['id'],
                                'mtu': 1500,
                                'peer_address':
                                '2607:f0d0:4545:3:200:f8ff:fe21:67cf',
                                'peer_cidrs': ['20.1.0.0/24', '21.1.0.0/24'],
                                'peer_id':
                                    '2607:f0d0:4545:3:200:f8ff:fe21:67cf',
                                'psk': 'secret',
                                'vpnservice_id': vpnservice_dict['id'],
                                'admin_state_up': True,
                                'status': 'Active'}
    TEST.api_ipsecsiteconnections.add(ipsecsiteconnection_dict)
    TEST.ipsecsiteconnections.add(
        vpn.IPSecSiteConnection(ipsecsiteconnection_dict))

    # 2nd IPSecSiteConnection
    ipsecsiteconnection_dict = {'id': 'dd1dd3a0-f349-49be-b013-245e147763d7',
                                'tenant_id': '1',
                                'name': 'ipsec_connection_2',
                                'description': 'vpn connection description',
                                'dpd': {'action': 'hold',
                                        'interval': 30,
                                        'timeout': 120},
                                'ikepolicy_id': ikepolicy_dict['id'],
                                'initiator': 'bi-directional',
                                'ipsecpolicy_id': ipsecpolicy_dict['id'],
                                'mtu': 1500,
                                'peer_address': '172.0.0.2',
                                'peer_cidrs': ['20.1.0.0/24'],
                                'peer_id': '172.0.0.2',
                                'psk': 'secret',
                                'vpnservice_id': vpnservice_dict['id'],
                                'admin_state_up': True,
                                'status': 'Active'}
    TEST.api_ipsecsiteconnections.add(ipsecsiteconnection_dict)
    TEST.ipsecsiteconnections.add(
        vpn.IPSecSiteConnection(ipsecsiteconnection_dict))

    # FWaaS

    # 1st rule (used by 1st policy)
    rule1_dict = {'id': 'f0881d38-c3eb-4fee-9763-12de3338041d',
                  'tenant_id': '1',
                  'name': 'rule1',
                  'description': 'rule1 description',
                  'protocol': 'tcp',
                  'action': 'allow',
                  'source_ip_address': '1.2.3.0/24',
                  'source_port': '80',
                  'destination_ip_address': '4.5.6.7/32',
                  'destination_port': '1:65535',
                  'firewall_policy_id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                  'position': 1,
                  'shared': True,
                  'enabled': True,
                  'ip_version': '4'}
    TEST.api_fw_rules.add(rule1_dict)

    rule1 = fwaas.Rule(copy.deepcopy(rule1_dict))
    # NOTE: rule1['policy'] is set below
    TEST.fw_rules.add(rule1)

    # 2nd rule (used by 2nd policy; no name)
    rule2_dict = {'id': 'c6298a93-850f-4f64-b78a-959fd4f1e5df',
                  'tenant_id': '1',
                  'name': '',
                  'description': '',
                  'protocol': 'udp',
                  'action': 'deny',
                  'source_ip_address': '1.2.3.0/24',
                  'source_port': '80',
                  'destination_ip_address': '4.5.6.7/32',
                  'destination_port': '1:65535',
                  'firewall_policy_id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                  'position': 2,
                  'shared': True,
                  'enabled': True,
                  'ip_version': '6'}
    TEST.api_fw_rules.add(rule2_dict)

    rule2 = fwaas.Rule(copy.deepcopy(rule2_dict))
    # NOTE: rule2['policy'] is set below
    TEST.fw_rules.add(rule2)

    # 3rd rule (not used by any policy)
    rule3_dict = {'id': 'h0881d38-c3eb-4fee-9763-12de3338041d',
                  'tenant_id': '1',
                  'name': 'rule3',
                  'description': 'rule3 description',
                  'protocol': None,
                  'action': 'allow',
                  'source_ip_address': '1.2.3.0/24',
                  'source_port': '80',
                  'destination_ip_address': '4.5.6.7/32',
                  'destination_port': '1:65535',
                  'firewall_policy_id': None,
                  'position': None,
                  'shared': True,
                  'enabled': True,
                  'ip_version': '4'}
    TEST.api_fw_rules.add(rule3_dict)

    rule3 = fwaas.Rule(copy.deepcopy(rule3_dict))
    # rule3 is not associated with any rules
    rule3._apidict['policy'] = None
    TEST.fw_rules.add(rule3)

    # 1st policy (associated with 2 rules)
    policy1_dict = {'id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                    'tenant_id': '1',
                    'name': 'policy1',
                    'description': 'policy with two rules',
                    'firewall_rules': [rule1_dict['id'], rule2_dict['id']],
                    'audited': True,
                    'shared': True}
    TEST.api_fw_policies.add(policy1_dict)

    policy1 = fwaas.Policy(copy.deepcopy(policy1_dict))
    policy1._apidict['rules'] = [rule1, rule2]
    TEST.fw_policies.add(policy1)

    # Reverse relations (rule -> policy)
    rule1._apidict['policy'] = policy1
    rule2._apidict['policy'] = policy1

    # 2nd policy (associated with no rules; no name)
    policy2_dict = {'id': 'cf50b331-787a-4623-825e-da794c918d6a',
                    'tenant_id': '1',
                    'name': '',
                    'description': '',
                    'firewall_rules': [],
                    'audited': False,
                    'shared': False}
    TEST.api_fw_policies.add(policy2_dict)

    policy2 = fwaas.Policy(copy.deepcopy(policy2_dict))
    policy2._apidict['rules'] = []
    TEST.fw_policies.add(policy2)

    # 1st firewall
    fw1_dict = {'id': '8913dde8-4915-4b90-8d3e-b95eeedb0d49',
                'tenant_id': '1',
                'firewall_policy_id':
                    'abcdef-c3eb-4fee-9763-12de3338041e',
                'name': 'firewall1',
                'router_ids': [TEST.routers.first().id],
                'description': 'firewall description',
                'status': 'PENDING_CREATE',
                'admin_state_up': True}
    TEST.api_firewalls.add(fw1_dict)

    fw1 = fwaas.Firewall(copy.deepcopy(fw1_dict))
    fw1._apidict['policy'] = policy1
    fw1._apidict['routers'] = [TEST.routers.first()]
    TEST.firewalls.add(fw1)

    # 2nd firewall (no name)
    fw2_dict = {'id': '1aa75150-415f-458e-bae5-5a362a4fb1f7',
                'tenant_id': '1',
                'firewall_policy_id':
                    'abcdef-c3eb-4fee-9763-12de3338041e',
                'name': '',
                'router_ids': [],
                'description': '',
                'status': 'PENDING_CREATE',
                'admin_state_up': True}
    TEST.api_firewalls.add(fw2_dict)

    fw2 = fwaas.Firewall(copy.deepcopy(fw2_dict))
    fw2._apidict['policy'] = policy1
    TEST.firewalls.add(fw2)

    # Additional Cisco N1K profiles.

    # 2nd network profile for network when using the cisco n1k plugin.
    # Profile applied on 1st network.
    net_profile_dict = {'name': 'net_profile_test2',
                        'segment_type': 'overlay',
                        'sub_type': 'native_vxlan',
                        'segment_range': '10000-10100',
                        'multicast_ip_range': '144.0.0.0-144.0.0.100',
                        'id':
                        '00000000-2222-2222-2222-000000000000',
                        'project': '1',
                        # overlay profiles have no physical_network
                        'physical_network': None}

    TEST.api_net_profiles.add(net_profile_dict)
    TEST.net_profiles.add(neutron.Profile(net_profile_dict))

    # 2nd network profile binding.
    network_profile_binding_dict = {'profile_id':
                                    '00000000-2222-2222-2222-000000000000',
                                    'tenant_id': '1'}

    TEST.api_network_profile_binding.add(network_profile_binding_dict)
    TEST.network_profile_binding.add(neutron.Profile(
        network_profile_binding_dict))

    # 3rd network profile for network when using the cisco n1k plugin
    # Profile applied on 1st network
    net_profile_dict = {'name': 'net_profile_test3',
                        'segment_type': 'overlay',
                        'sub_type': 'other',
                        'other_subtype': 'GRE',
                        'segment_range': '11000-11100',
                        'id':
                        '00000000-3333-3333-3333-000000000000',
                        'project': '1'}

    TEST.api_net_profiles.add(net_profile_dict)
    TEST.net_profiles.add(neutron.Profile(net_profile_dict))

    # 3rd network profile binding
    network_profile_binding_dict = {'profile_id':
                                    '00000000-3333-3333-3333-000000000000',
                                    'tenant_id': '1'}

    TEST.api_network_profile_binding.add(network_profile_binding_dict)
    TEST.network_profile_binding.add(neutron.Profile(
        network_profile_binding_dict))

    # 4th network profile for network when using the cisco n1k plugin
    # Profile applied on 1st network
    net_profile_dict = {'name': 'net_profile_test4',
                        'segment_type': 'trunk',
                        'sub_type_trunk': 'vlan',
                        'id':
                        '00000000-4444-4444-4444-000000000000',
                        'project': '1'}

    TEST.api_net_profiles.add(net_profile_dict)
    TEST.net_profiles.add(neutron.Profile(net_profile_dict))

    # 4th network profile binding
    network_profile_binding_dict = {'profile_id':
                                    '00000000-4444-4444-4444-000000000000',
                                    'tenant_id': '1'}

    TEST.api_network_profile_binding.add(network_profile_binding_dict)
    TEST.network_profile_binding.add(neutron.Profile(
        network_profile_binding_dict))

    # Adding a new network and new network and policy profile
    # similar to the first to test launching an instance with multiple
    # nics and multiple profiles.

    # 4th network to use for testing instances with multiple-nics & profiles
    network_dict = {'admin_state_up': True,
                    'id': '7aa23d91-ffff-abab-dcdc-3411ae767e8a',
                    'name': 'net4',
                    'status': 'ACTIVE',
                    'subnets': ['31be4a21-aadd-73da-6422-821ff249a4bb'],
                    'tenant_id': '1',
                    'router:external': False,
                    'shared': False}
    subnet_dict = {'allocation_pools': [{'end': '11.10.0.254',
                                         'start': '11.10.0.2'}],
                   'dns_nameservers': [],
                   'host_routes': [],
                   'cidr': '11.10.0.0/24',
                   'enable_dhcp': True,
                   'gateway_ip': '11.10.0.1',
                   'id': network_dict['subnets'][0],
                   'ip_version': 4,
                   'name': 'mysubnet4',
                   'network_id': network_dict['id'],
                   'tenant_id': network_dict['tenant_id']}

    TEST.api_networks.add(network_dict)
    TEST.api_subnets.add(subnet_dict)

    network = copy.deepcopy(network_dict)
    subnet = neutron.Subnet(subnet_dict)
    network['subnets'] = [subnet]
    TEST.networks.add(neutron.Network(network))
    TEST.subnets.add(subnet)

    # 5th network profile for network when using the cisco n1k plugin
    # Network Profile applied on 4th network
    net_profile_dict = {'name': 'net_profile_test5',
                        'segment_type': 'vlan',
                        'physical_network': 'phys5',
                        'segment_range': '400-450',
                        'id':
                        '00000000-5555-5555-5555-000000000000',
                        'project': TEST.networks.get(name="net4")['tenant_id']}

    TEST.api_net_profiles.add(net_profile_dict)
    TEST.net_profiles.add(neutron.Profile(net_profile_dict))

    # 2nd policy profile for port when using the cisco n1k plugin
    policy_profile_dict = {'name': 'policy_profile_test2',
                           'id':
                           '11111111-9999-9999-9999-111111111111'}

    TEST.api_policy_profiles.add(policy_profile_dict)
    TEST.policy_profiles.add(neutron.Profile(policy_profile_dict))

    # network profile binding
    network_profile_binding_dict = {'profile_id':
                                    '00000000-5555-5555-5555-000000000000',
                                    'tenant_id':
                                    TEST.networks.get(name="net4")['tenant_id']
                                    }

    TEST.api_network_profile_binding.add(network_profile_binding_dict)
    TEST.network_profile_binding.add(neutron.Profile(
        network_profile_binding_dict))

    # policy profile binding
    policy_profile_binding_dict = {'profile_id':
                                   '11111111-9999-9999-9999-111111111111',
                                   'tenant_id':
                                   TEST.networks.get(name="net4")['tenant_id']}

    TEST.api_policy_profile_binding.add(policy_profile_binding_dict)
    TEST.policy_profile_binding.add(neutron.Profile(
        policy_profile_binding_dict))

    # ports on 4th network
    port_dict = {'admin_state_up': True,
                 'device_id': '9872faaa-b2b2-eeee-9911-21332eedaa77',
                 'device_owner': 'network:dhcp',
                 'fixed_ips': [{'ip_address': '11.10.0.3',
                                'subnet_id':
                                TEST.subnets.get(name="mysubnet4")['id']}],
                 'id': 'a21dcd22-6733-cccc-aa32-22adafaf16a2',
                 'mac_address': '78:22:ff:1a:ba:23',
                 'name': 'port5',
                 'network_id': TEST.networks.get(name="net4")['id'],
                 'status': 'ACTIVE',
                 'tenant_id': TEST.networks.get(name="net4")['tenant_id'],
                 'binding:vnic_type': 'normal',
                 'binding:host_id': 'host'}
    TEST.api_ports.add(port_dict)
    TEST.ports.add(neutron.Port(port_dict))
