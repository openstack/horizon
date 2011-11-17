# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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
from django.contrib import messages
from django.core.urlresolvers import reverse
from mox import IgnoreArg, IsA
import quantum.client

from horizon import api
from horizon import test


class NetworkViewTests(test.BaseViewTests):
    def setUp(self):
        super(NetworkViewTests, self).setUp()
        self.network = {}
        self.network['networks'] = []
        self.network['networks'].append({'id': 'n1'})
        self.network_details = {'network': {'id': '1', 'name': 'test_network'}}
        self.ports = {}
        self.ports['ports'] = []
        self.ports['ports'].append({'id': 'p1'})
        self.port_details = {
            'port': {
                'id': 'p1',
                'state': 'DOWN'}}
        self.port_attachment = {
            'attachment': {
                'id': 'vif1'}}
        self.vifs = [{'id': 'vif1'}]

    def test_network_index(self):
        self.mox.StubOutWithMock(api, 'quantum_list_networks')
        api.quantum_list_networks(IsA(http.HttpRequest)).\
                                            AndReturn(self.network)

        self.mox.StubOutWithMock(api, 'quantum_network_details')
        api.quantum_network_details(IsA(http.HttpRequest),
                                    'n1').AndReturn(self.network_details)

        self.mox.StubOutWithMock(api, 'quantum_list_ports')
        api.quantum_list_ports(IsA(http.HttpRequest),
                               'n1').AndReturn(self.ports)

        self.mox.StubOutWithMock(api, 'quantum_port_attachment')
        api.quantum_port_attachment(IsA(http.HttpRequest),
                                    'n1', 'p1').AndReturn(self.port_attachment)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:networks:index'))

        self.assertTemplateUsed(res, 'nova/networks/index.html')
        self.assertIn('networks', res.context)
        networks = res.context['networks']

        self.assertEqual(len(networks), 1)
        self.assertEqual(networks[0]['name'], 'test_network')
        self.assertEqual(networks[0]['id'], 'n1')
        self.assertEqual(networks[0]['total'], 1)
        self.assertEqual(networks[0]['used'], 1)
        self.assertEqual(networks[0]['available'], 0)

    def test_network_create(self):
        self.mox.StubOutWithMock(api, "quantum_create_network")
        api.quantum_create_network(IsA(http.HttpRequest), dict).AndReturn(True)

        self.mox.ReplayAll()

        formData = {'name': 'Test',
                    'method': 'CreateNetwork'}

        res = self.client.post(reverse('horizon:nova:networks:create'),
                               formData)

        self.assertRedirectsNoFollow(res,
                                     reverse('horizon:nova:networks:index'))

    def test_network_delete(self):
        self.mox.StubOutWithMock(api, "quantum_delete_network")
        api.quantum_delete_network(IsA(http.HttpRequest), 'n1').AndReturn(True)

        self.mox.StubOutWithMock(api, 'quantum_list_networks')
        api.quantum_list_networks(IsA(http.HttpRequest)).\
                                            AndReturn(self.network)

        self.mox.StubOutWithMock(api, 'quantum_network_details')
        api.quantum_network_details(IsA(http.HttpRequest),
                                    'n1').AndReturn(self.network_details)

        self.mox.StubOutWithMock(api, 'quantum_list_ports')
        api.quantum_list_ports(IsA(http.HttpRequest),
                               'n1').AndReturn(self.ports)

        self.mox.StubOutWithMock(api, 'quantum_port_attachment')
        api.quantum_port_attachment(IsA(http.HttpRequest),
                                    'n1', 'p1').AndReturn(self.port_attachment)

        self.mox.ReplayAll()

        formData = {'network': 'n1',
                    'method': 'DeleteNetwork'}

        res = self.client.post(reverse('horizon:nova:networks:index'),
                               formData)

    def test_network_rename(self):
        self.mox.StubOutWithMock(api, 'quantum_network_details')
        api.quantum_network_details(IsA(http.HttpRequest),
                                    'n1').AndReturn(self.network_details)

        self.mox.StubOutWithMock(api, 'quantum_update_network')
        api.quantum_update_network(IsA(http.HttpRequest), 'n1',
                                   {'network': {'name': "Test1"}})

        self.mox.ReplayAll()

        formData = {'network': 'n1',
                    'new_name': 'Test1',
                    'method': 'RenameNetwork'}

        res = self.client.post(reverse('horizon:nova:networks:rename',
                                       args=["n1"]),
                               formData)

        self.assertRedirectsNoFollow(res,
                                     reverse('horizon:nova:networks:index'))

    def test_network_details(self):
        self.mox.StubOutWithMock(api, 'quantum_network_details')
        api.quantum_network_details(IsA(http.HttpRequest),
                                    'n1').AndReturn(self.network_details)

        self.mox.StubOutWithMock(api, 'quantum_list_ports')
        api.quantum_list_ports(IsA(http.HttpRequest),
                               'n1').AndReturn(self.ports)

        self.mox.StubOutWithMock(api, 'quantum_port_attachment')
        api.quantum_port_attachment(IsA(http.HttpRequest),
                                    'n1', 'p1').AndReturn(self.port_attachment)

        self.mox.StubOutWithMock(api, 'quantum_port_details')
        api.quantum_port_details(IsA(http.HttpRequest),
                                 'n1', 'p1').AndReturn(self.port_details)

        self.mox.StubOutWithMock(api, 'get_vif_ids')
        api.get_vif_ids(IsA(http.HttpRequest)).AndReturn(self.vifs)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:networks:detail',
                                      args=['n1']))

        self.assertTemplateUsed(res, 'nova/networks/detail.html')
        self.assertIn('network', res.context)

        network = res.context['network']

        self.assertEqual(network['name'], 'test_network')
        self.assertEqual(network['id'], 'n1')


