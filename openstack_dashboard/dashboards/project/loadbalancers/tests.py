# vim: tabstop=4 shiftwidth=4 softtabstop=4

from mox import IsA  # noqa

from django.core.urlresolvers import reverse  # noqa
from django.core.urlresolvers import reverse_lazy  # noqa
from django import http

from horizon.workflows import views

from openstack_dashboard import api
from openstack_dashboard.api import lbaas
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.project.loadbalancers import workflows


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

    UPDATEPOOL_PATH = 'horizon:%s:loadbalancers:updatepool' % DASHBOARD
    UPDATEVIP_PATH = 'horizon:%s:loadbalancers:updatevip' % DASHBOARD
    UPDATEMEMBER_PATH = 'horizon:%s:loadbalancers:updatemember' % DASHBOARD
    UPDATEMONITOR_PATH = 'horizon:%s:loadbalancers:updatemonitor' % DASHBOARD

    ADDASSOC_PATH = 'horizon:%s:loadbalancers:addassociation' % DASHBOARD
    DELETEASSOC_PATH = 'horizon:%s:loadbalancers:deleteassociation' % DASHBOARD

    def set_up_expect(self):
        # retrieve pools
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
            IsA(http.HttpRequest)).MultipleTimes() \
                .AndReturn(self.monitors.list())

    def set_up_expect_with_exception(self):
        api.lbaas.pools_get(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.neutron)
        api.lbaas.members_get(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.neutron)
        api.lbaas.pool_health_monitors_get(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.neutron)

    @test.create_stubs({api.lbaas: ('pools_get', 'vip_get',
                                    'members_get', 'pool_get',
                                    'pool_health_monitors_get'),
                        api.neutron: ('subnet_get',)})
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
                        api.neutron: ('subnet_get',)})
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
                        api.neutron: ('subnet_get',)})
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

    @test.create_stubs({api.neutron: ('network_list_for_tenant',
                                      'provider_list',
                                      'is_extension_supported'),
                        api.lbaas: ('pool_create', )})
    def test_add_pool_post(self):
        pool = self.pools.first()

        subnet = self.subnets.first()
        networks = [{'subnets': [subnet, ]}, ]

        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'service-type').AndReturn(True)
        api.neutron.network_list_for_tenant(
            IsA(http.HttpRequest), subnet.tenant_id).AndReturn(networks)
        api.neutron.provider_list(IsA(http.HttpRequest)) \
            .AndReturn(self.providers.list())

        api.lbaas.pool_create(
            IsA(http.HttpRequest),
            name=pool.name,
            description=pool.description,
            subnet_id=pool.subnet_id,
            protocol=pool.protocol,
            lb_method=pool.lb_method,
            admin_state_up=pool.admin_state_up,
            provider=pool.provider).AndReturn(pool)

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

    @test.create_stubs({api.neutron: ('network_list_for_tenant',
                                      'provider_list',
                                      'is_extension_supported')})
    def test_add_pool_get(self):
        self._test_add_pool_get(with_service_type=True)

    @test.create_stubs({api.neutron: ('network_list_for_tenant',
                                      'provider_list',
                                      'is_extension_supported')})
    def test_add_pool_get_provider_list_exception(self):
        self._test_add_pool_get(with_service_type=True)

    @test.create_stubs({api.neutron: ('network_list_for_tenant',
                                      'is_extension_supported')})
    def test_add_pool_get_without_service_type_support(self):
        self._test_add_pool_get(with_service_type=False)

    def _test_add_pool_get(self, with_service_type=True,
                           with_provider_exception=False):
        subnet = self.subnets.first()
        default_provider = self.providers.first()['name']

        networks = [{'subnets': [subnet, ]}, ]

        api.neutron.is_extension_supported(
            IsA(http.HttpRequest), 'service-type').AndReturn(with_service_type)
        api.neutron.network_list_for_tenant(
            IsA(http.HttpRequest), subnet.tenant_id).AndReturn(networks)
        if with_service_type:
            prov_list = api.neutron.provider_list(IsA(http.HttpRequest))
            if with_provider_exception:
                prov_list.AndRaise(self.exceptions.neutron)
            else:
                prov_list.AndReturn(self.providers.list())

        self.mox.ReplayAll()

        res = self.client.get(reverse(self.ADDPOOL_PATH))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddPool.name)

        expected_objs = ['<AddPoolStep: addpoolaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

        if not with_service_type:
            self.assertNotContains(res, default_provider)
            self.assertContains(res, ('Provider for Load Balancer '
                                      'is not supported.'))
        elif with_provider_exception:
            self.assertNotContains(res, default_provider)
            self.assertContains(res, 'No provider is available.')
        else:
            self.assertContains(res, default_provider)

    @test.create_stubs({api.lbaas: ('pool_get', 'vip_create'),
                        api.neutron: ('subnet_get', )})
    def test_add_vip_post(self):
        vip = self.vips.first()

        subnet = self.subnets.first()
        pool = self.pools.first()

        api.lbaas.pool_get(
            IsA(http.HttpRequest), pool.id).MultipleTimes().AndReturn(pool)

        api.neutron.subnet_get(
            IsA(http.HttpRequest), subnet.id).AndReturn(subnet)

        api.lbaas.vip_create(
            IsA(http.HttpRequest),
            name=vip.name,
            description=vip.description,
            pool_id=vip.pool_id,
            address=vip.address,
            floatip_address=vip.floatip_address,
            other_address=vip.other_address,
            subnet=vip.subnet,
            subnet_id=vip.subnet_id,
            protocol_port=vip.protocol_port,
            protocol=vip.protocol,
            session_persistence=vip.session_persistence['type'],
            cookie_name=vip.session_persistence['cookie_name'],
            connection_limit=vip.connection_limit,
            admin_state_up=vip.admin_state_up).AndReturn(vip)

        self.mox.ReplayAll()

        form_data = {'name': vip.name,
                     'description': vip.description,
                     'pool_id': vip.pool_id,
                     'address': vip.address,
                     'floatip_address': vip.floatip_address,
                     'other_address': vip.other_address,
                     'subnet_id': vip.subnet_id,
                     'subnet': vip.subnet,
                     'protocol_port': vip.protocol_port,
                     'protocol': vip.protocol,
                     'session_persistence': vip.session_persistence['type'],
                     'cookie_name': vip.session_persistence['cookie_name'],
                     'connection_limit': vip.connection_limit,
                     'admin_state_up': vip.admin_state_up}

        res = self.client.post(
            reverse(self.ADDVIP_PATH, args=(pool.id,)), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.lbaas: ('pool_get', ),
                        api.neutron: ('subnet_get', )})
    def test_add_vip_post_with_error(self):
        vip = self.vips.first()

        subnet = self.subnets.first()
        pool = self.pools.first()

        api.lbaas.pool_get(IsA(http.HttpRequest), pool.id).AndReturn(pool)
        api.neutron.subnet_get(
            IsA(http.HttpRequest), subnet.id).AndReturn(subnet)

        self.mox.ReplayAll()

        form_data = {'name': vip.name,
                     'description': vip.description,
                     'pool_id': vip.pool_id,
                     'address': vip.address,
                     'subnet_id': vip.subnet_id,
                     'protocol_port': 65536,
                     'protocol': vip.protocol,
                     'session_persistence': vip.session_persistence['type'],
                     'cookie_name': vip.session_persistence['cookie_name'],
                     'connection_limit': -2,
                     'admin_state_up': vip.admin_state_up}

        res = self.client.post(
            reverse(self.ADDVIP_PATH, args=(pool.id,)), form_data)

        self.assertFormErrors(res, 2)

    @test.create_stubs({api.lbaas: ('pool_get', ),
                        api.neutron: ('subnet_get', )})
    def test_add_vip_get(self):
        subnet = self.subnets.first()
        pool = self.pools.first()

        api.lbaas.pool_get(IsA(http.HttpRequest), pool.id).AndReturn(pool)
        api.neutron.subnet_get(
            IsA(http.HttpRequest), subnet.id).AndReturn(subnet)

        self.mox.ReplayAll()

        res = self.client.get(reverse(self.ADDVIP_PATH, args=(pool.id,)))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddVip.name)

        expected_objs = ['<AddVipStep: addvipaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.lbaas: ('pool_health_monitor_create', )})
    def test_add_monitor_post(self):
        monitor = self.monitors.first()

        api.lbaas.pool_health_monitor_create(
            IsA(http.HttpRequest),
            type=monitor.type,
            delay=monitor.delay,
            timeout=monitor.timeout,
            max_retries=monitor.max_retries,
            http_method=monitor.http_method,
            url_path=monitor.url_path,
            expected_codes=monitor.expected_codes,
            admin_state_up=monitor.admin_state_up).AndReturn(
                lbaas.PoolMonitor(monitor))

        self.mox.ReplayAll()

        form_data = {'type': monitor.type,
                     'delay': monitor.delay,
                     'timeout': monitor.timeout,
                     'max_retries': monitor.max_retries,
                     'http_method': monitor.http_method,
                     'url_path': monitor.url_path,
                     'expected_codes': monitor.expected_codes,
                     'admin_state_up': monitor.admin_state_up}

        res = self.client.post(reverse(self.ADDMONITOR_PATH), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    def test_add_monitor_post_with_error(self):
        monitor = self.monitors.first()

        form_data = {'type': monitor.type,
                     'delay': 0,
                     'timeout': 0,
                     'max_retries': 11,
                     'http_method': monitor.http_method,
                     'url_path': monitor.url_path,
                     'expected_codes': monitor.expected_codes,
                     'admin_state_up': monitor.admin_state_up}

        res = self.client.post(reverse(self.ADDMONITOR_PATH), form_data)

        self.assertFormErrors(res, 3)

    def test_add_monitor_post_with_httpmethod_error(self):
        monitor = self.monitors.first()

        form_data = {'type': 'http',
                     'delay': monitor.delay,
                     'timeout': monitor.timeout,
                     'max_retries': monitor.max_retries,
                     'http_method': '',
                     'url_path': '',
                     'expected_codes': '',
                     'admin_state_up': monitor.admin_state_up}

        res = self.client.post(reverse(self.ADDMONITOR_PATH), form_data)

        self.assertFormErrors(res, 3)

    def test_add_monitor_get(self):
        res = self.client.get(reverse(self.ADDMONITOR_PATH))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddMonitor.name)

        expected_objs = ['<AddMonitorStep: addmonitoraction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.lbaas: ('pools_get', 'member_create'),
                        api.neutron: ('port_list',),
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

        api.nova.server_list(IsA(http.HttpRequest)).AndReturn(
            [[server1, server2], False])

        api.neutron.port_list(IsA(http.HttpRequest),
                              device_id=server1.id).AndReturn([port1, ])

        api.lbaas.member_create(
            IsA(http.HttpRequest),
            pool_id=member.pool_id,
            address=member.address,
            protocol_port=member.protocol_port,
            weight=member.weight,
            members=[server1.id],
            admin_state_up=member.admin_state_up).AndReturn(
                lbaas.Member(member))

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
    def test_add_member_post_with_error(self):
        member = self.members.first()

        server1 = self.AttributeDict({'id':
                                      '12381d38-c3eb-4fee-9763-12de3338042e',
                                      'name': 'vm1'})
        server2 = self.AttributeDict({'id':
                                      '12381d38-c3eb-4fee-9763-12de3338043e',
                                      'name': 'vm2'})

        api.lbaas.pools_get(IsA(http.HttpRequest)).AndReturn(self.pools.list())

        api.nova.server_list(IsA(http.HttpRequest)).AndReturn([[server1,
                                                                server2],
                                                                False])

        self.mox.ReplayAll()

        # try to create member with invalid protocol port and weight
        form_data = {'pool_id': member.pool_id,
                     'address': member.address,
                     'protocol_port': 65536,
                     'weight': -1,
                     'members': [server1.id],
                     'admin_state_up': member.admin_state_up}

        res = self.client.post(reverse(self.ADDMEMBER_PATH), form_data)

        self.assertFormErrors(res, 2)

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
            IsA(http.HttpRequest)).AndReturn([[server1, server2], False])

        self.mox.ReplayAll()

        res = self.client.get(reverse(self.ADDMEMBER_PATH))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddMember.name)

        expected_objs = ['<AddMemberStep: addmemberaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.lbaas: ('pool_get', 'pool_update')})
    def test_update_pool_post(self):
        pool = self.pools.first()

        api.lbaas.pool_get(IsA(http.HttpRequest), pool.id).AndReturn(pool)

        data = {'name': pool.name,
                'description': pool.description,
                'lb_method': pool.lb_method,
                'admin_state_up': pool.admin_state_up}

        api.lbaas.pool_update(IsA(http.HttpRequest), pool.id, pool=data)\
            .AndReturn(pool)

        self.mox.ReplayAll()

        form_data = data.copy()
        form_data.update({'pool_id': pool.id})

        res = self.client.post(
            reverse(self.UPDATEPOOL_PATH, args=(pool.id,)), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.lbaas: ('pool_get',)})
    def test_update_pool_get(self):
        pool = self.pools.first()

        api.lbaas.pool_get(IsA(http.HttpRequest), pool.id).AndReturn(pool)

        self.mox.ReplayAll()

        res = self.client.get(reverse(self.UPDATEPOOL_PATH, args=(pool.id,)))

        self.assertTemplateUsed(res, 'project/loadbalancers/updatepool.html')

    @test.create_stubs({api.lbaas: ('pools_get', 'vip_get',
                                    'vip_update')})
    def test_update_vip_post(self):
        vip = self.vips.first()

        api.lbaas.pools_get(IsA(http.HttpRequest)).AndReturn(self.pools.list())
        api.lbaas.vip_get(IsA(http.HttpRequest), vip.id).AndReturn(vip)

        data = {'name': vip.name,
                'description': vip.description,
                'pool_id': vip.pool_id,
                'session_persistence': {},
                'connection_limit': vip.connection_limit,
                'admin_state_up': vip.admin_state_up}

        api.lbaas.vip_update(IsA(http.HttpRequest), vip.id, vip=data)\
            .AndReturn(vip)

        self.mox.ReplayAll()

        form_data = data.copy()
        form_data.update({'vip_id': vip.id})

        res = self.client.post(
            reverse(self.UPDATEVIP_PATH, args=(vip.id,)), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.lbaas: ('vip_get', 'pools_get')})
    def test_update_vip_get(self):
        vip = self.vips.first()

        api.lbaas.pools_get(IsA(http.HttpRequest)).AndReturn(self.pools.list())
        api.lbaas.vip_get(IsA(http.HttpRequest), vip.id).AndReturn(vip)

        self.mox.ReplayAll()

        res = self.client.get(reverse(self.UPDATEVIP_PATH, args=(vip.id,)))

        self.assertTemplateUsed(res, 'project/loadbalancers/updatevip.html')

    @test.create_stubs({api.lbaas: ('pools_get', 'member_get',
                                    'member_update')})
    def test_update_member_post(self):
        member = self.members.first()

        api.lbaas.pools_get(IsA(http.HttpRequest)).AndReturn(self.pools.list())
        api.lbaas.member_get(IsA(http.HttpRequest), member.id)\
            .AndReturn(member)

        data = {'pool_id': member.pool_id,
                'weight': member.weight,
                'admin_state_up': member.admin_state_up}

        api.lbaas.member_update(IsA(http.HttpRequest), member.id, member=data)\
            .AndReturn(member)

        self.mox.ReplayAll()

        form_data = data.copy()
        form_data.update({'member_id': member.id})

        res = self.client.post(
            reverse(self.UPDATEMEMBER_PATH, args=(member.id,)), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.lbaas: ('member_get', 'pools_get')})
    def test_update_member_get(self):
        member = self.members.first()

        api.lbaas.pools_get(IsA(http.HttpRequest)).AndReturn(self.pools.list())
        api.lbaas.member_get(IsA(http.HttpRequest), member.id)\
            .AndReturn(member)

        self.mox.ReplayAll()

        res = self.client.get(
            reverse(self.UPDATEMEMBER_PATH, args=(member.id,)))

        self.assertTemplateUsed(res, 'project/loadbalancers/updatemember.html')

    @test.create_stubs({api.lbaas: ('pool_health_monitor_get',
                                    'pool_health_monitor_update')})
    def test_update_monitor_post(self):
        monitor = self.monitors.first()

        api.lbaas.pool_health_monitor_get(IsA(http.HttpRequest), monitor.id)\
            .AndReturn(monitor)

        data = {'delay': monitor.delay,
                'timeout': monitor.timeout,
                'max_retries': monitor.max_retries,
                'admin_state_up': monitor.admin_state_up}

        api.lbaas.pool_health_monitor_update(IsA(http.HttpRequest),
            monitor.id, health_monitor=data).AndReturn(monitor)

        self.mox.ReplayAll()

        form_data = data.copy()
        form_data.update({'monitor_id': monitor.id})

        res = self.client.post(
            reverse(self.UPDATEMONITOR_PATH, args=(monitor.id,)), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.lbaas: ('pool_health_monitor_get',)})
    def test_update_monitor_get(self):
        monitor = self.monitors.first()

        api.lbaas.pool_health_monitor_get(IsA(http.HttpRequest), monitor.id)\
            .AndReturn(monitor)

        self.mox.ReplayAll()

        res = self.client.get(
            reverse(self.UPDATEMONITOR_PATH, args=(monitor.id,)))

        self.assertTemplateUsed(
            res, 'project/loadbalancers/updatemonitor.html')

    @test.create_stubs({api.lbaas: ('pool_get', 'pool_health_monitors_get',
                                    'pool_monitor_association_create')})
    def test_add_pool_monitor_association_post(self):
        pool = self.pools.first()
        monitors = self.monitors.list()
        monitor = self.monitors.list()[1]

        api.lbaas.pool_get(IsA(http.HttpRequest), pool.id).AndReturn(pool)
        api.lbaas.pool_health_monitors_get(
            IsA(http.HttpRequest)).AndReturn(monitors)

        api.lbaas.pool_monitor_association_create(
            IsA(http.HttpRequest),
            monitor_id=monitor.id,
            pool_id=pool.id,
            pool_monitors=pool.health_monitors,
            pool_name=pool.name).AndReturn(None)

        self.mox.ReplayAll()

        form_data = {'monitor_id': monitor.id,
                     'pool_id': pool.id,
                     'pool_monitors': pool.health_monitors,
                     'pool_name': pool.name}

        res = self.client.post(
            reverse(self.ADDASSOC_PATH, args=(pool.id,)), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.lbaas: ('pool_get', 'pool_health_monitors_get')})
    def test_add_pool_monitor_association_get(self):
        pool = self.pools.first()
        monitors = self.monitors.list()

        api.lbaas.pool_get(IsA(http.HttpRequest), pool.id).AndReturn(pool)
        api.lbaas.pool_health_monitors_get(
            IsA(http.HttpRequest)).AndReturn(monitors)

        self.mox.ReplayAll()

        res = self.client.get(reverse(self.ADDASSOC_PATH, args=(pool.id,)))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.AddPMAssociation.name)

        expected_objs = ['<AddPMAssociationStep: addpmassociationaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.lbaas: ('pool_get',
                                    'pool_monitor_association_delete')})
    def test_delete_pool_monitor_association_post(self):
        pool = self.pools.first()
        monitor = self.monitors.first()

        api.lbaas.pool_get(IsA(http.HttpRequest), pool.id).AndReturn(pool)

        api.lbaas.pool_monitor_association_delete(
            IsA(http.HttpRequest),
            monitor_id=monitor.id,
            pool_id=pool.id,
            pool_monitors=pool.health_monitors,
            pool_name=pool.name).AndReturn(None)

        self.mox.ReplayAll()

        form_data = {'monitor_id': monitor.id,
                     'pool_id': pool.id,
                     'pool_monitors': pool.health_monitors,
                     'pool_name': pool.name}

        res = self.client.post(
            reverse(self.DELETEASSOC_PATH, args=(pool.id,)), form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, str(self.INDEX_URL))

    @test.create_stubs({api.lbaas: ('pool_get',)})
    def test_delete_pool_monitor_association_get(self):
        pool = self.pools.first()

        api.lbaas.pool_get(IsA(http.HttpRequest), pool.id).AndReturn(pool)

        self.mox.ReplayAll()

        res = self.client.get(
            reverse(self.DELETEASSOC_PATH, args=(pool.id,)))

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(workflow.name, workflows.DeletePMAssociation.name)

        expected_objs = [
            '<DeletePMAssociationStep: deletepmassociationaction>', ]
        self.assertQuerysetEqual(workflow.steps, expected_objs)
