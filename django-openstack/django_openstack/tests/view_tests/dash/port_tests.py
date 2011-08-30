from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django_openstack import api
from django_openstack.tests.view_tests import base
from mox import IgnoreArg, IsA


class PortViewTests(base.BaseViewTests):
    def setUp(self):
        super(PortViewTests, self).setUp()

    def test_port_create(self):
        q_api = api.quantum_api(self.request)
        formData = {'ports_num' : 1,
                    'network' : 'n1',
                    'method': 'CreatePort'}

        self.mox.StubOutWithMock(q_api, 'create_port')
        q_api.create_port(self.request.user.tenant, "n1")(
                IsA(http.HttpRequest), 'CreatePort')

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(str))

        res = self.client.post(reverse('dash_ports_create',
                               args=[self.request.user.tenant, "n1"]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_networks_detail',
                                          args=[self.request.user.tenant, "n1"]))

    def test_port_delete(self):
        q_api = api.quantum_api(self.request)
        formData = {'port' : 'p1',
                    'network' : 'n1',
                    'method': 'DeletePort'}

        self.mox.StubOutWithMock(q_api, 'delete_port')
        q_api.delete_port(self.request.user.tenant, "n1", "p1")(
                IsA(http.HttpRequest), 'DeletePort')

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(str))

        res = self.client.post(reverse('dash_networks_detail',
                               args=[self.request.user.tenant, "n1"]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_networks_detail',
                                          args=[self.request.user.tenant, "n1"]))

    def test_port_attach(self):
        q_api = api.quantum_api(self.request)
        formData = {'port' : 'p1',
                    'network' : 'n1',
                    'vif_id' : 'v1',
                    'method': 'AttachPort'}

        self.mox.StubOutWithMock(q_api, 'attach_resource')
        q_api.attach_resource(self.request.user.tenant, "n1", "p1")(
                IsA(http.HttpRequest), 'AttachPort')

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(str))

        res = self.client.post(reverse('dash_ports_attach',
                               args=[self.request.user.tenant, "n1", "p1"]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_networks_detail',
                                          args=[self.request.user.tenant, "n1"]))

    def test_port_detach(self):
        q_api = api.quantum_api(self.request)
        formData = {'port' : 'p1',
                    'network' : 'n1',
                    'method': 'DetachPort'}

        self.mox.StubOutWithMock(q_api, 'detach_resource')
        q_api.detach_resource(self.request.user.tenant, "n1", "p1")(
                IsA(http.HttpRequest), 'DetachPort')

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(str))

        res = self.client.post(reverse('dash_networks_detail',
                               args=[self.request.user.tenant, "n1"]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_networks_detail',
                                          args=[self.request.user.tenant, "n1"]))
