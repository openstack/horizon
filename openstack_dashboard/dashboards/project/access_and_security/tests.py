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

from copy import deepcopy  # noqa

from django.core.urlresolvers import reverse
from django import http
from mox3.mox import IsA  # noqa
import six

from horizon.workflows import views
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.access_and_security \
    import api_access
from openstack_dashboard.dashboards.project.access_and_security \
    .security_groups import tables
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas

INDEX_URL = reverse('horizon:project:access_and_security:index')


class AccessAndSecurityTests(test.TestCase):
    def setUp(self):
        super(AccessAndSecurityTests, self).setUp()

    @test.create_stubs({api.network: ('floating_ip_supported',
                                      'tenant_floating_ip_list',
                                      'security_group_list',),
                        api.nova: ('keypair_list',
                                   'server_list',),
                        api.base: ('is_service_enabled',),
                        quotas: ('tenant_quota_usages',)})
    def _test_index(self, ec2_enabled):
        keypairs = self.keypairs.list()
        sec_groups = self.security_groups.list()
        floating_ips = self.floating_ips.list()
        quota_data = self.quota_usages.first()
        quota_data['security_groups']['available'] = 10

        api.nova.server_list(
            IsA(http.HttpRequest)) \
            .AndReturn([self.servers.list(), False])
        api.nova.keypair_list(
            IsA(http.HttpRequest)) \
            .AndReturn(keypairs)
        api.network.floating_ip_supported(
            IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(
            IsA(http.HttpRequest)) \
            .AndReturn(floating_ips)
        api.network.security_group_list(
            IsA(http.HttpRequest)) \
            .AndReturn(sec_groups)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)).MultipleTimes() \
            .AndReturn(quota_data)

        api.base.is_service_enabled(
            IsA(http.HttpRequest),
            'network').MultipleTimes() \
            .AndReturn(True)
        api.base.is_service_enabled(
            IsA(http.HttpRequest),
            'ec2').MultipleTimes() \
            .AndReturn(ec2_enabled)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/access_and_security/index.html')
        self.assertItemsEqual(res.context['keypairs_table'].data, keypairs)
        self.assertItemsEqual(res.context['floating_ips_table'].data,
                              floating_ips)

        # Security groups
        sec_groups_from_ctx = res.context['security_groups_table'].data
        # Context data needs to contains all items from the test data.
        self.assertItemsEqual(sec_groups_from_ctx,
                              sec_groups)
        # Sec groups in context need to be sorted by their ``name`` attribute.
        # This assertion is somewhat weak since it's only meaningful as long as
        # the sec groups in the test data are *not* sorted by name (which is
        # the case as of the time of this addition).
        self.assertTrue(
            all([sec_groups_from_ctx[i].name <= sec_groups_from_ctx[i + 1].name
                 for i in range(len(sec_groups_from_ctx) - 1)]))

        if ec2_enabled:
            self.assertTrue(any(map(
                lambda x: isinstance(x, api_access.tables.DownloadEC2),
                res.context['endpoints_table'].get_table_actions()
            )))
        else:
            self.assertFalse(any(map(
                lambda x: isinstance(x, api_access.tables.DownloadEC2),
                res.context['endpoints_table'].get_table_actions()
            )))

    def test_index(self):
        self._test_index(ec2_enabled=True)

    def test_index_with_ec2_disabled(self):
        self._test_index(ec2_enabled=False)

    @test.create_stubs({api.network: ('floating_ip_target_list',
                                      'tenant_floating_ip_list',)})
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

        api.network.tenant_floating_ip_list(
            IsA(http.HttpRequest)) \
            .AndReturn(self.floating_ips.list())
        api.network.floating_ip_target_list(
            IsA(http.HttpRequest)) \
            .AndReturn(targets)

        self.mox.ReplayAll()

        res = self.client.get(reverse("horizon:project:access_and_security:"
                                      "floating_ips:associate"))

        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertContains(res, '<option value="1">server_1 (1)</option>')
        self.assertContains(res, '<option value="101">server_1 (101)</option>')
        self.assertContains(res, '<option value="2">server_2 (2)</option>')


class AccessAndSecurityNeutronProxyTests(AccessAndSecurityTests):
    def setUp(self):
        super(AccessAndSecurityNeutronProxyTests, self).setUp()
        self.floating_ips = self.floating_ips_uuid


class SecurityGroupTabTests(test.TestCase):
    def setUp(self):
        super(SecurityGroupTabTests, self).setUp()

    @test.create_stubs({api.network: ('floating_ip_supported',
                                      'tenant_floating_ip_list',
                                      'security_group_list',
                                      'floating_ip_pools_list',),
                        api.nova: ('keypair_list',
                                   'server_list',),
                        quotas: ('tenant_quota_usages',),
                        api.base: ('is_service_enabled',)})
    def _test_create_button_disabled_when_quota_exceeded(self,
                                                         network_enabled):
        keypairs = self.keypairs.list()
        floating_ips = self.floating_ips.list()
        floating_pools = self.pools.list()
        sec_groups = self.security_groups.list()
        quota_data = self.quota_usages.first()
        quota_data['security_groups']['available'] = 0

        api.network.floating_ip_supported(
            IsA(http.HttpRequest)) \
            .AndReturn(True)
        api.network.tenant_floating_ip_list(
            IsA(http.HttpRequest)) \
            .AndReturn(floating_ips)
        api.network.floating_ip_pools_list(
            IsA(http.HttpRequest)) \
            .AndReturn(floating_pools)
        api.network.security_group_list(
            IsA(http.HttpRequest)) \
            .AndReturn(sec_groups)
        api.nova.keypair_list(
            IsA(http.HttpRequest)) \
            .AndReturn(keypairs)
        api.nova.server_list(
            IsA(http.HttpRequest)) \
            .AndReturn([self.servers.list(), False])
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest)).MultipleTimes() \
            .AndReturn(quota_data)

        api.base.is_service_enabled(
            IsA(http.HttpRequest), 'network').MultipleTimes() \
            .AndReturn(network_enabled)
        api.base.is_service_enabled(
            IsA(http.HttpRequest), 'ec2').MultipleTimes() \
            .AndReturn(False)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL +
                              "?tab=access_security_tabs__security_groups_tab")

        security_groups = res.context['security_groups_table'].data
        self.assertItemsEqual(security_groups, self.security_groups.list())

        create_link = tables.CreateGroup()
        url = create_link.get_link_url()
        classes = (list(create_link.get_default_classes())
                   + list(create_link.classes))
        link_name = "%s (%s)" % (six.text_type(create_link.verbose_name),
                                 "Quota exceeded")
        expected_string = "<a href='%s' title='%s'  class='%s disabled' "\
            "id='security_groups__action_create'>" \
            "<span class='fa fa-plus'></span>%s</a>" \
            % (url, link_name, " ".join(classes), link_name)
        self.assertContains(res, expected_string, html=True,
                            msg_prefix="The create button is not disabled")

    def test_create_button_disabled_when_quota_exceeded_neutron_disabled(self):
        self._test_create_button_disabled_when_quota_exceeded(False)

    def test_create_button_disabled_when_quota_exceeded_neutron_enabled(self):
        self._test_create_button_disabled_when_quota_exceeded(True)
