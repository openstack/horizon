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

from openstack_dashboard.api.lbaas import Member
from openstack_dashboard.api.lbaas import Pool
from openstack_dashboard.api.lbaas import PoolMonitor
from openstack_dashboard.api.lbaas import Vip

from openstack_dashboard.api.neutron import FloatingIp
from openstack_dashboard.api.neutron import Network
from openstack_dashboard.api.neutron import Port
from openstack_dashboard.api.neutron import Router
from openstack_dashboard.api.neutron import SecurityGroup
from openstack_dashboard.api.neutron import SecurityGroupRule
from openstack_dashboard.api.neutron import Subnet

from openstack_dashboard.test.test_data.utils import TestDataContainer


def data(TEST):
    # data returned by openstack_dashboard.api.neutron wrapper
    TEST.networks = TestDataContainer()
    TEST.subnets = TestDataContainer()
    TEST.ports = TestDataContainer()
    TEST.routers = TestDataContainer()
    TEST.q_floating_ips = TestDataContainer()
    TEST.q_secgroups = TestDataContainer()
    TEST.q_secgroup_rules = TestDataContainer()
    TEST.pools = TestDataContainer()
    TEST.vips = TestDataContainer()
    TEST.members = TestDataContainer()
    TEST.monitors = TestDataContainer()

    # data return by neutronclient
    TEST.api_networks = TestDataContainer()
    TEST.api_subnets = TestDataContainer()
    TEST.api_ports = TestDataContainer()
    TEST.api_routers = TestDataContainer()
    TEST.api_q_floating_ips = TestDataContainer()
    TEST.api_q_secgroups = TestDataContainer()
    TEST.api_q_secgroup_rules = TestDataContainer()
    TEST.api_pools = TestDataContainer()
    TEST.api_vips = TestDataContainer()
    TEST.api_members = TestDataContainer()
    TEST.api_monitors = TestDataContainer()

    #------------------------------------------------------------
    # 1st network
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
    subnet = Subnet(subnet_dict)
    network['subnets'] = [subnet]
    TEST.networks.add(Network(network))
    TEST.subnets.add(subnet)

    # ports on 1st network
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
                 'tenant_id': network_dict['tenant_id']}
    TEST.api_ports.add(port_dict)
    TEST.ports.add(Port(port_dict))

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
                 'tenant_id': network_dict['tenant_id']}
    TEST.api_ports.add(port_dict)
    TEST.ports.add(Port(port_dict))
    assoc_port = port_dict

    #------------------------------------------------------------
    # 2nd network
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
    subnet = Subnet(subnet_dict)
    network['subnets'] = [subnet]
    TEST.networks.add(Network(network))
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
                 'tenant_id': network_dict['tenant_id']}

    TEST.api_ports.add(port_dict)
    TEST.ports.add(Port(port_dict))

    #------------------------------------------------------------
    # external network
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
    subnet = Subnet(subnet_dict)
    network['subnets'] = [subnet]
    TEST.networks.add(Network(network))
    TEST.subnets.add(subnet)

    #------------------------------------------------------------
    # Set up router data
    port_dict = {'admin_state_up': True,
                 'device_id': '7180cede-bcd8-4334-b19f-f7ef2f331f53',
                 'device_owner': 'network:router_gateway',
                 'fixed_ips': [{'ip_address': '10.0.0.3',
                                'subnet_id': subnet_dict['id']}],
                 'id': '44ec6726-4bdc-48c5-94d4-df8d1fbf613b',
                 'mac_address': 'fa:16:3e:9c:d5:7e',
                 'name': '',
                 'network_id': network_dict['id'],
                 'status': 'ACTIVE',
                 'tenant_id': '1'}
    TEST.api_ports.add(port_dict)
    TEST.ports.add(Port(port_dict))

    router_dict = {'id': '279989f7-54bb-41d9-ba42-0d61f12fda61',
                   'name': 'router1',
                   'external_gateway_info':
                       {'network_id': ext_net['id']},
                   'tenant_id': '1'}
    TEST.api_routers.add(router_dict)
    TEST.routers.add(Router(router_dict))
    router_dict = {'id': '10e3dc42-1ce1-4d48-87cf-7fc333055d6c',
                   'name': 'router2',
                   'external_gateway_info':
                       {'network_id': ext_net['id']},
                   'tenant_id': '1'}
    TEST.api_routers.add(router_dict)
    TEST.routers.add(Router(router_dict))

    #------------------------------------------------------------
    # floating IP
    # unassociated
    fip_dict = {'tenant_id': '1',
                'floating_ip_address': '172.16.88.227',
                'floating_network_id': ext_net['id'],
                'id': '9012cd70-cfae-4e46-b71e-6a409e9e0063',
                'fixed_ip_address': None,
                'port_id': None,
                'router_id': None}
    TEST.api_q_floating_ips.add(fip_dict)
    TEST.q_floating_ips.add(FloatingIp(fip_dict))

    # associated (with compute port on 1st network)
    fip_dict = {'tenant_id': '1',
                'floating_ip_address': '172.16.88.228',
                'floating_network_id': ext_net['id'],
                'id': 'a97af8f2-3149-4b97-abbd-e49ad19510f7',
                'fixed_ip_address': assoc_port['fixed_ips'][0]['ip_address'],
                'port_id': assoc_port['id'],
                'router_id': router_dict['id']}
    TEST.api_q_floating_ips.add(fip_dict)
    TEST.q_floating_ips.add(FloatingIp(fip_dict))

    #------------------------------------------------------------
    # security group

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

        rules = []
        if not default_only:
            rules += [rule_tcp_80, rule_icmp, rule_group]
        rules += [rule_egress_ipv4, rule_egress_ipv6]
        secgroup['security_group_rules'] = rules

    add_rule_to_group(sec_group_1, default_only=False)
    add_rule_to_group(sec_group_2)
    add_rule_to_group(sec_group_3)

    groups = [sec_group_1, sec_group_2, sec_group_3]
    sg_name_dict = dict([(sg['id'], sg['name']) for sg in groups])
    for sg in groups:
        # Neutron API
        TEST.api_q_secgroups.add(sg)
        for rule in sg['security_group_rules']:
            TEST.api_q_secgroup_rules.add(copy.copy(rule))
        # OpenStack Dashboard internaly API
        TEST.q_secgroups.add(SecurityGroup(copy.deepcopy(sg), sg_name_dict))
        for rule in sg['security_group_rules']:
            TEST.q_secgroup_rules.add(
                SecurityGroupRule(copy.copy(rule), sg_name_dict))

    #------------------------------------------------------------
    # LBaaS

    # 1st pool
    pool_dict = {'id': '8913dde8-4915-4b90-8d3e-b95eeedb0d49',
                 'tenant_id': '1',
                 'vip_id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                 'name': 'pool1',
                 'description': 'pool description',
                 'subnet_id': TEST.subnets.first().id,
                 'protocol': 'HTTP',
                 'lb_method': 'ROUND_ROBIN',
                 'health_monitors': ['d4a0500f-db2b-4cc4-afcf-ec026febff96'],
                 'admin_state_up': True}
    TEST.api_pools.add(pool_dict)
    TEST.pools.add(Pool(pool_dict))

    # 1st vip
    vip_dict = {'id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                'name': 'vip1',
                'address': '10.0.0.100',
                'floatip_address': '',
                'other_address': '10.0.0.100',
                'description': 'vip description',
                'subnet_id': TEST.subnets.first().id,
                'subnet': TEST.subnets.first().cidr,
                'protocol_port': 80,
                'protocol': pool_dict['protocol'],
                'pool_id': pool_dict['id'],
                'session_persistence': {'type': 'APP_COOKIE',
                                        'cookie_name': 'jssessionid'},
                'connection_limit': 10,
                'admin_state_up': True}
    TEST.api_vips.add(vip_dict)
    TEST.vips.add(Vip(vip_dict))

    # 2nd vip
    vip_dict = {'id': 'f0881d38-c3eb-4fee-9763-12de3338041d',
                'name': 'vip2',
                'address': '10.0.0.110',
                'floatip_address': '',
                'other_address': '10.0.0.110',
                'description': 'vip description',
                'subnet_id': TEST.subnets.first().id,
                'subnet': TEST.subnets.first().cidr,
                'protocol_port': 80,
                'protocol': pool_dict['protocol'],
                'pool_id': pool_dict['id'],
                'session_persistence': {'type': 'APP_COOKIE',
                                        'cookie_name': 'jssessionid'},
                'connection_limit': 10,
                'admin_state_up': True}
    TEST.api_vips.add(vip_dict)
    TEST.vips.add(Vip(vip_dict))

    # 1st member
    member_dict = {'id': '78a46e5e-eb1a-418a-88c7-0e3f5968b08',
                   'tenant_id': '1',
                   'pool_id': pool_dict['id'],
                   'address': '10.0.0.11',
                   'protocol_port': 80,
                   'weight': 10,
                   'admin_state_up': True}
    TEST.api_members.add(member_dict)
    TEST.members.add(Member(member_dict))

    # 2nd member
    member_dict = {'id': '41ac1f8d-6d9c-49a4-a1bf-41955e651f91',
                  'tenant_id': '1',
                  'pool_id': pool_dict['id'],
                  'address': '10.0.0.12',
                  'protocol_port': 80,
                  'weight': 10,
                  'admin_state_up': True}
    TEST.api_members.add(member_dict)
    TEST.members.add(Member(member_dict))

    # 2nd pool
    pool_dict = {'id': '8913dde8-4915-4b90-8d3e-b95eeedb0d50',
                 'tenant_id': '1',
                 'vip_id': 'f0881d38-c3eb-4fee-9763-12de3338041d',
                 'name': 'pool2',
                 'description': 'pool description',
                 'subnet_id': TEST.subnets.first().id,
                 'protocol': 'HTTPS',
                 'lb_method': 'ROUND_ROBIN',
                 'health_monitors': ['d4a0500f-db2b-4cc4-afcf-ec026febff97'],
                 'admin_state_up': True}
    TEST.api_pools.add(pool_dict)
    TEST.pools.add(Pool(pool_dict))

    # 1st monitor
    monitor_dict = {'id': 'd4a0500f-db2b-4cc4-afcf-ec026febff96',
                    'type': 'ping',
                    'delay': 10,
                    'timeout': 10,
                    'max_retries': 10,
                    'http_method': 'GET',
                    'url_path': '/',
                    'expected_codes': '200',
                    'admin_state_up': True}
    TEST.api_monitors.add(monitor_dict)
    TEST.monitors.add(PoolMonitor(monitor_dict))

    # 2nd monitor
    monitor_dict = {'id': 'd4a0500f-db2b-4cc4-afcf-ec026febff97',
                    'type': 'ping',
                    'delay': 10,
                    'timeout': 10,
                    'max_retries': 10,
                    'http_method': 'GET',
                    'url_path': '/',
                    'expected_codes': '200',
                    'admin_state_up': True}
    TEST.api_monitors.add(monitor_dict)
    TEST.monitors.add(PoolMonitor(monitor_dict))
