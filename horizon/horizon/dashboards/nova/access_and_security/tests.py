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
from mox import IsA
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import test


class AccessAndSecurityTests(test.BaseViewTests):
    def setUp(self):
        super(AccessAndSecurityTests, self).setUp()
        keypair = api.KeyPair(None)
        keypair.name = 'keyName'
        self.keypairs = (keypair,)

        server = api.Server(None, self.request)
        server.id = 1
        server.name = 'serverName'
        self.server = server
        self.servers = (server, )

        floating_ip = api.FloatingIp(None)
        floating_ip.id = 1
        floating_ip.fixed_ip = '10.0.0.4'
        floating_ip.instance_id = 1
        floating_ip.ip = '58.58.58.58'

        self.floating_ip = floating_ip
        self.floating_ips = (floating_ip,)

        security_group = api.SecurityGroup(None)
        security_group.id = '1'
        security_group.name = 'default'
        self.security_groups = (security_group,)

    def test_index(self):
        self.mox.StubOutWithMock(api, 'tenant_floating_ip_list')
        self.mox.StubOutWithMock(api, 'security_group_list')
        self.mox.StubOutWithMock(api.nova, 'keypair_list')

        api.nova.keypair_list(IsA(http.HttpRequest)).AndReturn(self.keypairs)
        api.tenant_floating_ip_list(IsA(http.HttpRequest)).\
                                    AndReturn(self.floating_ips)
        api.security_group_list(IsA(http.HttpRequest)).\
                                AndReturn(self.security_groups)

        self.mox.ReplayAll()

        res = self.client.get(
                             reverse('horizon:nova:access_and_security:index'))

        self.assertTemplateUsed(res, 'nova/access_and_security/index.html')
        self.assertItemsEqual(res.context['keypairs_table'].data,
                              self.keypairs)
        self.assertItemsEqual(res.context['security_groups_table'].data,
                              self.security_groups)
        self.assertItemsEqual(res.context['floating_ips_table'].data,
                              self.floating_ips)
