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
        messages.success(IgnoreArg(), IsA(basestring))

        res = self.client.post(reverse('dash_ports_create',
                               args=[self.request.user.tenant_id, "n1"]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_networks_detail',
                                          args=[self.request.user.tenant_id,
                                          "n1"]))

    def test_port_delete(self):
        self.mox.StubOutWithMock(api, "quantum_delete_port")
        api.quantum_delete_port(IsA(http.HttpRequest),
                                'n1', 'p1').AndReturn(True)

        formData = {'port': 'p1',
                    'network': 'n1',
                    'method': 'DeletePort'}

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(basestring))

        res = self.client.post(reverse('dash_networks_detail',
                               args=[self.request.user.tenant_id, "n1"]),
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
        messages.success(IgnoreArg(), IsA(basestring))

        res = self.client.post(reverse('dash_ports_attach',
                               args=[self.request.user.tenant_id, "n1", "p1"]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_networks_detail',
                                          args=[self.request.user.tenant_id,
                                          "n1"]))

    def test_port_detach(self):
        self.mox.StubOutWithMock(api, "quantum_detach_port")
        api.quantum_detach_port(IsA(http.HttpRequest),
                                'n1', 'p1').AndReturn(True)

        formData = {'port': 'p1',
                    'network': 'n1',
                    'method': 'DetachPort'}

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(basestring))

        res = self.client.post(reverse('dash_networks_detail',
                               args=[self.request.user.tenant_id, "n1"]),
                               formData)
