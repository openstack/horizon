# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 NEC Corporation
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
from django.core.urlresolvers import reverse
from django.utils.html import escape

from mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from .workflows import CreateNetwork


INDEX_URL = reverse('horizon:project:networks:index')


class NetworkTests(test.TestCase):
    @test.create_stubs({api.quantum: ('network_list',)})
    def test_index(self):
        api.quantum.network_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            shared=False).AndReturn(self.networks.list())
        api.quantum.network_list(
            IsA(http.HttpRequest),
            shared=True).AndReturn([])

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/networks/index.html')
        networks = res.context['networks_table'].data
        self.assertItemsEqual(networks, self.networks.list())

    @test.create_stubs({api.quantum: ('network_list',)})
    def test_index_network_list_exception(self):
        api.quantum.network_list(
            IsA(http.HttpRequest),
            tenant_id=self.tenant.id,
            shared=False).AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/networks/index.html')
        self.assertEqual(len(res.context['networks_table'].data), 0)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_list',
                                      'port_list',)})
    def test_network_detail(self):
        network_id = self.networks.first().id
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_list',
                                      'port_list',)})
    def test_network_detail_network_exception(self):
        network_id = self.networks.first().id
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:detail', args=[network_id])
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_list',
                                      'port_list',)})
    def test_network_detail_subnet_exception(self):
        network_id = self.networks.first().id
        api.quantum.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndRaise(self.exceptions.quantum)
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id).\
            AndReturn([self.ports.first()])
        # Called from SubnetTable
        api.quantum.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertEqual(len(subnets), 0)
        self.assertItemsEqual(ports, [self.ports.first()])

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_list',
                                      'port_list',)})
    def test_network_detail_port_exception(self):
        network_id = self.networks.first().id
        api.quantum.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id).\
            AndReturn([self.subnets.first()])
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id).\
            AndRaise(self.exceptions.quantum)
        # Called from SubnetTable
        api.quantum.network_get(IsA(http.HttpRequest), network_id).\
            AndReturn(self.networks.first())

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:detail',
                                      args=[network_id]))

        self.assertTemplateUsed(res, 'project/networks/detail.html')
        subnets = res.context['subnets_table'].data
        ports = res.context['ports_table'].data
        self.assertItemsEqual(subnets, [self.subnets.first()])
        self.assertEqual(len(ports), 0)

    def test_network_create_get(self):
        # no api methods are called.
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:create')
        res = self.client.get(url)

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, 'project/networks/create.html')
        self.assertEqual(workflow.name, CreateNetwork.name)
        expected_objs = ['<CreateNetworkInfo: createnetworkinfoaction>',
                         '<CreateSubnetInfo: createsubnetinfoaction>']
        self.assertQuerysetEqual(workflow.steps, expected_objs)

    @test.create_stubs({api.quantum: ('network_create',)})
    def test_network_create_post(self):
        network = self.networks.first()
        api.quantum.network_create(IsA(http.HttpRequest), name=network.name)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'with_subnet': False,
                     'subnet_name': '',
                     'cidr': '',
                     'ip_version': 4,
                     'gateway_ip': ''}
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_create',
                                      'subnet_create',)})
    def test_network_create_post_with_subnet(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_create(IsA(http.HttpRequest), name=network.name)\
            .AndReturn(network)
        api.quantum.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'with_subnet': True,
                     'subnet_name': subnet.name,
                     'cidr': subnet.cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_create',)})
    def test_network_create_post_network_exception(self):
        network = self.networks.first()
        api.quantum.network_create(IsA(http.HttpRequest), name=network.name)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'with_subnet': False,
                     'subnet_name': '',
                     'cidr': '',
                     'ip_version': 4,
                     'gateway_ip': ''}
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_create',)})
    def test_network_create_post_with_subnet_network_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_create(IsA(http.HttpRequest), name=network.name)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'with_subnet': True,
                     'subnet_name': subnet.name,
                     'cidr': subnet.cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_create',
                                      'subnet_create',)})
    def test_network_create_post_with_subnet_subnet_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_create(IsA(http.HttpRequest), name=network.name)\
            .AndReturn(network)
        api.quantum.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'with_subnet': True,
                     'subnet_name': subnet.name,
                     'cidr': subnet.cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_network_create_post_with_subnet_nocidr(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        self.mox.ReplayAll()

        form_data = {'net_name': network.name,
                     'with_subnet': True,
                     'subnet_name': subnet.name,
                     'cidr': '',
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertContains(res, escape('Specify "Network Address" or '
                                        'clear "Create Subnet" checkbox.'))

    def test_network_create_post_with_subnet_cidr_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        self.mox.ReplayAll()

        # dummy IPv6 address
        cidr = '2001:0DB8:0:CD30:123:4567:89AB:CDEF/60'
        form_data = {'net_name': network.name,
                     'with_subnet': True,
                     'subnet_name': subnet.name,
                     'cidr': cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        expected_msg = 'Network Address and IP version are inconsistent.'
        self.assertContains(res, expected_msg)

    def test_network_create_post_with_subnet_gw_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = {'net_name': network.name,
                     'with_subnet': True,
                     'subnet_name': subnet.name,
                     'cidr': subnet.cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': gateway_ip}
        url = reverse('horizon:project:networks:create')
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_network_update_get(self):
        network = self.networks.first()
        api.quantum.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/networks/update.html')

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_network_update_get_exception(self):
        network = self.networks.first()
        api.quantum.network_get(IsA(http.HttpRequest), network.id)\
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.get(url)

        redir_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_modify',
                                      'network_get',)})
    def test_network_update_post(self):
        network = self.networks.first()
        api.quantum.network_modify(IsA(http.HttpRequest), network.id,
                                   name=network.name)\
            .AndReturn(network)
        api.quantum.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        formData = {'network_id': network.id,
                    'name': network.name,
                    'tenant_id': network.tenant_id}
        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_modify',
                                      'network_get',)})
    def test_network_update_post_exception(self):
        network = self.networks.first()
        api.quantum.network_modify(IsA(http.HttpRequest), network.id,
                                   name=network.name)\
            .AndRaise(self.exceptions.quantum)
        api.quantum.network_get(IsA(http.HttpRequest), network.id)\
            .AndReturn(network)
        self.mox.ReplayAll()

        form_data = {'network_id': network.id,
                     'name': network.name,
                     'tenant_id': network.tenant_id}
        url = reverse('horizon:project:networks:update', args=[network.id])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_list',
                                      'subnet_list',
                                      'network_delete')})
    def test_delete_network_no_subnet(self):
        network = self.networks.first()
        api.quantum.network_list(IsA(http.HttpRequest),
                                 tenant_id=network.tenant_id,
                                 shared=False)\
            .AndReturn([network])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 shared=True)\
            .AndReturn([])
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network.id)\
            .AndReturn([])
        api.quantum.network_delete(IsA(http.HttpRequest), network.id)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_list',
                                      'subnet_list',
                                      'network_delete',
                                      'subnet_delete')})
    def test_delete_network_with_subnet(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_list(IsA(http.HttpRequest),
                                 tenant_id=network.tenant_id,
                                 shared=False)\
            .AndReturn([network])
        api.quantum.network_list(IsA(http.HttpRequest), shared=True)\
            .AndReturn([])
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network.id)\
            .AndReturn([subnet])
        api.quantum.subnet_delete(IsA(http.HttpRequest), subnet.id)
        api.quantum.network_delete(IsA(http.HttpRequest), network.id)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_list',
                                      'subnet_list',
                                      'network_delete',
                                      'subnet_delete')})
    def test_delete_network_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_list(IsA(http.HttpRequest),
                                 tenant_id=network.tenant_id,
                                 shared=False)\
            .AndReturn([network])
        api.quantum.network_list(IsA(http.HttpRequest),
                                 shared=True)\
            .AndReturn([])
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network.id)\
            .AndReturn([subnet])
        api.quantum.subnet_delete(IsA(http.HttpRequest), subnet.id)
        api.quantum.network_delete(IsA(http.HttpRequest), network.id)\
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        form_data = {'action': 'networks__delete__%s' % network.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('subnet_get',)})
    def test_subnet_detail(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(self.subnets.first())

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:subnets:detail',
                      args=[subnet.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/networks/subnets/detail.html')
        self.assertEqual(res.context['subnet'].id, subnet.id)

    @test.create_stubs({api.quantum: ('subnet_get',)})
    def test_subnet_detail_exception(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:subnets:detail',
                      args=[subnet.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_get(self):
        network = self.networks.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        url = reverse('horizon:project:networks:addsubnet',
                      args=[network.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/networks/subnets/create.html')

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  network_name=network.name,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        form_data = {'network_id': subnet.network_id,
                     'network_name': network.name,
                     'name': subnet.name,
                     'cidr': subnet.cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_network_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = {'network_id': subnet.network_id,
                     'network_name': network.name,
                     'name': subnet.name,
                     'cidr': subnet.cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.quantum: ('network_get',
                                      'subnet_create',)})
    def test_subnet_create_post_subnet_exception(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        api.quantum.subnet_create(IsA(http.HttpRequest),
                                  network_id=network.id,
                                  network_name=network.name,
                                  name=subnet.name,
                                  cidr=subnet.cidr,
                                  ip_version=subnet.ip_version,
                                  gateway_ip=subnet.gateway_ip)\
            .AndRaise(self.exceptions.quantum)
        self.mox.ReplayAll()

        form_data = {'network_id': subnet.network_id,
                     'network_name': network.name,
                     'name': subnet.name,
                     'cidr': subnet.cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_cidr_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        # dummy IPv6 address
        cidr = '2001:0DB8:0:CD30:123:4567:89AB:CDEF/60'
        form_data = {'network_id': subnet.network_id,
                     'network_name': network.name,
                     'name': subnet.name,
                     'cidr': cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        expected_msg = 'Network Address and IP version are inconsistent.'
        self.assertContains(res, expected_msg)

    @test.create_stubs({api.quantum: ('network_get',)})
    def test_subnet_create_post_gw_inconsistent(self):
        network = self.networks.first()
        subnet = self.subnets.first()
        api.quantum.network_get(IsA(http.HttpRequest),
                                network.id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        form_data = {'network_id': subnet.network_id,
                     'network_name': network.name,
                     'name': subnet.name,
                     'cidr': subnet.cidr,
                     'ip_version': subnet.ip_version,
                     'gateway_ip': gateway_ip}
        url = reverse('horizon:project:networks:addsubnet',
                      args=[subnet.network_id])
        res = self.client.post(url, form_data)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        api.quantum.subnet_modify(IsA(http.HttpRequest), subnet.id,
                                  name=subnet.name,
                                  gateway_ip=subnet.gateway_ip)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        formData = {'network_id': subnet.network_id,
                    'subnet_id': subnet.id,
                    'name': subnet.name,
                    'cidr': subnet.cidr,
                    'ip_version': subnet.ip_version,
                    'gateway_ip': subnet.gateway_ip}
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, formData)

        redir_url = reverse('horizon:project:networks:detail',
                            args=[subnet.network_id])
        self.assertRedirectsNoFollow(res, redir_url)

    @test.create_stubs({api.quantum: ('subnet_modify',
                                      'subnet_get',)})
    def test_subnet_update_post_gw_inconsistent(self):
        subnet = self.subnets.first()
        api.quantum.subnet_get(IsA(http.HttpRequest), subnet.id)\
            .AndReturn(subnet)
        self.mox.ReplayAll()

        # dummy IPv6 address
        gateway_ip = '2001:0DB8:0:CD30:123:4567:89AB:CDEF'
        formData = {'network_id': subnet.network_id,
                    'subnet_id': subnet.id,
                    'name': subnet.name,
                    'cidr': subnet.cidr,
                    'ip_version': subnet.ip_version,
                    'gateway_ip': gateway_ip}
        url = reverse('horizon:project:networks:editsubnet',
                      args=[subnet.network_id, subnet.id])
        res = self.client.post(url, formData)

        self.assertContains(res, 'Gateway IP and IP version are inconsistent.')

    @test.create_stubs({api.quantum: ('subnet_delete',
                                      'subnet_list',
                                      'network_get',
                                      'port_list',)})
    def test_subnet_delete(self):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        api.quantum.subnet_delete(IsA(http.HttpRequest), subnet.id)
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        # Called from SubnetTable
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        formData = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse('horizon:project:networks:detail',
                      args=[network_id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.quantum: ('subnet_delete',
                                      'subnet_list',
                                      'network_get',
                                      'port_list',)})
    def test_subnet_delete_excceeption(self):
        subnet = self.subnets.first()
        network_id = subnet.network_id
        api.quantum.subnet_delete(IsA(http.HttpRequest), subnet.id)\
            .AndRaise(self.exceptions.quantum)
        api.quantum.subnet_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.subnets.first()])
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        api.quantum.port_list(IsA(http.HttpRequest), network_id=network_id)\
            .AndReturn([self.ports.first()])
        # Called from SubnetTable
        api.quantum.network_get(IsA(http.HttpRequest), network_id)\
            .AndReturn(self.networks.first())
        self.mox.ReplayAll()

        formData = {'action': 'subnets__delete__%s' % subnet.id}
        url = reverse('horizon:project:networks:detail',
                      args=[network_id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.quantum: ('port_get',)})
    def test_port_detail(self):
        port = self.ports.first()
        api.quantum.port_get(IsA(http.HttpRequest), port.id)\
            .AndReturn(self.ports.first())

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:ports:detail',
                                      args=[port.id]))

        self.assertTemplateUsed(res, 'project/networks/ports/detail.html')
        self.assertEqual(res.context['port'].id, port.id)

    @test.create_stubs({api.quantum: ('port_get',)})
    def test_port_detail_exception(self):
        port = self.ports.first()
        api.quantum.port_get(IsA(http.HttpRequest), port.id)\
            .AndRaise(self.exceptions.quantum)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:networks:ports:detail',
                                      args=[port.id]))

        self.assertRedirectsNoFollow(res, INDEX_URL)
