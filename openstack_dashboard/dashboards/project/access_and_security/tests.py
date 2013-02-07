# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from copy import deepcopy

from django import http
from django.core.urlresolvers import reverse

from mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class AccessAndSecurityTests(test.TestCase):
    def setUp(self):
        super(AccessAndSecurityTests, self).setUp()

    def test_index(self):
        keypairs = self.keypairs.list()
        sec_groups = self.security_groups.list()
        floating_ips = self.floating_ips.list()
        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api.nova, 'security_group_list')
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api.nova, 'server_list')

        api.nova.server_list(IsA(http.HttpRequest),
                             all_tenants=True).AndReturn(self.servers.list())
        api.nova.keypair_list(IsA(http.HttpRequest)).AndReturn(keypairs)
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
            .AndReturn(floating_ips)
        api.nova.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(sec_groups)

        self.mox.ReplayAll()

        url = reverse('horizon:project:access_and_security:index')
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/access_and_security/index.html')
        self.assertItemsEqual(res.context['keypairs_table'].data, keypairs)
        self.assertItemsEqual(res.context['security_groups_table'].data,
                              sec_groups)
        self.assertItemsEqual(res.context['floating_ips_table'].data,
                              floating_ips)

    def test_association(self):
        servers = [api.nova.Server(s, self.request)
                   for s in self.servers.list()]
        # Add duplicate instance name to test instance name with [ID]
        # Change id and private IP
        server3 = api.nova.Server(self.servers.first(), self.request)
        server3.id = 101
        server3.addresses = deepcopy(server3.addresses)
        server3.addresses['private'][0]['addr'] = "10.0.0.5"
        servers.append(server3)

        targets = [api.nova.FloatingIpTarget(s) for s in servers]

        self.mox.StubOutWithMock(api.network, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api.network, 'floating_ip_target_list')
        api.network.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        api.network.floating_ip_target_list(IsA(http.HttpRequest)) \
                .AndReturn(targets)
        self.mox.ReplayAll()

        res = self.client.get(reverse("horizon:project:access_and_security:"
                                      "floating_ips:associate"))
        self.assertTemplateUsed(res,
                    'project/access_and_security/floating_ips/associate.html')

        self.assertContains(res,
                            '<option value="1">server_1 (1)</option>')
        self.assertContains(res,
                            '<option value="101">server_1 (101)</option>')
        self.assertContains(res, '<option value="2">server_2 (2)</option>')


class AccessAndSecurityQuantumProxyTests(AccessAndSecurityTests):
    def setUp(self):
        super(AccessAndSecurityQuantumProxyTests, self).setUp()
        self.floating_ips = self.floating_ips_uuid
