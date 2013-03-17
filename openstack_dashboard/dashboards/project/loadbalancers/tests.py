# vim: tabstop=4 shiftwidth=4 softtabstop=4

import json

from mox import IsA
from django import http
from django.core.urlresolvers import reverse, reverse_lazy

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.api.lbaas import Pool, Vip, Member, PoolMonitor

from .tabs import LoadBalancerTabs, MembersTab, PoolsTab, MonitorsTab
from .workflows import AddPool, AddMember, AddMonitor, AddVip


class LoadBalancerTests(test.TestCase):
    class AttributeDict(dict):
        def __getattr__(self, attr):
            return self[attr]

        def __setattr__(self, attr, value):
            self[attr] = value

    DASHBOARD = 'project'
    INDEX_URL = reverse_lazy('horizon:%s:loadbalancers:index' % DASHBOARD)

    ADDPOOL_PATH = 'horizon:%s:loadbalancers:addpool' % DASHBOARD
    ADDVIP_PATH = 'horizon:%s:loadbalancers:addvip' % DASHBOARD
    ADDMEMBER_PATH = 'horizon:%s:loadbalancers:addmember' % DASHBOARD
    ADDMONITOR_PATH = 'horizon:%s:loadbalancers:addmonitor' % DASHBOARD

    POOL_DETAIL_PATH = 'horizon:%s:loadbalancers:pooldetails' % DASHBOARD
    VIP_DETAIL_PATH = 'horizon:%s:loadbalancers:vipdetails' % DASHBOARD
    MEMBER_DETAIL_PATH = 'horizon:%s:loadbalancers:memberdetails' % DASHBOARD
    MONITOR_DETAIL_PATH = 'horizon:%s:loadbalancers:monitordetails' % DASHBOARD

    def set_up_expect(self):
        # retrieve pools
        subnet = self.subnets.first()

        vip1 = self.vips.first()

        vip2 = self.vips.list()[1]

        api.lbaas.pools_get(
            IsA(http.HttpRequest)).AndReturn(self.pools.list())

        api.lbaas.vip_get(IsA(http.HttpRequest), vip1.id).AndReturn(vip1)
        api.lbaas.vip_get(IsA(http.HttpRequest), vip2.id).AndReturn(vip2)

        # retrieves members
        api.lbaas.members_get(
            IsA(http.HttpRequest)).AndReturn(self.members.list())

        pool1 = self.pools.first()
        pool2 = self.pools.list()[1]

        api.lbaas.pool_get(IsA(http.HttpRequest),
                           self.members.list()[0].pool_id).AndReturn(pool1)
        api.lbaas.pool_get(IsA(http.HttpRequest),
                           self.members.list()[1].pool_id).AndReturn(pool2)

        # retrieves monitors
        api.lbaas.pool_health_monitors_get(
            IsA(http.HttpRequest)).AndReturn(self.monitors.list())

    def set_up_expect_with_exception(self):
        api.lbaas.pools_get(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.quantum)
        api.lbaas.members_get(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.quantum)
        api.lbaas.pool_health_monitors_get(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.quantum)

    @test.create_stubs({api.lbaas: ('pools_get', 'vip_get',
                                    'members_get', 'pool_get',
                                    'pool_health_monitors_get'),
                        api.quantum: ('subnet_get',)})
    def test_index_pools(self):
        self.set_up_expect()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res, '%s/loadbalancers/details_tabs.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['table'].data),
                         len(self.pools.list()))

    @test.create_stubs({api.lbaas: ('pools_get', 'vip_get',
                                    'members_get', 'pool_get',
                                    'pool_health_monitors_get'),
                        api.quantum: ('subnet_get',)})
    def test_index_members(self):
        self.set_up_expect()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL + '?tab=lbtabs__members')

        self.assertTemplateUsed(res, '%s/loadbalancers/details_tabs.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['memberstable_table'].data),
                              len(self.members.list()))

    @test.create_stubs({api.lbaas: ('pools_get', 'vip_get',
                                    'pool_health_monitors_get',
                                    'members_get', 'pool_get'),
                        api.quantum: ('subnet_get',)})
    def test_index_monitors(self):
        self.set_up_expect()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL + '?tab=lbtabs__monitors')

        self.assertTemplateUsed(res, '%s/loadbalancers/details_tabs.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['monitorstable_table'].data),
                              len(self.monitors.list()))

    @test.create_stubs({api.lbaas: ('pools_get', 'members_get',
                                    'pool_health_monitors_get')})
    def test_index_exception_pools(self):
        self.set_up_expect_with_exception()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)

        self.assertTemplateUsed(res,
                                '%s/loadbalancers/details_tabs.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res,
                                'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['table'].data), 0)

    @test.create_stubs({api.lbaas: ('pools_get', 'members_get',
                                    'pool_health_monitors_get')})
    def test_index_exception_members(self):
        self.set_up_expect_with_exception()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL + '?tab=lbtabs__members')

        self.assertTemplateUsed(res,
                                '%s/loadbalancers/details_tabs.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res,
                                'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['memberstable_table'].data), 0)

    @test.create_stubs({api.lbaas: ('pools_get', 'members_get',
                                    'pool_health_monitors_get')})
    def test_index_exception_monitors(self):
        self.set_up_expect_with_exception()

        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL + '?tab=lbtabs__monitors')

        self.assertTemplateUsed(res,
                                '%s/loadbalancers/details_tabs.html'
                                % self.DASHBOARD)
        self.assertTemplateUsed(res,
                                'horizon/common/_detail_table.html')
        self.assertEqual(len(res.context['monitorstable_table'].data), 0)

    @test.create_stubs({api.quantum: ('network_list_for_tenant',),
                        api.lbaas: ('pool_create', )})
    def test_add_pool_post(self):
        pool = self.pools.first()

        subnet = self.subnets.first()
        networks = [{'subnets': [subnet, ]}, ]

        api.quantum.network_list_for_tenant(
            IsA(http.HttpRequest), subnet.tenant_id).AndReturn(networks)

        api.lbaas.pool_create(
            IsA(http.HttpRequest),
            name=pool.name,
            description=pool.description,
            subnet_id=pool.subnet_id,
            protocol=pool.protocol,
            lb_method=pool.lb_method,
            admin_state_up=pool.admin_state_up).AndReturn(Pool(pool))

        self.mox.ReplayAll()

        form_data = {'name': pool.name,
                     'description': pool.description,
                     'subnet_id': pool.subnet_id,
                     'protocol': pool.protocol,
                     'lb_method': pool.lb_method,
                     'admin_state_up': pool.admin_state_up}

        res = self.client.post(reverse(self.ADDPOOL_PATH), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.quantum: ('network_list_for_tenant',)})
    def test_add_pool_get(self):
        subnet = self.subnets.first()

        networks = [{'subnets': [subnet, ]}, ]

        api.quantum.network_list_for_tenant(
            IsA(http.HttpRequest), subnet.tenant_id).AndReturn(networks)

        self.mox.ReplayAll()

        res = self.client.get(reverse(self.ADDPOOL_PATH))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, 'project/loadbalancers/addpool.html')
        self.assertEqual(workflow.name, AddPool.name)

        expected_objs = ['<AddPoolStep: addpoolaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.lbaas: ('pools_get', 'member_create'),
                        api.quantum: ('port_list',),
                        api.nova: ('server_list',)})
    def test_add_member_post(self):
        member = self.members.first()

        server1 = self.AttributeDict({'id':
                                      '12381d38-c3eb-4fee-9763-12de3338042e',
                                      'name': 'vm1'})
        server2 = self.AttributeDict({'id':
                                      '12381d38-c3eb-4fee-9763-12de3338043e',
                                      'name': 'vm2'})

        port1 = self.AttributeDict(
            {'fixed_ips': [{'ip_address': member.address}]})

        api.lbaas.pools_get(IsA(http.HttpRequest)).AndReturn(self.pools.list())

        api.nova.server_list(IsA(http.HttpRequest)).AndReturn([server1,
                                                               server2])

        api.quantum.port_list(IsA(http.HttpRequest),
                              device_id=server1.id).AndReturn([port1, ])

        api.lbaas.member_create(
            IsA(http.HttpRequest),
            pool_id=member.pool_id,
            address=member.address,
            protocol_port=member.protocol_port,
            weight=member.weight,
            members=[server1.id],
            admin_state_up=member.admin_state_up).AndReturn(Member(member))

        self.mox.ReplayAll()

        form_data = {'pool_id': member.pool_id,
                     'address': member.address,
                     'protocol_port': member.protocol_port,
                     'weight': member.weight,
                     'members': [server1.id],
                     'admin_state_up': member.admin_state_up}

        res = self.client.post(reverse(self.ADDMEMBER_PATH), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.lbaas: ('pools_get',),
                        api.nova: ('server_list',)})
    def test_add_member_get(self):
        server1 = self.AttributeDict({'id':
                                      '12381d38-c3eb-4fee-9763-12de3338042e',
                                      'name': 'vm1'})
        server2 = self.AttributeDict({'id':
                                      '12381d38-c3eb-4fee-9763-12de3338043e',
                                      'name': 'vm2'})

        api.lbaas.pools_get(IsA(http.HttpRequest)).AndReturn(self.pools.list())
        api.nova.server_list(
            IsA(http.HttpRequest)).AndReturn([server1, server2])

        self.mox.ReplayAll()

        res = self.client.get(reverse(self.ADDMEMBER_PATH))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, 'project/loadbalancers/addmember.html')
        self.assertEqual(workflow.name, AddMember.name)

        expected_objs = ['<AddMemberStep: addmemberaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)
