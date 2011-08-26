from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django_openstack import api
from django_openstack.tests.view_tests import base
from mox import IgnoreArg, IsA


class NetworkViewTests(base.BaseViewTests):
    def setUp(self):
        super(NetworkViewTests, self).setUp()
        self.network = {}
        self.network['networks'] = []
        self.network['networks'].append({id : 'n1'})
        self.network_details = {'network' : {'name' : 'test_network'}}
        self.ports = {}
        self.ports['ports'] = []
        self.ports['ports'].append({'id' : 'p1'})
        self.port_attachment = {}
        self.port_attachment['attachment'] = 'vif1'
        
    def test_network_index(self):
        q_api = api.quantum_api(self.request)
        
        self.mox.StubOutWithMock(q_api, 'list_networks')
        q_api.list_networks()(
                IsA(http.HttpRequest)).AndReturn([self.network])

        self.mox.StubOutWithMock(q_api, 'show_network_details')
        q_api.show_network_details("n1")(
                IsA(http.HttpRequest)).AndReturn([self.network_details])

        self.mox.StubOutWithMock(q_api, 'list_ports')
        q_api.list_ports("n1")(
                IsA(http.HttpRequest)).AndReturn([self.ports])

        self.mox.StubOutWithMock(q_api, 'show_port_attachment')
        q_api.show_port_attachment("p1")(
                IsA(http.HttpRequest)).AndReturn([self.port_attachment])
        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_networks', args=['tenant']))

        self.assertTemplateUsed(res, 'dash_networks.html')
        self.assertIn('networks', res.context)
        networks = res.context['networks']

        self.assertEqual(len(networks), 1)
        self.assertEqual(networks[0].name, 'test')
        self.assertEqual(networks[0].id, 'n1')
        self.assertEqual(networks[0].id, 'n1')
        self.assertEqual(networks[0].total, 1)
        self.assertEqual(networks[0].used, 1)
        self.assertEqual(networks[0].available, 0)
        
        self.mox.VerifyAll()
        
    def test_network_create(self):
        q_api = api.quantum_api(self.request)
        formData = {'name': 'Test',
                    'method': 'CreateNetwork'}

        self.mox.StubOutWithMock(q_api, 'create_network')
        q_api.create_network(
                IsA(http.HttpRequest), 'CreateNetwork')

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(str))

        res = self.client.post(reverse('dash_network_create',
                               args=[self.request.user.tenant]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_networks',
                                          args=[self.request.user.tenant]))

    def test_network_delete(self):
        q_api = api.quantum_api(self.request)
        formData = {'id': 'n1',
                    'method': 'DeleteNetwork'}

        self.mox.StubOutWithMock(q_api, 'delete_network')
        q_api.delete_network(
                IsA(http.HttpRequest), 'DeleteNetwork')

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(str))

        res = self.client.post(reverse('dash_networks',
                               args=[self.request.user.tenant]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_networks',
                                          args=[self.request.user.tenant]))
        
    def test_network_rename(self):
        q_api = api.quantum_api(self.request)
        formData = {'new_name' : 'Test1',
                    'method': 'DeleteNetwork'}

        self.mox.StubOutWithMock(q_api, 'update_network')
        q_api.update_network("n1")(
                IsA(http.HttpRequest), 'DeleteNetwork')

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(str))

        res = self.client.post(reverse('dash_network_rename',
                               args=[self.request.user.tenant, "n1"]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_networks',
                                          args=[self.request.user.tenant]))
