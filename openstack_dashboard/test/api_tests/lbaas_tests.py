#    Copyright 2013, Big Switch Networks, Inc.
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

from neutronclient.v2_0 import client

neutronclient = client.Client


class LbaasApiTests(test.APITestCase):
    @test.create_stubs({neutronclient: ('create_vip',)})
    def test_vip_create(self):
        vip1 = self.api_vips.first()
        form_data = {'address': vip1['address'],
                     'name': vip1['name'],
                     'description': vip1['description'],
                     'subnet_id': vip1['subnet_id'],
                     'protocol_port': vip1['protocol_port'],
                     'protocol': vip1['protocol'],
                     'pool_id': vip1['pool_id'],
                     'session_persistence': vip1['session_persistence'],
                     'connection_limit': vip1['connection_limit'],
                     'admin_state_up': vip1['admin_state_up']
                     }
        vip = {'vip': self.api_vips.first()}
        neutronclient.create_vip({'vip': form_data}).AndReturn(vip)
        self.mox.ReplayAll()

        ret_val = api.lbaas.vip_create(self.request, **form_data)
        self.assertIsInstance(ret_val, api.lbaas.Vip)

    @test.create_stubs({neutronclient: ('create_vip',)})
    def test_vip_create_skip_address_if_empty(self):
        vip1 = self.api_vips.first()
        vipform_data = {'name': vip1['name'],
                        'description': vip1['description'],
                        'subnet_id': vip1['subnet_id'],
                        'protocol_port': vip1['protocol_port'],
                        'protocol': vip1['protocol'],
                        'pool_id': vip1['pool_id'],
                        'session_persistence': vip1['session_persistence'],
                        'connection_limit': vip1['connection_limit'],
                        'admin_state_up': vip1['admin_state_up']
                        }

        neutronclient.create_vip({'vip': vipform_data}).AndReturn(
            {'vip': vipform_data})
        self.mox.ReplayAll()

        form_data = dict(vipform_data)
        form_data['address'] = ""
        ret_val = api.lbaas.vip_create(self.request, **form_data)
        self.assertIsInstance(ret_val, api.lbaas.Vip)

    @test.create_stubs({neutronclient: ('list_vips',)})
    def test_vip_list(self):
        vips = {'vips': [{'id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                          'address': '10.0.0.100',
                          'name': 'vip1name',
                          'description': 'vip1description',
                          'subnet_id': '12381d38-c3eb-4fee-9763-12de3338041e',
                          'protocol_port': '80',
                          'protocol': 'HTTP',
                          'pool_id': '8913dde8-4915-4b90-8d3e-b95eeedb0d49',
                          'connection_limit': '10',
                          'admin_state_up': True
                          }, ]}
        neutronclient.list_vips().AndReturn(vips)
        self.mox.ReplayAll()

        ret_val = api.lbaas.vip_list(self.request)
        for v in ret_val:
            self.assertIsInstance(v, api.lbaas.Vip)
            self.assertTrue(v.id)

    @test.create_stubs({neutronclient: ('show_vip', 'show_pool'),
                        api.neutron: ('subnet_get', 'port_get')})
    def test_vip_get(self):
        vip = self.api_vips.first()
        neutronclient.show_vip(vip['id']).AndReturn({'vip': vip})
        api.neutron.subnet_get(self.request, vip['subnet_id']
                               ).AndReturn(self.subnets.first())
        api.neutron.port_get(self.request, vip['port_id']
                             ).AndReturn(self.ports.first())
        neutronclient.show_pool(vip['pool_id']
                                ).AndReturn({'pool': self.api_pools.first()})
        self.mox.ReplayAll()

        ret_val = api.lbaas.vip_get(self.request, vip['id'])
        self.assertIsInstance(ret_val, api.lbaas.Vip)
        self.assertIsInstance(ret_val.subnet, api.neutron.Subnet)
        self.assertEqual(vip['subnet_id'], ret_val.subnet.id)
        self.assertIsInstance(ret_val.port, api.neutron.Port)
        self.assertEqual(vip['port_id'], ret_val.port.id)
        self.assertIsInstance(ret_val.pool, api.lbaas.Pool)
        self.assertEqual(self.api_pools.first()['id'], ret_val.pool.id)

    @test.create_stubs({neutronclient: ('update_vip',)})
    def test_vip_update(self):
        form_data = {'address': '10.0.0.100',
                     'name': 'vip1name',
                     'description': 'vip1description',
                     'subnet_id': '12381d38-c3eb-4fee-9763-12de3338041e',
                     'protocol_port': '80',
                     'protocol': 'HTTP',
                     'pool_id': '8913dde8-4915-4b90-8d3e-b95eeedb0d49',
                     'connection_limit': '10',
                     'admin_state_up': True
                     }

        vip = {'vip': {'id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                       'address': '10.0.0.100',
                       'name': 'vip1name',
                       'description': 'vip1description',
                       'subnet_id': '12381d38-c3eb-4fee-9763-12de3338041e',
                       'protocol_port': '80',
                       'protocol': 'HTTP',
                       'pool_id': '8913dde8-4915-4b90-8d3e-b95eeedb0d49',
                       'connection_limit': '10',
                       'admin_state_up': True
                       }}
        neutronclient.update_vip(vip['vip']['id'], form_data).AndReturn(vip)
        self.mox.ReplayAll()

        ret_val = api.lbaas.vip_update(self.request,
                                       vip['vip']['id'], **form_data)
        self.assertIsInstance(ret_val, api.lbaas.Vip)

    @test.create_stubs({neutronclient: ('create_pool',)})
    def test_pool_create(self):
        form_data = {'name': 'pool1name',
                     'description': 'pool1description',
                     'subnet_id': '12381d38-c3eb-4fee-9763-12de3338041e',
                     'protocol': 'HTTP',
                     'lb_method': 'ROUND_ROBIN',
                     'admin_state_up': True,
                     'provider': 'dummy'
                     }

        pool = {'pool': {'id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                         'name': 'pool1name',
                         'description': 'pool1description',
                         'subnet_id': '12381d38-c3eb-4fee-9763-12de3338041e',
                         'protocol': 'HTTP',
                         'lb_method': 'ROUND_ROBIN',
                         'admin_state_up': True,
                         'provider': 'dummy'
                         }}
        neutronclient.create_pool({'pool': form_data}).AndReturn(pool)
        self.mox.ReplayAll()

        ret_val = api.lbaas.pool_create(self.request, **form_data)
        self.assertIsInstance(ret_val, api.lbaas.Pool)

    @test.create_stubs({neutronclient: ('list_pools', 'list_vips'),
                        api.neutron: ('subnet_list',)})
    def test_pool_list(self):
        pools = {'pools': self.api_pools.list()}
        subnets = self.subnets.list()
        vips = {'vips': self.api_vips.list()}

        neutronclient.list_pools().AndReturn(pools)
        api.neutron.subnet_list(self.request).AndReturn(subnets)
        neutronclient.list_vips().AndReturn(vips)
        self.mox.ReplayAll()

        ret_val = api.lbaas.pool_list(self.request)
        for v in ret_val:
            self.assertIsInstance(v, api.lbaas.Pool)
            self.assertTrue(v.id)

    @test.create_stubs({neutronclient: ('show_pool', 'show_vip',
                                        'list_members',
                                        'show_health_monitor',),
                        api.neutron: ('subnet_get',)})
    def test_pool_get(self):
        pool = self.pools.first()
        subnet = self.subnets.first()
        pool_dict = {'pool': self.api_pools.first()}
        vip_dict = {'vip': self.api_vips.first()}

        neutronclient.show_pool(pool.id).AndReturn(pool_dict)
        api.neutron.subnet_get(self.request, subnet.id).AndReturn(subnet)
        neutronclient.show_vip(pool.vip_id).AndReturn(vip_dict)
        neutronclient.list_members(pool_id=pool.id).AndReturn(
            {'members': self.api_members.list()})
        monitor = self.api_monitors.first()
        for pool_mon in pool.health_monitors:
            neutronclient.show_health_monitor(pool_mon).AndReturn(
                {'health_monitor': monitor})
        self.mox.ReplayAll()

        ret_val = api.lbaas.pool_get(self.request, pool.id)
        self.assertIsInstance(ret_val, api.lbaas.Pool)
        self.assertIsInstance(ret_val.vip, api.lbaas.Vip)
        self.assertEqual(ret_val.vip.id, vip_dict['vip']['id'])
        self.assertIsInstance(ret_val.subnet, api.neutron.Subnet)
        self.assertEqual(ret_val.subnet.id, subnet.id)
        self.assertEqual(3, len(ret_val.members))
        self.assertIsInstance(ret_val.members[0], api.lbaas.Member)
        self.assertEqual(len(pool.health_monitors),
                         len(ret_val.health_monitors))
        self.assertIsInstance(ret_val.health_monitors[0],
                              api.lbaas.PoolMonitor)

    @test.create_stubs({neutronclient: ('update_pool',)})
    def test_pool_update(self):
        form_data = {'name': 'pool1name',
                     'description': 'pool1description',
                     'subnet_id': '12381d38-c3eb-4fee-9763-12de3338041e',
                     'protocol': 'HTTPS',
                     'lb_method': 'LEAST_CONNECTION',
                     'admin_state_up': True
                     }

        pool = {'pool': {'id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                         'name': 'pool1name',
                         'description': 'pool1description',
                         'subnet_id': '12381d38-c3eb-4fee-9763-12de3338041e',
                         'protocol': 'HTTPS',
                         'lb_method': 'LEAST_CONNECTION',
                         'admin_state_up': True
                         }}
        neutronclient.update_pool(pool['pool']['id'],
                                  form_data).AndReturn(pool)
        self.mox.ReplayAll()

        ret_val = api.lbaas.pool_update(self.request,
                                        pool['pool']['id'], **form_data)
        self.assertIsInstance(ret_val, api.lbaas.Pool)

    @test.create_stubs({neutronclient: ('create_health_monitor',)})
    def test_pool_health_monitor_create(self):
        form_data = {'type': 'PING',
                     'delay': '10',
                     'timeout': '10',
                     'max_retries': '10',
                     'admin_state_up': True
                     }
        monitor = {'health_monitor': {
            'id': 'abcdef-c3eb-4fee-9763-12de3338041e',
            'type': 'PING',
            'delay': '10',
            'timeout': '10',
            'max_retries': '10',
            'admin_state_up': True}}
        neutronclient.create_health_monitor({
            'health_monitor': form_data}).AndReturn(monitor)
        self.mox.ReplayAll()

        ret_val = api.lbaas.pool_health_monitor_create(
            self.request, **form_data)
        self.assertIsInstance(ret_val, api.lbaas.PoolMonitor)

    @test.create_stubs({neutronclient: ('list_health_monitors',)})
    def test_pool_health_monitor_list(self):
        monitors = {'health_monitors': [
            {'id': 'abcdef-c3eb-4fee-9763-12de3338041e',
             'type': 'PING',
             'delay': '10',
             'timeout': '10',
             'max_retries': '10',
             'http_method': 'GET',
             'url_path': '/monitor',
             'expected_codes': '200',
             'admin_state_up': True}, ]}

        neutronclient.list_health_monitors().AndReturn(monitors)
        self.mox.ReplayAll()

        ret_val = api.lbaas.pool_health_monitor_list(self.request)
        for v in ret_val:
            self.assertIsInstance(v, api.lbaas.PoolMonitor)
            self.assertTrue(v.id)

    @test.create_stubs({neutronclient: ('show_health_monitor',
                                        'list_pools')})
    def test_pool_health_monitor_get(self):
        monitor = self.api_monitors.first()
        neutronclient.show_health_monitor(
            monitor['id']).AndReturn({'health_monitor': monitor})
        neutronclient.list_pools(id=[p['pool_id'] for p in monitor['pools']]
                                 ).AndReturn({'pools': self.api_pools.list()})
        self.mox.ReplayAll()

        ret_val = api.lbaas.pool_health_monitor_get(
            self.request, monitor['id'])
        self.assertIsInstance(ret_val, api.lbaas.PoolMonitor)
        self.assertEqual(3, len(ret_val.pools))
        self.assertIsInstance(ret_val.pools[0], api.lbaas.Pool)

    @test.create_stubs({neutronclient: ('create_member', )})
    def test_member_create(self):
        form_data = {'pool_id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                     'address': '10.0.1.2',
                     'protocol_port': '80',
                     'weight': '10',
                     'admin_state_up': True
                     }

        member = {'member':
                  {'id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                   'pool_id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                   'address': '10.0.1.2',
                   'protocol_port': '80',
                   'weight': '10',
                   'admin_state_up': True}}

        neutronclient.create_member({'member': form_data}).AndReturn(member)
        self.mox.ReplayAll()

        ret_val = api.lbaas.member_create(self.request, **form_data)
        self.assertIsInstance(ret_val, api.lbaas.Member)

    @test.create_stubs({neutronclient: ('list_members', 'list_pools')})
    def test_member_list(self):
        members = {'members': self.api_members.list()}
        pools = {'pools': self.api_pools.list()}

        neutronclient.list_members().AndReturn(members)
        neutronclient.list_pools().AndReturn(pools)
        self.mox.ReplayAll()

        ret_val = api.lbaas.member_list(self.request)
        for v in ret_val:
            self.assertIsInstance(v, api.lbaas.Member)
            self.assertTrue(v.id)

    @test.create_stubs({neutronclient: ('show_member', 'show_pool')})
    def test_member_get(self):
        member = self.members.first()
        member_dict = {'member': self.api_members.first()}
        pool_dict = {'pool': self.api_pools.first()}

        neutronclient.show_member(member.id).AndReturn(member_dict)
        neutronclient.show_pool(member.pool_id).AndReturn(pool_dict)
        self.mox.ReplayAll()

        ret_val = api.lbaas.member_get(self.request, member.id)
        self.assertIsInstance(ret_val, api.lbaas.Member)

    @test.create_stubs({neutronclient: ('update_member',)})
    def test_member_update(self):
        form_data = {'pool_id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                     'address': '10.0.1.4',
                     'protocol_port': '80',
                     'weight': '10',
                     'admin_state_up': True
                     }

        member = {'member': {'id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                             'pool_id': 'abcdef-c3eb-4fee-9763-12de3338041e',
                             'address': '10.0.1.2',
                             'protocol_port': '80',
                             'weight': '10',
                             'admin_state_up': True
                             }}

        neutronclient.update_member(member['member']['id'],
                                    form_data).AndReturn(member)
        self.mox.ReplayAll()

        ret_val = api.lbaas.member_update(self.request,
                                          member['member']['id'], **form_data)
        self.assertIsInstance(ret_val, api.lbaas.Member)