class PortViewTests(test.BaseViewTests):
    def setUp(self):
        super(PortViewTests, self).setUp()

    def test_port_create(self):
        self.mox.StubOutWithMock(api, "quantum_create_port")
        api.quantum_create_port(IsA(http.HttpRequest), 'n1').AndReturn(True)

        formData = {'ports_num': 1,
                    'network': 'n1',
                    'method': 'CreatePort'}

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:networks:port_create',
                                       args=["n1"]),
                               formData)

        self.assertRedirectsNoFollow(res,
                                     reverse('horizon:nova:networks:detail',
                                             args=["n1"]))

    def test_port_delete(self):
        self.mox.StubOutWithMock(api, "quantum_delete_port")
        api.quantum_delete_port(IsA(http.HttpRequest),
                                'n1', 'p1').AndReturn(True)

        formData = {'port': 'p1',
                    'network': 'n1',
                    'method': 'DeletePort'}

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:networks:detail',
                                       args=["n1"]),
                               formData)

    def test_port_attach(self):
        self.mox.StubOutWithMock(api, "quantum_attach_port")
        api.quantum_attach_port(IsA(http.HttpRequest),
                                'n1', 'p1', dict).AndReturn(True)
        self.mox.StubOutWithMock(api, "get_vif_ids")
        api.get_vif_ids(IsA(http.HttpRequest)).AndReturn([{
                'id': 'v1',
                'instance_name': 'instance1',
                'available': True}])

        formData = {'port': 'p1',
                    'network': 'n1',
                    'vif_id': 'v1',
                    'method': 'AttachPort'}

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:networks:port_attach',
                                       args=["n1", "p1"]),
                               formData)

        self.assertRedirectsNoFollow(res,
                                     reverse('horizon:nova:networks:detail',
                                             args=["n1"]))

    def test_port_detach(self):
        self.mox.StubOutWithMock(api, "quantum_detach_port")
        api.quantum_detach_port(IsA(http.HttpRequest),
                                'n1', 'p1').AndReturn(True)

        formData = {'port': 'p1',
                    'network': 'n1',
                    'method': 'DetachPort'}

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:networks:detail',
                                             args=["n1"]),
                               formData)
