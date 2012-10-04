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

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:access_and_security:index')
NAMESPACE = "horizon:project:access_and_security:floating_ips"


class FloatingIpViewTests(test.TestCase):
    def test_associate(self):
        self.mox.StubOutWithMock(api.nova, 'server_list')
        self.mox.StubOutWithMock(api.nova, 'tenant_floating_ip_list')
        api.nova.server_list(IsA(http.HttpRequest)) \
                .AndReturn(self.servers.list())
        api.nova.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        self.mox.ReplayAll()

        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                    'project/access_and_security/floating_ips/associate.html')
        workflow = res.context['workflow']
        choices = dict(workflow.steps[0].action.fields['ip_id'].choices)
        # Verify that our "associated" floating IP isn't in the choices list.
        self.assertTrue(self.floating_ips.get(id=1) not in choices)

    def test_associate_post(self):
        floating_ip = self.floating_ips.get(id=2)
        server = self.servers.first()
        self.mox.StubOutWithMock(api.nova, 'server_add_floating_ip')
        self.mox.StubOutWithMock(api.nova, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api.nova, 'server_list')

        api.nova.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        api.nova.server_list(IsA(http.HttpRequest)) \
                .AndReturn(self.servers.list())
        api.nova.server_add_floating_ip(IsA(http.HttpRequest),
                                        server.id,
                                        floating_ip.id)
        self.mox.ReplayAll()

        form_data = {'instance_id': server.id,
                     'ip_id': floating_ip.id}
        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_associate_post_with_redirect(self):
        floating_ip = self.floating_ips.get(id=2)
        server = self.servers.first()
        self.mox.StubOutWithMock(api.nova, 'server_add_floating_ip')
        self.mox.StubOutWithMock(api.nova, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api.nova, 'server_list')

        api.nova.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        api.nova.server_list(IsA(http.HttpRequest)) \
                .AndReturn(self.servers.list())
        api.nova.server_add_floating_ip(IsA(http.HttpRequest),
                                        server.id,
                                        floating_ip.id)
        self.mox.ReplayAll()

        form_data = {'instance_id': server.id,
                     'ip_id': floating_ip.id}
        url = reverse('%s:associate' % NAMESPACE)
        next = reverse("horizon:project:instances:index")
        res = self.client.post("%s?next=%s" % (url, next), form_data)
        self.assertRedirectsNoFollow(res, next)

    def test_associate_post_with_exception(self):
        floating_ip = self.floating_ips.get(id=2)
        server = self.servers.first()
        self.mox.StubOutWithMock(api.nova, 'server_add_floating_ip')
        self.mox.StubOutWithMock(api.nova, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api.nova, 'server_list')

        api.nova.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                .AndReturn(self.floating_ips.list())
        api.nova.server_list(IsA(http.HttpRequest)) \
                .AndReturn(self.servers.list())
        api.nova.server_add_floating_ip(IsA(http.HttpRequest),
                                        server.id,
                                        floating_ip.id) \
                .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        form_data = {'instance_id': server.id,
                     'ip_id': floating_ip.id}
        url = reverse('%s:associate' % NAMESPACE)
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_disassociate_post(self):
        floating_ip = self.floating_ips.first()
        server = self.servers.first()
        self.mox.StubOutWithMock(api.nova, 'keypair_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_get')
        self.mox.StubOutWithMock(api, 'server_remove_floating_ip')
        self.mox.StubOutWithMock(api.nova, 'server_list')

        api.nova.server_list(IsA(http.HttpRequest),
                             all_tenants=True).AndReturn(self.servers.list())
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
        self.mox.StubOutWithMock(api.nova, 'server_list')

        api.nova.server_list(IsA(http.HttpRequest),
                             all_tenants=True).AndReturn(self.servers.list())
        api.nova.keypair_list(IsA(http.HttpRequest)) \
                              .AndReturn(self.keypairs.list())
        api.security_group_list(IsA(http.HttpRequest)) \
                                .AndReturn(self.security_groups.list())
        api.tenant_floating_ip_list(IsA(http.HttpRequest)) \
                                    .AndReturn(self.floating_ips.list())

        api.server_remove_floating_ip(IsA(http.HttpRequest),
                                      server.id,
                                      floating_ip.id) \
                                .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        action = "floating_ips__disassociate__%s" % floating_ip.id
        res = self.client.post(INDEX_URL, {"action": action})
        self.assertRedirectsNoFollow(res, INDEX_URL)
