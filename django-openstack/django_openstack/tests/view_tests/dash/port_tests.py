from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django_openstack import api
from django_openstack.tests.view_tests import base
from mox import IgnoreArg, IsA
import quantum.client


class PortViewTests(base.BaseViewTests):
    def setUp(self):
        super(PortViewTests, self).setUp()

    def test_port_create(self):
        self.mox.StubOutWithMock(api, "quantum_create_port")
        api.quantum_create_port(IsA(http.HttpRequest), 'n1').AndReturn(True)

        formData = {'ports_num': 1,
                    'network': 'n1',
                    'method': 'CreatePort'}

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(str))

        res = self.client.post(reverse('dash_ports_create',
                               args=[self.request.user.tenant, "n1"]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_networks_detail',
                                          args=[self.request.user.tenant,
                                          "n1"]))

    def test_port_delete(self):
        self.mox.StubOutWithMock(api, "quantum_delete_port")
        api.quantum_delete_port(IsA(http.HttpRequest),
                                'n1', 'p1').AndReturn(True)

        formData = {'port': 'p1',
                    'network': 'n1',
                    'method': 'DeletePort'}

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(str))

        res = self.client.post(reverse('dash_networks_detail',
                               args=[self.request.user.tenant, "n1"]),
                               formData)

    def test_port_attach(self):
        self.mox.StubOutWithMock(api, "quantum_attach_port")
        api.quantum_attach_port(IsA(http.HttpRequest),
                                'n1', 'p1', dict).AndReturn(True)

        formData = {'port': 'p1',
                    'network': 'n1',
                    'vif_id': 'v1',
                    'method': 'AttachPort'}

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(str))

        res = self.client.post(reverse('dash_ports_attach',
                               args=[self.request.user.tenant, "n1", "p1"]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_networks_detail',
                                          args=[self.request.user.tenant,
                                          "n1"]))

    def test_port_detach(self):
        self.mox.StubOutWithMock(api, "quantum_detach_port")
        api.quantum_detach_port(IsA(http.HttpRequest),
                                'n1', 'p1').AndReturn(True)

        formData = {'port': 'p1',
                    'network': 'n1',
                    'method': 'DetachPort'}

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(str))

        res = self.client.post(reverse('dash_networks_detail',
                               args=[self.request.user.tenant, "n1"]),
                               formData)
