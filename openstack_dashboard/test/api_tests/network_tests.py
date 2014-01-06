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

import copy
import itertools
import uuid

from django import http
from mox import IsA  # noqa

from novaclient.v1_1 import floating_ip_pools

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class NetworkClientTestCase(test.APITestCase):
    def test_networkclient_no_neutron(self):
        self.mox.StubOutWithMock(api.base, 'is_service_enabled')
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .AndReturn(False)
        self.mox.ReplayAll()

        nc = api.network.NetworkClient(self.request)
        self.assertIsInstance(nc.floating_ips, api.nova.FloatingIpManager)
        self.assertIsInstance(nc.secgroups, api.nova.SecurityGroupManager)

    def test_networkclient_neutron(self):
        self.mox.StubOutWithMock(api.base, 'is_service_enabled')
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .AndReturn(True)
        self.neutronclient = self.stub_neutronclient()
        self.neutronclient.list_extensions() \
            .AndReturn({'extensions': self.api_extensions.list()})
        self.mox.ReplayAll()

        nc = api.network.NetworkClient(self.request)
        self.assertIsInstance(nc.floating_ips, api.neutron.FloatingIpManager)
        self.assertIsInstance(nc.secgroups, api.neutron.SecurityGroupManager)

    def test_networkclient_neutron_with_nova_security_group(self):
        self.mox.StubOutWithMock(api.base, 'is_service_enabled')
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .AndReturn(True)
        self.neutronclient = self.stub_neutronclient()
        self.neutronclient.list_extensions().AndReturn({'extensions': []})
        self.mox.ReplayAll()

        nc = api.network.NetworkClient(self.request)
        self.assertIsInstance(nc.floating_ips, api.neutron.FloatingIpManager)
        self.assertIsInstance(nc.secgroups, api.nova.SecurityGroupManager)


class NetworkApiNovaTestBase(test.APITestCase):
    def setUp(self):
        super(NetworkApiNovaTestBase, self).setUp()
        self.mox.StubOutWithMock(api.base, 'is_service_enabled')
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .AndReturn(False)


class NetworkApiNovaSecurityGroupTests(NetworkApiNovaTestBase):
    def test_server_update_security_groups(self):
        all_secgroups = self.security_groups.list()
        added_secgroup = all_secgroups[2]
        rm_secgroup = all_secgroups[0]
        cur_secgroups_raw = [{'id': sg.id, 'name': sg.name,
                              'rules': []}
                             for sg in all_secgroups[0:2]]
        cur_secgroups_ret = {'security_groups': cur_secgroups_raw}
        new_sg_ids = [sg.id for sg in all_secgroups[1:3]]
        instance_id = self.servers.first().id

        novaclient = self.stub_novaclient()
        novaclient.security_groups = self.mox.CreateMockAnything()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.client = self.mox.CreateMockAnything()
        novaclient.security_groups.list().AndReturn(all_secgroups)
        url = '/servers/%s/os-security-groups' % instance_id
        novaclient.client.get(url).AndReturn((200, cur_secgroups_ret))
        novaclient.servers.add_security_group(instance_id, added_secgroup.name)
        novaclient.servers.remove_security_group(instance_id, rm_secgroup.name)
        self.mox.ReplayAll()

        api.network.server_update_security_groups(
            self.request, instance_id, new_sg_ids)


class NetworkApiNovaFloatingIpTests(NetworkApiNovaTestBase):
    def test_floating_ip_pools_list(self):
        pool_names = ['pool1', 'pool2']
        pools = [floating_ip_pools.FloatingIPPool(
            None, {'name': pool}) for pool in pool_names]
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


class NetworkApiNeutronTestBase(test.APITestCase):
    def setUp(self):
        super(NetworkApiNeutronTestBase, self).setUp()
        self.mox.StubOutWithMock(api.base, 'is_service_enabled')
        api.base.is_service_enabled(IsA(http.HttpRequest), 'network') \
            .AndReturn(True)
        self.qclient = self.stub_neutronclient()
        self.qclient.list_extensions() \
            .AndReturn({'extensions': self.api_extensions.list()})


