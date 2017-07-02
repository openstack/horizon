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

import cgi

from mox3.mox import IsA
import six

import django
from django.conf import settings
from django.core.urlresolvers import reverse
from django import http

from horizon import exceptions
from horizon import forms

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.security_groups import tables
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


INDEX_URL = reverse('horizon:project:security_groups:index')
SG_CREATE_URL = reverse('horizon:project:security_groups:create')

SG_VIEW_PATH = 'horizon:project:security_groups:%s'
SG_DETAIL_VIEW = SG_VIEW_PATH % 'detail'
SG_UPDATE_VIEW = SG_VIEW_PATH % 'update'
SG_ADD_RULE_VIEW = SG_VIEW_PATH % 'add_rule'

SG_TEMPLATE_PATH = 'project/security_groups/%s'
SG_DETAIL_TEMPLATE = SG_TEMPLATE_PATH % 'detail.html'
SG_CREATE_TEMPLATE = SG_TEMPLATE_PATH % 'create.html'
SG_UPDATE_TEMPLATE = SG_TEMPLATE_PATH % '_update.html'


def strip_absolute_base(uri):
    return uri.split(settings.TESTSERVER, 1)[-1]


class SecurityGroupsViewTests(test.TestCase):
    secgroup_backend = 'neutron'

    def setUp(self):
        super(SecurityGroupsViewTests, self).setUp()

        sec_group = self.security_groups.first()
        self.detail_url = reverse(SG_DETAIL_VIEW, args=[sec_group.id])
        self.edit_url = reverse(SG_ADD_RULE_VIEW, args=[sec_group.id])
        self.update_url = reverse(SG_UPDATE_VIEW, args=[sec_group.id])

    @test.create_stubs({api.neutron: ('security_group_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_index(self):
        sec_groups = self.security_groups.list()
        quota_data = self.quota_usages.first()
        quota_data['security_groups']['available'] = 10

        api.neutron.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn(sec_groups)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest),
            targets=('security_groups', )).MultipleTimes() \
            .AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')

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

    @test.create_stubs({api.neutron: ('security_group_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_create_button_attributes(self):
        sec_groups = self.security_groups.list()
        quota_data = self.quota_usages.first()
        quota_data['security_groups']['available'] = 10

        api.neutron.security_group_list(
            IsA(http.HttpRequest)) \
            .AndReturn(sec_groups)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest),
            targets=('security_groups', )).MultipleTimes() \
            .AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        security_groups = res.context['security_groups_table'].data
        self.assertItemsEqual(security_groups, self.security_groups.list())

        create_action = self.getAndAssertTableAction(res, 'security_groups',
                                                     'create')

        self.assertEqual('Create Security Group',
                         six.text_type(create_action.verbose_name))
        self.assertIsNone(create_action.policy_rules)
        self.assertEqual(set(['ajax-modal']), set(create_action.classes))

        url = 'horizon:project:security_groups:create'
        self.assertEqual(url, create_action.url)

    @test.create_stubs({api.neutron: ('security_group_list',),
                        quotas: ('tenant_quota_usages',)})
    def _test_create_button_disabled_when_quota_exceeded(self,
                                                         network_enabled):
        sec_groups = self.security_groups.list()
        quota_data = self.quota_usages.first()
        quota_data['security_groups']['available'] = 0

        api.neutron.security_group_list(
            IsA(http.HttpRequest)) \
            .AndReturn(sec_groups)
        quotas.tenant_quota_usages(
            IsA(http.HttpRequest),
            targets=('security_groups', )).MultipleTimes() \
            .AndReturn(quota_data)

        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        security_groups = res.context['security_groups_table'].data
        self.assertItemsEqual(security_groups, self.security_groups.list())

        create_action = self.getAndAssertTableAction(res, 'security_groups',
                                                     'create')
        self.assertIn('disabled', create_action.classes,
                      'The create button should be disabled')

    def test_create_button_disabled_when_quota_exceeded_neutron_disabled(self):
        self._test_create_button_disabled_when_quota_exceeded(False)

    def test_create_button_disabled_when_quota_exceeded_neutron_enabled(self):
        self._test_create_button_disabled_when_quota_exceeded(True)

    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list')})
    def _add_security_group_rule_fixture(self, **kwargs):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.first()

        api.neutron.security_group_rule_create(
            IsA(http.HttpRequest),
            kwargs.get('sec_group', sec_group.id),
            kwargs.get('ingress', 'ingress'),
            kwargs.get('ethertype', 'IPv4'),
            kwargs.get('ip_protocol', rule.ip_protocol),
            kwargs.get('from_port', int(rule.from_port)),
            kwargs.get('to_port', int(rule.to_port)),
            kwargs.get('cidr', rule.ip_range['cidr']),
            kwargs.get('security_group', u'%s' % sec_group.id)).AndReturn(rule)
        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        return sec_group, rule

    @test.create_stubs({api.neutron: ('security_group_get',)})
    def test_update_security_groups_get(self):
        sec_group = self.security_groups.first()
        api.neutron.security_group_get(IsA(http.HttpRequest),
                                       sec_group.id).AndReturn(sec_group)
        self.mox.ReplayAll()
        res = self.client.get(self.update_url)
        self.assertTemplateUsed(res, SG_UPDATE_TEMPLATE)
        self.assertEqual(res.context['security_group'].name,
                         sec_group.name)

    @test.create_stubs({api.neutron: ('security_group_update',
                                      'security_group_get')})
    def test_update_security_groups_post(self):
        """Ensure that we can change a group name.

        The name must not be restricted to alphanumeric characters.
        bug #1233501 Security group names cannot contain at characters
        bug #1224576 Security group names cannot contain spaces
        """
        sec_group = self.security_groups.first()
        sec_group.name = "@new name"
        api.neutron.security_group_update(
            IsA(http.HttpRequest),
            str(sec_group.id),
            sec_group.name,
            sec_group.description).AndReturn(sec_group)
        api.neutron.security_group_get(
            IsA(http.HttpRequest), sec_group.id).AndReturn(sec_group)
        self.mox.ReplayAll()
        form_data = {'method': 'UpdateGroup',
                     'id': sec_group.id,
                     'name': sec_group.name,
                     'description': sec_group.description}
        res = self.client.post(self.update_url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_create_security_groups_get(self):
        res = self.client.get(SG_CREATE_URL)
        self.assertTemplateUsed(res, SG_CREATE_TEMPLATE)

    def test_create_security_groups_post(self):
        sec_group = self.security_groups.first()
        self._create_security_group(sec_group)

    def test_create_security_groups_special_chars(self):
        """Ensure non-alphanumeric characters can be used as a group name.

        bug #1233501 Security group names cannot contain at characters
        bug #1224576 Security group names cannot contain spaces
        """
        sec_group = self.security_groups.first()
        sec_group.name = '@group name-\xe3\x82\xb3'
        self._create_security_group(sec_group)

    @test.create_stubs({api.neutron: ('security_group_create',)})
    def _create_security_group(self, sec_group):
        api.neutron.security_group_create(
            IsA(http.HttpRequest),
            sec_group.name,
            sec_group.description).AndReturn(sec_group)
        self.mox.ReplayAll()

        form_data = {'method': 'CreateGroup',
                     'name': sec_group.name,
                     'description': sec_group.description}
        res = self.client.post(SG_CREATE_URL, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('security_group_create',)})
    def test_create_security_groups_post_exception(self):
        sec_group = self.security_groups.first()
        api.neutron.security_group_create(
            IsA(http.HttpRequest),
            sec_group.name,
            sec_group.description).AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        formData = {'method': 'CreateGroup',
                    'name': sec_group.name,
                    'description': sec_group.description}
        res = self.client.post(SG_CREATE_URL, formData)
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.neutron: ('security_group_get',)})
    def test_detail_get(self):
        sec_group = self.security_groups.first()

        api.neutron.security_group_get(IsA(http.HttpRequest),
                                       sec_group.id).AndReturn(sec_group)
        self.mox.ReplayAll()
        res = self.client.get(self.detail_url)
        self.assertTemplateUsed(res, SG_DETAIL_TEMPLATE)

    @test.create_stubs({api.neutron: ('security_group_get',)})
    def test_detail_get_exception(self):
        sec_group = self.security_groups.first()

        api.neutron.security_group_get(
            IsA(http.HttpRequest),
            sec_group.id).AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        res = self.client.get(self.detail_url)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_detail_add_rule_cidr(self):
        sec_group, rule = self._add_security_group_rule_fixture(
            security_group=None)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'port': rule.from_port,
                    'rule_menu': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    def test_detail_add_rule_cidr_with_invalid_unused_fields(self):
        sec_group, rule = self._add_security_group_rule_fixture(
            security_group=None)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'port': rule.from_port,
                    'to_port': 'INVALID',
                    'from_port': 'INVALID',
                    'icmp_code': 'INVALID',
                    'icmp_type': 'INVALID',
                    'security_group': 'INVALID',
                    'ip_protocol': 'INVALID',
                    'rule_menu': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.detail_url)

    def test_detail_add_rule_securitygroup_with_invalid_unused_fields(self):
        sec_group, rule = self._add_security_group_rule_fixture(
            cidr=None, ethertype='')
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'port': rule.from_port,
                    'to_port': 'INVALID',
                    'from_port': 'INVALID',
                    'icmp_code': 'INVALID',
                    'icmp_type': 'INVALID',
                    'security_group': sec_group.id,
                    'ip_protocol': 'INVALID',
                    'rule_menu': rule.ip_protocol,
                    'cidr': 'INVALID',
                    'remote': 'sg'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.detail_url)

    def test_detail_add_rule_icmp_with_invalid_unused_fields(self):
        sec_group, rule = self._add_security_group_rule_fixture(
            ip_protocol='icmp', security_group=None)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'port': 'INVALID',
                    'to_port': 'INVALID',
                    'from_port': 'INVALID',
                    'icmp_code': rule.to_port,
                    'icmp_type': rule.from_port,
                    'security_group': sec_group.id,
                    'ip_protocol': 'INVALID',
                    'rule_menu': 'icmp',
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.detail_url)

    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list')})
    def test_detail_add_rule_cidr_with_template(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.first()

        api.neutron.security_group_rule_create(IsA(http.HttpRequest),
                                               sec_group.id,
                                               'ingress', 'IPv4',
                                               rule.ip_protocol,
                                               int(rule.from_port),
                                               int(rule.to_port),
                                               rule.ip_range['cidr'],
                                               None).AndReturn(rule)
        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'rule_menu': 'http',
                    'port_or_range': 'port',
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    def _get_source_group_rule(self):
        for rule in self.security_group_rules.list():
            if rule.group:
                return rule
        raise Exception("No matches found.")

    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list',)})
    def test_detail_add_rule_self_as_source_group(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self._get_source_group_rule()

        api.neutron.security_group_rule_create(
            IsA(http.HttpRequest),
            sec_group.id,
            'ingress',
            # ethertype is empty for source_group of Nova Security Group
            '',
            rule.ip_protocol,
            int(rule.from_port),
            int(rule.to_port),
            None,
            u'%s' % sec_group.id).AndReturn(rule)
        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'port': rule.from_port,
                    'rule_menu': rule.ip_protocol,
                    'cidr': '0.0.0.0/0',
                    'security_group': sec_group.id,
                    'remote': 'sg'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list',)})
    def test_detail_add_rule_self_as_source_group_with_template(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self._get_source_group_rule()

        api.neutron.security_group_rule_create(
            IsA(http.HttpRequest),
            sec_group.id,
            'ingress',
            # ethertype is empty for source_group of Nova Security Group
            '',
            rule.ip_protocol,
            int(rule.from_port),
            int(rule.to_port),
            None,
            u'%s' % sec_group.id).AndReturn(rule)
        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'rule_menu': 'http',
                    'port_or_range': 'port',
                    'cidr': '0.0.0.0/0',
                    'security_group': sec_group.id,
                    'remote': 'sg'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    @test.create_stubs({api.neutron: ('security_group_list',)})
    def test_detail_invalid_port(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.first()

        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        if django.VERSION >= (1, 9):
            api.neutron.security_group_list(
                IsA(http.HttpRequest)).AndReturn(sec_group_list)

        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'port': None,
                    'rule_menu': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, "The specified port is invalid")

    @test.create_stubs({api.neutron: ('security_group_list',)})
    def test_detail_invalid_port_range(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.first()

        for i in range(3):
            api.neutron.security_group_list(
                IsA(http.HttpRequest)).AndReturn(sec_group_list)
        if django.VERSION >= (1, 9):
            for i in range(3):
                api.neutron.security_group_list(
                    IsA(http.HttpRequest)).AndReturn(sec_group_list)

        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'range',
                    'from_port': rule.from_port,
                    'to_port': int(rule.from_port) - 1,
                    'rule_menu': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, "greater than or equal to")

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'range',
                    'from_port': None,
                    'to_port': rule.to_port,
                    'rule_menu': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, cgi.escape('"from" port number is invalid',
                                            quote=True))

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'range',
                    'from_port': rule.from_port,
                    'to_port': None,
                    'rule_menu': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, cgi.escape('"to" port number is invalid',
                                            quote=True))

    @test.create_stubs({api.neutron: ('security_group_get',
                                      'security_group_list')})
    def test_detail_invalid_icmp_rule(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        icmp_rule = self.security_group_rules.list()[1]

        # Call POST 5 times (*2 if Django >= 1.9)
        call_post = 5
        if django.VERSION >= (1, 9):
            call_post *= 2

        for i in range(call_post):
            api.neutron.security_group_list(
                IsA(http.HttpRequest)).AndReturn(sec_group_list)

        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'icmp_type': 256,
                    'icmp_code': icmp_rule.to_port,
                    'rule_menu': icmp_rule.ip_protocol,
                    'cidr': icmp_rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, "The ICMP type not in range (-1, 255)")

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'icmp_type': icmp_rule.from_port,
                    'icmp_code': 256,
                    'rule_menu': icmp_rule.ip_protocol,
                    'cidr': icmp_rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, "The ICMP code not in range (-1, 255)")

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'icmp_type': icmp_rule.from_port,
                    'icmp_code': None,
                    'rule_menu': icmp_rule.ip_protocol,
                    'cidr': icmp_rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, "The ICMP code not in range (-1, 255)")

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'icmp_type': None,
                    'icmp_code': icmp_rule.to_port,
                    'rule_menu': icmp_rule.ip_protocol,
                    'cidr': icmp_rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, "The ICMP type not in range (-1, 255)")

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'icmp_type': -1,
                    'icmp_code': icmp_rule.to_port,
                    'rule_menu': icmp_rule.ip_protocol,
                    'cidr': icmp_rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(
            res, "ICMP code is provided but ICMP type is missing.")

    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list')})
    def test_detail_add_rule_exception(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.first()

        api.neutron.security_group_rule_create(
            IsA(http.HttpRequest),
            sec_group.id, 'ingress', 'IPv4',
            rule.ip_protocol,
            int(rule.from_port),
            int(rule.to_port),
            rule.ip_range['cidr'],
            None).AndRaise(self.exceptions.nova)
        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'port': rule.from_port,
                    'rule_menu': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list')})
    def test_detail_add_rule_duplicated(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.first()

        api.neutron.security_group_rule_create(
            IsA(http.HttpRequest),
            sec_group.id, 'ingress', 'IPv4',
            rule.ip_protocol,
            int(rule.from_port),
            int(rule.to_port),
            rule.ip_range['cidr'],
            None).AndRaise(exceptions.Conflict)
        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'port': rule.from_port,
                    'rule_menu': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, self.detail_url)

    @test.create_stubs({api.neutron: ('security_group_rule_delete',)})
    def test_detail_delete_rule(self):
        sec_group = self.security_groups.first()
        rule = self.security_group_rules.first()

        api.neutron.security_group_rule_delete(IsA(http.HttpRequest), rule.id)
        self.mox.ReplayAll()

        form_data = {"action": "rules__delete__%s" % rule.id}
        req = self.factory.post(self.edit_url, form_data)
        kwargs = {'security_group_id': sec_group.id}
        table = tables.RulesTable(req, sec_group.rules, **kwargs)
        handled = table.maybe_handle()
        self.assertEqual(strip_absolute_base(handled['location']),
                         self.detail_url)

    @test.create_stubs({api.neutron: ('security_group_rule_delete',)})
    def test_detail_delete_rule_exception(self):
        sec_group = self.security_groups.first()
        rule = self.security_group_rules.first()

        api.neutron.security_group_rule_delete(
            IsA(http.HttpRequest),
            rule.id).AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        form_data = {"action": "rules__delete__%s" % rule.id}
        req = self.factory.post(self.edit_url, form_data)
        kwargs = {'security_group_id': sec_group.id}
        table = tables.RulesTable(
            req, self.security_group_rules.list(), **kwargs)
        handled = table.maybe_handle()
        self.assertEqual(strip_absolute_base(handled['location']),
                         self.detail_url)

    @test.create_stubs({api.neutron: ('security_group_delete',)})
    def test_delete_group(self):
        sec_group = self.security_groups.get(name="other_group")

        api.neutron.security_group_delete(IsA(http.HttpRequest), sec_group.id)
        self.mox.ReplayAll()

        form_data = {"action": "security_groups__delete__%s" % sec_group.id}
        req = self.factory.post(INDEX_URL, form_data)
        table = tables.SecurityGroupsTable(req, self.security_groups.list())
        handled = table.maybe_handle()
        self.assertEqual(strip_absolute_base(handled['location']),
                         INDEX_URL)

    @test.create_stubs({api.neutron: ('security_group_delete',)})
    def test_delete_group_exception(self):
        sec_group = self.security_groups.get(name="other_group")

        api.neutron.security_group_delete(
            IsA(http.HttpRequest),
            sec_group.id).AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        form_data = {"action": "security_groups__delete__%s" % sec_group.id}
        req = self.factory.post(INDEX_URL, form_data)
        table = tables.SecurityGroupsTable(req, self.security_groups.list())
        handled = table.maybe_handle()

        self.assertEqual(strip_absolute_base(handled['location']),
                         INDEX_URL)

    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list')})
    def test_detail_add_rule_custom_protocol(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.first()

        api.neutron.security_group_rule_create(IsA(http.HttpRequest),
                                               sec_group.id, 'ingress', 'IPv6',
                                               37, None, None, 'fe80::/48',
                                               None).AndReturn(rule)
        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'rule_menu': 'custom',
                    'direction': 'ingress',
                    'port_or_range': 'port',
                    'ip_protocol': 37,
                    'cidr': 'fe80::/48',
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list')})
    def test_detail_add_rule_egress(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.first()

        api.neutron.security_group_rule_create(IsA(http.HttpRequest),
                                               sec_group.id, 'egress', 'IPv4',
                                               'udp', 80, 80, '10.1.1.0/24',
                                               None).AndReturn(rule)
        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'direction': 'egress',
                    'rule_menu': 'udp',
                    'port_or_range': 'port',
                    'port': 80,
                    'cidr': '10.1.1.0/24',
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list')})
    def test_detail_add_rule_egress_with_all_tcp(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.list()[3]

        api.neutron.security_group_rule_create(IsA(http.HttpRequest),
                                               sec_group.id, 'egress', 'IPv4',
                                               rule.ip_protocol,
                                               int(rule.from_port),
                                               int(rule.to_port),
                                               rule.ip_range['cidr'],
                                               None).AndReturn(rule)
        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'direction': 'egress',
                    'port_or_range': 'range',
                    'rule_menu': 'all_tcp',
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list')})
    def test_detail_add_rule_source_group_with_direction_ethertype(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self._get_source_group_rule()

        api.neutron.security_group_rule_create(
            IsA(http.HttpRequest),
            sec_group.id,
            'egress',
            # ethertype is empty for source_group of Nova Security Group
            'IPv6',
            rule.ip_protocol,
            int(rule.from_port),
            int(rule.to_port),
            None,
            u'%s' % sec_group.id).AndReturn(rule)
        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'direction': 'egress',
                    'port_or_range': 'port',
                    'port': rule.from_port,
                    'rule_menu': rule.ip_protocol,
                    'cidr': '0.0.0.0/0',
                    'security_group': sec_group.id,
                    'remote': 'sg',
                    'ethertype': 'IPv6'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'enable_ipv6': False})
    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list')})
    def test_add_rule_ethertype_with_ipv6_disabled(self):

        self.mox.ReplayAll()

        res = self.client.get(self.edit_url)

        self.assertIsInstance(
            res.context['form']['ethertype'].field.widget,
            forms.TextInput
        )
        self.assertIn(
            'readonly',
            res.context['form']['ethertype'].field.widget.attrs
        )
        self.assertEqual(
            res.context['form']['ethertype'].field.initial,
            'IPv4'
        )

    @test.update_settings(
        OPENSTACK_NEUTRON_NETWORK={'enable_ipv6': False})
    @test.create_stubs({api.neutron: ('security_group_list',)})
    def test_add_rule_cidr_with_ipv6_disabled(self):
        sec_group = self.security_groups.first()

        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'rule_menu': 'custom',
                    'direction': 'ingress',
                    'port_or_range': 'port',
                    'ip_protocol': 37,
                    'cidr': 'fe80::/48',
                    'etherype': 'IPv4',
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertFormError(res, 'form', 'cidr',
                             'Invalid version for IP address')

    @test.create_stubs({api.neutron: ('security_group_list',)})
    def test_detail_add_rule_invalid_port(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.first()

        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        if django.VERSION >= (1, 9):
            api.neutron.security_group_list(
                IsA(http.HttpRequest)).AndReturn(sec_group_list)

        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'port': -1,
                    'rule_menu': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, "Not a valid port number")

    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list')})
    def test_detail_add_rule_ingress_tcp_without_port(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.list()[3]

        api.neutron.security_group_rule_create(IsA(http.HttpRequest),
                                               sec_group.id, 'ingress', 'IPv4',
                                               'tcp',
                                               None,
                                               None,
                                               rule.ip_range['cidr'],
                                               None).AndReturn(rule)
        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'id': sec_group.id,
                    'direction': 'ingress',
                    'port_or_range': 'all',
                    'rule_menu': 'tcp',
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    @test.create_stubs({api.neutron: ('security_group_rule_create',
                                      'security_group_list')})
    def test_detail_add_rule_custom_without_protocol(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.list()[3]

        api.neutron.security_group_rule_create(IsA(http.HttpRequest),
                                               sec_group.id, 'ingress', 'IPv4',
                                               None,
                                               None,
                                               None,
                                               rule.ip_range['cidr'],
                                               None).AndReturn(rule)
        api.neutron.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'id': sec_group.id,
                    'direction': 'ingress',
                    'port_or_range': 'port',
                    'rule_menu': 'custom',
                    'ip_protocol': -1,
                    'cidr': rule.ip_range['cidr'],
                    'remote': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)
