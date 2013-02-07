# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 NEC Corporation
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

from django import http
from mox import IsA

from novaclient.v1_1.floating_ip_pools import FloatingIPPool

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class NetworkApiNovaFloatingIpTests(test.APITestCase):
    def setUp(self):
        super(NetworkApiNovaFloatingIpTests, self).setUp()
        self.mox.StubOutWithMock(api.base, 'is_service_enabled')
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .AndReturn(False)

    def test_floating_ip_pools_list(self):
        pool_names = ['pool1', 'pool2']
        pools = [FloatingIPPool(None, {'name': pool}) for pool in pool_names]
        novaclient = self.stub_novaclient()
        novaclient.floating_ip_pools = self.mox.CreateMockAnything()
        novaclient.floating_ip_pools.list().AndReturn(pools)
        self.mox.ReplayAll()

        ret = api.network.floating_ip_pools_list(self.request)
        self.assertEqual([p.name for p in ret], pool_names)

    def test_floating_ip_list(self):
        fips = self.api_floating_ips.list()
        novaclient = self.stub_novaclient()
        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.floating_ips.list().AndReturn(fips)
        self.mox.ReplayAll()

        ret = api.network.tenant_floating_ip_list(self.request)
        for r, e in zip(ret, fips):
            for attr in ['id', 'ip', 'pool', 'fixed_ip', 'instance_id']:
                self.assertEqual(r.__getattr__(attr), e.__getattr__(attr))
            self.assertEqual(r.port_id, e.instance_id)

    def test_floating_ip_get(self):
        fip = self.api_floating_ips.first()
        novaclient = self.stub_novaclient()
        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.floating_ips.get(fip.id).AndReturn(fip)
        self.mox.ReplayAll()

        ret = api.network.tenant_floating_ip_get(self.request, fip.id)
        for attr in ['id', 'ip', 'pool', 'fixed_ip', 'instance_id']:
            self.assertEqual(ret.__getattr__(attr), fip.__getattr__(attr))
        self.assertEqual(ret.port_id, fip.instance_id)

    def test_floating_ip_allocate(self):
        pool_name = 'fip_pool'
        fip = self.api_floating_ips.first()
        novaclient = self.stub_novaclient()
        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.floating_ips.create(pool=pool_name).AndReturn(fip)
        self.mox.ReplayAll()

        ret = api.network.tenant_floating_ip_allocate(self.request, pool_name)
        for attr in ['id', 'ip', 'pool', 'fixed_ip', 'instance_id']:
            self.assertEqual(ret.__getattr__(attr), fip.__getattr__(attr))
        self.assertEqual(ret.port_id, fip.instance_id)

    def test_floating_ip_release(self):
        fip = self.api_floating_ips.first()
        novaclient = self.stub_novaclient()
        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.floating_ips.delete(fip.id)
        self.mox.ReplayAll()

        api.network.tenant_floating_ip_release(self.request, fip.id)

    def test_floating_ip_associate(self):
        server = api.nova.Server(self.servers.first(), self.request)
        floating_ip = self.floating_ips.first()

        novaclient = self.stub_novaclient()
        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.get(server.id).AndReturn(server)
        novaclient.floating_ips.get(floating_ip.id).AndReturn(floating_ip)
        novaclient.servers.add_floating_ip(server.id, floating_ip.ip) \
                          .AndReturn(server)
        self.mox.ReplayAll()

        api.network.floating_ip_associate(self.request,
                                          floating_ip.id,
                                          server.id)

    def test_floating_ip_disassociate(self):
        server = api.nova.Server(self.servers.first(), self.request)
        floating_ip = self.api_floating_ips.first()

        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.floating_ips = self.mox.CreateMockAnything()
        novaclient.servers.get(server.id).AndReturn(server)
        novaclient.floating_ips.get(floating_ip.id).AndReturn(floating_ip)
        novaclient.servers.remove_floating_ip(server.id, floating_ip.ip) \
                          .AndReturn(server)
        self.mox.ReplayAll()

        api.network.floating_ip_disassociate(self.request,
                                             floating_ip.id,
                                             server.id)

    def test_floating_ip_target_list(self):
        servers = self.servers.list()
        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.servers.list().AndReturn(servers)
        self.mox.ReplayAll()

        targets = api.network.floating_ip_target_list(self.request)
        for target, server in zip(targets, servers):
            self.assertEqual(target.id, server.id)
            self.assertEqual(target.name, '%s (%s)' % (server.name, server.id))

    def test_floating_ip_target_get_by_instance(self):
        self.mox.ReplayAll()
        instance_id = self.servers.first().id
        ret = api.network.floating_ip_target_get_by_instance(self.request,
                                                             instance_id)
        self.assertEqual(instance_id, ret)