class NetworkApiNeutronSecurityGroupTests(NetworkApiNeutronTestBase):

    def setUp(self):
        super(NetworkApiNeutronSecurityGroupTests, self).setUp()
        self.sg_dict = dict([(sg['id'], sg['name']) for sg
                             in self.api_q_secgroups.list()])

    def _cmp_sg_rule(self, exprule, retrule):
        self.assertEqual(exprule['id'], retrule.id)
        self.assertEqual(exprule['security_group_id'],
                         retrule.parent_group_id)
        self.assertEqual(exprule['direction'], retrule.direction)
        self.assertEqual(exprule['ethertype'], retrule.ethertype)
        self.assertEqual(exprule['port_range_min'], retrule.from_port)
        self.assertEqual(exprule['port_range_max'], retrule.to_port)
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
        for (exprule, retrule) in itertools.izip(exp_rules, ret_sg.rules):
            self._cmp_sg_rule(exprule, retrule)

    def test_security_group_list(self):
        sgs = self.api_q_secgroups.list()
        tenant_id = self.request.user.tenant_id
        # use deepcopy to ensure self.api_q_secgroups is not modified.
        self.qclient.list_security_groups(tenant_id=tenant_id) \
            .AndReturn({'security_groups': copy.deepcopy(sgs)})
        self.mox.ReplayAll()

        rets = api.network.security_group_list(self.request)
        self.assertEqual(len(sgs), len(rets))
        for (exp, ret) in itertools.izip(sgs, rets):
            self._cmp_sg(exp, ret)

    def test_security_group_get(self):
        secgroup = self.api_q_secgroups.first()
        sg_ids = set([secgroup['id']] +
                     [rule['remote_group_id'] for rule
                      in secgroup['security_group_rules']
                      if rule['remote_group_id']])
        related_sgs = [sg for sg in self.api_q_secgroups.list()
                       if sg['id'] in sg_ids]
        # use deepcopy to ensure self.api_q_secgroups is not modified.
        self.qclient.show_security_group(secgroup['id']) \
            .AndReturn({'security_group': copy.deepcopy(secgroup)})
        self.qclient.list_security_groups(id=sg_ids, fields=['id', 'name']) \
            .AndReturn({'security_groups': related_sgs})
        self.mox.ReplayAll()
        ret = api.network.security_group_get(self.request, secgroup['id'])
        self._cmp_sg(secgroup, ret)

    def test_security_group_create(self):
        secgroup = self.api_q_secgroups.list()[1]
        body = {'security_group':
                    {'name': secgroup['name'],
                     'description': secgroup['description']}}
        self.qclient.create_security_group(body) \
            .AndReturn({'security_group': copy.deepcopy(secgroup)})
        self.mox.ReplayAll()
        ret = api.network.security_group_create(self.request, secgroup['name'],
                                                secgroup['description'])
        self._cmp_sg(secgroup, ret)

    def test_security_group_update(self):
        secgroup = self.api_q_secgroups.list()[1]
        secgroup = copy.deepcopy(secgroup)
        secgroup['name'] = 'newname'
        secgroup['description'] = 'new description'
        body = {'security_group':
                    {'name': secgroup['name'],
                     'description': secgroup['description']}}
        self.qclient.update_security_group(secgroup['id'], body) \
            .AndReturn({'security_group': secgroup})
        self.mox.ReplayAll()
        ret = api.network.security_group_update(self.request,
                                                secgroup['id'],
                                                secgroup['name'],
                                                secgroup['description'])
        self._cmp_sg(secgroup, ret)

    def test_security_group_delete(self):
        secgroup = self.api_q_secgroups.first()
        self.qclient.delete_security_group(secgroup['id'])
        self.mox.ReplayAll()
        api.network.security_group_delete(self.request, secgroup['id'])

    def test_security_group_rule_create(self):
        sg_rule = [r for r in self.api_q_secgroup_rules.list()
                   if r['protocol'] == 'tcp' and r['remote_ip_prefix']][0]
        sg_id = sg_rule['security_group_id']
        secgroup = [sg for sg in self.api_q_secgroups.list()
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

        ret = api.network.security_group_rule_create(
            self.request, sg_rule['security_group_id'],
            sg_rule['direction'], sg_rule['ethertype'], sg_rule['protocol'],
            sg_rule['port_range_min'], sg_rule['port_range_max'],
            sg_rule['remote_ip_prefix'], sg_rule['remote_group_id'])
        self._cmp_sg_rule(sg_rule, ret)

    def test_security_group_rule_delete(self):
        sg_rule = self.api_q_secgroup_rules.first()
        self.qclient.delete_security_group_rule(sg_rule['id'])
        self.mox.ReplayAll()
        api.network.security_group_rule_delete(self.request, sg_rule['id'])

    def _get_instance(self, cur_sg_ids):
        instance_port = [p for p in self.api_ports.list()
                         if p['device_owner'].startswith('compute:')][0]
        instance_id = instance_port['device_id']
        # Emulate an intance with two ports
        instance_ports = []
        for _i in range(2):
            p = copy.deepcopy(instance_port)
            p['id'] = str(uuid.uuid4())
            p['security_groups'] = cur_sg_ids
            instance_ports.append(p)
        return (instance_id, instance_ports)

    def test_server_security_groups(self):
        cur_sg_ids = [sg['id'] for sg in self.api_q_secgroups.list()[:2]]
        instance_id, instance_ports = self._get_instance(cur_sg_ids)

        self.qclient.list_ports(device_id=instance_id) \
            .AndReturn({'ports': instance_ports})
        secgroups = copy.deepcopy(self.api_q_secgroups.list())
        self.qclient.list_security_groups(id=set(cur_sg_ids)) \
            .AndReturn({'security_groups': secgroups})
        self.mox.ReplayAll()

        api.network.server_security_groups(self.request, instance_id)

    def test_server_update_security_groups(self):
        cur_sg_ids = [self.api_q_secgroups.first()['id']]
        new_sg_ids = [sg['id'] for sg in self.api_q_secgroups.list()[:2]]
        instance_id, instance_ports = self._get_instance(cur_sg_ids)

        self.qclient.list_ports(device_id=instance_id) \
            .AndReturn({'ports': instance_ports})
        for p in instance_ports:
            body = {'port': {'security_groups': new_sg_ids}}
            self.qclient.update_port(p['id'], body=body).AndReturn({'port': p})
        self.mox.ReplayAll()
        api.network.server_update_security_groups(
            self.request, instance_id, new_sg_ids)

    def test_security_group_backend(self):
        self.mox.ReplayAll()
        self.assertEqual(api.network.security_group_backend(self.request),
                         'neutron')


class NetworkApiNeutronFloatingIpTests(NetworkApiNeutronTestBase):
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
        filters = {'tenant_id': self.request.user.tenant_id}
        self.qclient.list_floatingips(**filters) \
            .AndReturn({'floatingips': fips})
        self.qclient.list_ports(**filters) \
            .AndReturn({'ports': self.api_ports.list()})
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
        filters = {'tenant_id': self.request.user.tenant_id}
        self.qclient.list_ports(**filters).AndReturn({'ports': ports})
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

    def test_target_floating_ip_port_by_instance(self):
        ports = self.api_ports.list()
        candidates = [p for p in ports if p['device_id'] == '1']
        search_opts = {'device_id': '1'}
        self.qclient.list_ports(**search_opts).AndReturn({'ports': candidates})
        self.mox.ReplayAll()

        ret = api.network.floating_ip_target_list_by_instance(self.request,
                                                              '1')
        self.assertEqual(ret[0], self._get_target_id(candidates[0]))
        self.assertEqual(len(ret), len(candidates))
