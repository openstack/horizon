# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright (c) 2012 X.commerce, a business unit of eBay Inc.
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
from mox import IsA
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import test


INDEX_URL = reverse('horizon:nova:access_and_security:index')
NAMESPACE = "horizon:nova:access_and_security:floating_ips"


class FloatingIpViewTests(test.TestCase):
    def test_associate(self):
        floating_ip = self.floating_ips.first()
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_get')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.tenant_floating_ip_get(IsA(http.HttpRequest),
                                   floating_ip.id).AndReturn(floating_ip)
        self.mox.ReplayAll()

        url = reverse('%s:associate' % NAMESPACE, args=[floating_ip.id])
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                        'nova/access_and_security/floating_ips/associate.html')

    def test_associate_post(self):
        floating_ip = self.floating_ips.first()
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api, 'server_add_floating_ip')
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_get')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                                    .AndReturn(self.floating_ips.list())
        api.server_add_floating_ip(IsA(http.HttpRequest),
                                   server.id,
                                   floating_ip.id)
        api.tenant_floating_ip_get(IsA(http.HttpRequest),
                                   floating_ip.id).AndReturn(floating_ip)
        self.mox.ReplayAll()

        form_data = {'instance_id': server.id,
                     'floating_ip_id': floating_ip.id,
                     'floating_ip': floating_ip.ip,
                     'method': 'FloatingIpAssociate'}
        url = reverse('%s:associate' % NAMESPACE, args=[floating_ip.id])
        res = self.client.post(url, form_data)
        self.assertRedirects(res, INDEX_URL)

    def test_associate_post_with_exception(self):
        floating_ip = self.floating_ips.first()
        server = self.servers.first()
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api, 'server_add_floating_ip')
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_get')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                                    .AndReturn(self.floating_ips.list())
        api.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
                              .AndReturn(self.keypairs.list())
        exc = novaclient_exceptions.ClientException('ClientException')
        api.server_add_floating_ip(IsA(http.HttpRequest),
                                   server.id,
                                   floating_ip.id).AndRaise(exc)
        api.tenant_floating_ip_get(IsA(http.HttpRequest),
                                   floating_ip.id).AndReturn(floating_ip)
        self.mox.ReplayAll()

        url = reverse('%s:associate' % NAMESPACE, args=[floating_ip.id])
        res = self.client.post(url,
                {'instance_id': 1,
                 'floating_ip_id': floating_ip.id,
                 'floating_ip': floating_ip.ip,
                 'method': 'FloatingIpAssociate'})
        self.assertRaises(novaclient_exceptions.ClientException)
        self.assertRedirects(res, INDEX_URL)

    def test_disassociate_post(self):
        floating_ip = self.floating_ips.first()
        server = self.servers.first()
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_get')
        self.mox.StubOutWithMock(api, 'server_remove_floating_ip')

        api.nova.keypair_list(IsA(http.HttpRequest)) \
                              .AndReturn(self.keypairs.list())
        api.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        api.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                                    .AndReturn(self.floating_ips.list())
        api.server_remove_floating_ip(IsA(http.HttpRequest),
                                      server.id,
                                      floating_ip.id)
        self.mox.ReplayAll()

        action = "floating_ips__disassociate__%s" % floating_ip.id
        res = self.client.post(INDEX_URL, {"action": action})
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_disassociate_post_with_exception(self):
        floating_ip = self.floating_ips.first()
        server = self.servers.first()
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_get')
        self.mox.StubOutWithMock(api, 'server_remove_floating_ip')
        api.nova.keypair_list(IsA(http.HttpRequest)) \
                              .AndReturn(self.keypairs.list())
        api.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        api.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                                    .AndReturn(self.floating_ips.list())

        exc = novaclient_exceptions.ClientException('ClientException')
        api.server_remove_floating_ip(IsA(http.HttpRequest),
                                      server.id,
                                      floating_ip.id).AndRaise(exc)
        self.mox.ReplayAll()

        action = "floating_ips__disassociate__%s" % floating_ip.id
        res = self.client.post(INDEX_URL, {"action": action})
        self.assertRaises(novaclient_exceptions.ClientException)
        self.assertRedirectsNoFollow(res, INDEX_URL)