class NetworkApiQuantumFloatingIpTests(test.APITestCase):
    def setUp(self):
        super(NetworkApiQuantumFloatingIpTests, self).setUp()
        self.mox.StubOutWithMock(api.base, 'is_service_enabled')
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .AndReturn(True)
        self.qclient = self.stub_quantumclient()

    def test_floating_ip_pools_list(self):
        search_opts = {'router:external': True}
        ext_nets = [n for n in self.api_networks.list()
                    if n['router:external']]
        self.qclient.list_networks(**search_opts) \
            .AndReturn({'networks': ext_nets})
        self.mox.ReplayAll()

        rets = api.network.floating_ip_pools_list(self.request)
        for attr in ['id', 'name']:
            self.assertEqual([p.__getattr__(attr) for p in rets],
                             [p[attr] for p in ext_nets])

    def test_floating_ip_list(self):
        fips = self.api_q_floating_ips.list()
        self.qclient.list_floatingips().AndReturn({'floatingips': fips})
        self.qclient.list_ports().AndReturn({'ports': self.api_ports.list()})
        self.mox.ReplayAll()

        rets = api.network.tenant_floating_ip_list(self.request)
        assoc_port = self.api_ports.list()[1]
        self.assertEqual(len(fips), len(rets))
        for ret, exp in zip(rets, fips):
            for attr in ['id', 'ip', 'pool', 'fixed_ip', 'port_id']:
                self.assertEqual(ret.__getattr__(attr), exp[attr])
            if exp['port_id']:
                dev_id = assoc_port['device_id'] if exp['port_id'] else None
                self.assertEqual(ret.instance_id, dev_id)

    def test_floating_ip_get_associated(self):
        fip = self.api_q_floating_ips.list()[1]
        assoc_port = self.api_ports.list()[1]
        self.qclient.show_floatingip(fip['id']).AndReturn({'floatingip': fip})
        self.qclient.show_port(assoc_port['id']) \
            .AndReturn({'port': assoc_port})
        self.mox.ReplayAll()

        ret = api.network.tenant_floating_ip_get(self.request, fip['id'])
        for attr in ['id', 'ip', 'pool', 'fixed_ip', 'port_id']:
            self.assertEqual(ret.__getattr__(attr), fip[attr])
        self.assertEqual(ret.instance_id, assoc_port['device_id'])

    def test_floating_ip_get_unassociated(self):
        fip = self.api_q_floating_ips.list()[0]
        self.qclient.show_floatingip(fip['id']).AndReturn({'floatingip': fip})
        self.mox.ReplayAll()

        ret = api.network.tenant_floating_ip_get(self.request, fip['id'])
        for attr in ['id', 'ip', 'pool', 'fixed_ip', 'port_id']:
            self.assertEqual(ret.__getattr__(attr), fip[attr])
        self.assertEqual(ret.instance_id, None)

    def test_floating_ip_allocate(self):
        ext_nets = [n for n in self.api_networks.list()
                    if n['router:external']]
        ext_net = ext_nets[0]
        fip = self.api_q_floating_ips.first()
        self.qclient.create_floatingip(
            {'floatingip': {'floating_network_id': ext_net['id']}}) \
            .AndReturn({'floatingip': fip})
        self.mox.ReplayAll()

        ret = api.network.tenant_floating_ip_allocate(self.request,
                                                      ext_net['id'])
        for attr in ['id', 'ip', 'pool', 'fixed_ip', 'port_id']:
            self.assertEqual(ret.__getattr__(attr), fip[attr])
        self.assertEqual(ret.instance_id, None)

    def test_floating_ip_release(self):
        fip = self.api_q_floating_ips.first()
        self.qclient.delete_floatingip(fip['id'])
        self.mox.ReplayAll()

        api.network.tenant_floating_ip_release(self.request, fip['id'])

    def test_floating_ip_associate(self):
        fip = self.api_q_floating_ips.list()[1]
        assoc_port = self.api_ports.list()[1]
        ip_address = assoc_port['fixed_ips'][0]['ip_address']
        target_id = '%s_%s' % (assoc_port['id'], ip_address)
        params = {'port_id': assoc_port['id'],
                  'fixed_ip_address': ip_address}
        self.qclient.update_floatingip(fip['id'],
                                       {'floatingip': params})
        self.mox.ReplayAll()

        api.network.floating_ip_associate(self.request, fip['id'], target_id)

    def test_floating_ip_disassociate(self):
        fip = self.api_q_floating_ips.list()[1]
        assoc_port = self.api_ports.list()[1]
        ip_address = assoc_port['fixed_ips'][0]['ip_address']
        target_id = '%s_%s' % (assoc_port['id'], ip_address)
        self.qclient.update_floatingip(fip['id'],
                                       {'floatingip': {'port_id': None}})
        self.mox.ReplayAll()

        api.network.floating_ip_disassociate(self.request, fip['id'],
                                             target_id)

    def _get_target_id(self, port):
        param = {'id': port['id'],
                 'addr': port['fixed_ips'][0]['ip_address']}
        return '%(id)s_%(addr)s' % param

    def _get_target_name(self, port):
        param = {'svrid': port['device_id'],
                 'addr': port['fixed_ips'][0]['ip_address']}
        return 'server_%(svrid)s: %(addr)s' % param

    def test_floating_ip_target_list(self):
        ports = self.api_ports.list()
        target_ports = [(self._get_target_id(p),
                         self._get_target_name(p)) for p in ports
                        if not p['device_owner'].startswith('network:')]

        self.qclient.list_ports().AndReturn({'ports': ports})
        servers = self.servers.list()
        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        search_opts = {'project_id': self.request.user.tenant_id}
        novaclient.servers.list(True, search_opts).AndReturn(servers)
        self.mox.ReplayAll()

        rets = api.network.floating_ip_target_list(self.request)
        self.assertEqual(len(rets), len(target_ports))
        for ret, exp in zip(rets, target_ports):
            self.assertEqual(ret.id, exp[0])
            self.assertEqual(ret.name, exp[1])

    def test_floating_ip_target_get_by_instance(self):
        ports = self.api_ports.list()
        candidates = [p for p in ports if p['device_id'] == '1']
        search_opts = {'device_id': '1'}
        self.qclient.list_ports(**search_opts).AndReturn({'ports': candidates})
        self.mox.ReplayAll()

        ret = api.network.floating_ip_target_get_by_instance(self.request, '1')
        self.assertEqual(ret, self._get_target_id(candidates[0]))
