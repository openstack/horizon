# Copyright 2012 NEC Corporation
# Copyright 2015 Cisco Systems, Inc.
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

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

DETAIL_URL = 'horizon:admin:networks:ports:detail'

NETWORKS_INDEX_URL = reverse('horizon:admin:networks:index')
NETWORKS_DETAIL_URL = 'horizon:admin:networks:detail'


class NetworkPortTests(test.BaseAdminViewTests):

    @test.create_stubs({api.neutron: ('network_get',
                                      'port_get',
                                      'is_extension_supported',)})
    def test_port_detail(self):
        self._test_port_detail()

    @test.create_stubs({api.neutron: ('network_get',
                                      'port_get',
                                      'is_extension_supported',)})
    def test_port_detail_with_mac_learning(self):
        self._test_port_detail(mac_learning=True)

    def _test_port_detail(self, mac_learning=False):
        port = self.ports.first()
        network_id = self.networks.first().id
        api.neutron.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(self.ports.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .MultipleTimes().AndReturn(mac_learning)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'allowed-address-pairs') \
            .MultipleTimes().AndReturn(False)
        api.neutron.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        res = self.client.get(reverse(DETAIL_URL, args=[port.id]))

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['port'].id, port.id)

    @test.create_stubs({api.neutron: ('port_get',)})
    def test_port_detail_exception(self):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest), port.id)\
            .AndRaise(self.exceptions.neutron)

        self.mox.ReplayAll()

        res = self.client.get(reverse(DETAIL_URL, args=[port.id]))

        redir_url = NETWORKS_INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',)})
    def test_port_create_get(self):
        self._test_port_create_get()

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',)})
    def test_port_create_get_with_mac_learning(self):
        self._test_port_create_get(mac_learning=True)

    def _test_port_create_get(self, mac_learning=False, binding=False):
        network = self.networks.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:addport',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/ports/create.html')

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'port_create',)})
    def test_port_create_post(self):
        self._test_port_create_post()

    @test.create_stubs({api.neutron: ('network_get',
                                      'is_extension_supported',
                                      'port_create',)})
    def test_port_create_post_with_mac_learning(self):
        self._test_port_create_post(mac_learning=True, binding=False)

    def _test_port_create_post(self, mac_learning=False, binding=False):
        network = self.networks.first()
        port = self.ports.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = \
                port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        api.neutron.port_create(IsA(http.HttpRequest),
                                tenant_id=network.tenant_id,
                                network_id=network.id,
                                name=port.name,
                                admin_state_up=port.admin_state_up,
                                device_id=port.device_id,
                                device_owner=port.device_owner,
                                binding__host_id=port.binding__host_id,
                                **extension_kwargs)\
            .AndReturn(port)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        url = reverse('horizon:admin:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('network_get',
                                      'port_create',
                                      'is_extension_supported',)})
    def test_port_create_post_exception(self):
        self._test_port_create_post_exception()

    @test.create_stubs({api.neutron: ('network_get',
                                      'port_create',
                                      'is_extension_supported',)})
    def test_port_create_post_exception_with_mac_learning(self):
        self._test_port_create_post_exception(mac_learning=True)

    def _test_port_create_post_exception(self, mac_learning=False,
                                         binding=False):
        network = self.networks.first()
        port = self.ports.first()
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        api.neutron.port_create(IsA(http.HttpRequest),
                                tenant_id=network.tenant_id,
                                network_id=network.id,
                                name=port.name,
                                admin_state_up=port.admin_state_up,
                                device_id=port.device_id,
                                device_owner=port.device_owner,
                                binding__host_id=port.binding__host_id,
                                **extension_kwargs)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'network_name': network.name,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'mac_state': True,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_learning_enabled'] = True
        url = reverse('horizon:admin:networks:addport',
                      args=[port.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',)})
    def test_port_update_get(self):
        self._test_port_update_get()

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',)})
    def test_port_update_get_with_mac_learning(self):
        self._test_port_update_get(mac_learning=True)

    def _test_port_update_get(self, mac_learning=False, binding=False):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest),
                             port.id)\
            .AndReturn(port)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/networks/ports/update.html')

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_update_post(self):
        self._test_port_update_post()

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_update_post_with_mac_learning(self):
        self._test_port_update_post(mac_learning=True)

    def _test_port_update_post(self, mac_learning=False, binding=False):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(port)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        api.neutron.port_update(IsA(http.HttpRequest), port.id,
                                name=port.name,
                                admin_state_up=port.admin_state_up,
                                device_id=port.device_id,
                                device_owner=port.device_owner,
                                binding__host_id=port.binding__host_id,
                                **extension_kwargs)\
            .AndReturn(port)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'port_id': port.id,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id}

        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        url = reverse('horizon:admin:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, form_data)

        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_update_post_exception(self):
        self._test_port_update_post_exception()

    @test.create_stubs({api.neutron: ('port_get',
                                      'is_extension_supported',
                                      'port_update')})
    def test_port_update_post_exception_with_mac_learning(self):
        self._test_port_update_post_exception(mac_learning=True, binding=False)

    def _test_port_update_post_exception(self, mac_learning=False,
                                         binding=False):
        port = self.ports.first()
        api.neutron.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(port)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'binding')\
            .AndReturn(binding)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        extension_kwargs = {}
        if binding:
            extension_kwargs['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            extension_kwargs['mac_learning_enabled'] = True
        api.neutron.port_update(IsA(http.HttpRequest), port.id,
                                name=port.name,
                                admin_state_up=port.admin_state_up,
                                device_id=port.device_id,
                                device_owner=port.device_owner,
                                binding__host_id=port.binding__host_id,
                                **extension_kwargs)\
            .AndRaise(self.exceptions.neutron)
        self.mox.ReplayAll()

        form_data = {'network_id': port.network_id,
                     'port_id': port.id,
                     'name': port.name,
                     'admin_state': port.admin_state_up,
                     'device_id': port.device_id,
                     'device_owner': port.device_owner,
                     'binding__host_id': port.binding__host_id}
        if binding:
            form_data['binding__vnic_type'] = port.binding__vnic_type
        if mac_learning:
            form_data['mac_state'] = True
        url = reverse('horizon:admin:networks:editport',
                      args=[port.network_id, port.id])
        res = self.client.post(url, form_data)

        redir_url = reverse(NETWORKS_DETAIL_URL, args=[port.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.neutron: ('port_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_port_delete(self):
        self._test_port_delete()

    @test.create_stubs({api.neutron: ('port_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_port_delete_with_mac_learning(self):
        self._test_port_delete(mac_learning=True)

    def _test_port_delete(self, mac_learning=False):
        port = self.ports.first()
        network_id = port.network_id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.port_delete(IsA(http.HttpRequest), port.id)
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'dhcp_agent_scheduler')\
            .AndReturn(True)
        self.mox.ReplayAll()

        form_data = {'action': 'ports__delete__%s' % port.id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.neutron: ('port_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks',)})
    def test_port_delete_exception(self):
        self._test_port_delete_exception()

    @test.create_stubs({api.neutron: ('port_delete',
                                      'subnet_list',
                                      'port_list',
                                      'is_extension_supported',
                                      'list_dhcp_agent_hosting_networks')})
    def test_port_delete_exception_with_mac_learning(self):
        self._test_port_delete_exception(mac_learning=True)

    def _test_port_delete_exception(self, mac_learning=False):
        port = self.ports.first()
        network_id = port.network_id
        api.neutron.list_dhcp_agent_hosting_networks(IsA(http.HttpRequest),
                                                     network_id).\
            AndReturn(self.agents.list())
        api.neutron.port_delete(IsA(http.HttpRequest), port.id)\
            .AndRaise(self.exceptions.neutron)
        api.neutron.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.neutron.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'mac-learning')\
            .AndReturn(mac_learning)
        api.neutron.is_extension_supported(IsA(http.HttpRequest),
                                           'dhcp_agent_scheduler')\
            .AndReturn(True)
        self.mox.ReplayAll()

        form_data = {'action': 'ports__delete__%s' % port.id}
        url = reverse(NETWORKS_DETAIL_URL, args=[network_id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, url)
