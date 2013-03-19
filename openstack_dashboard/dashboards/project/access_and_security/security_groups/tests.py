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

from django import http
from django.conf import settings
from django.core.urlresolvers import reverse

from mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from .tables import SecurityGroupsTable, RulesTable


INDEX_URL = reverse('horizon:project:access_and_security:index')
SG_CREATE_URL = reverse('horizon:project:access_and_security:'
                        'security_groups:create')


def strip_absolute_base(uri):
    return uri.split(settings.TESTSERVER, 1)[-1]


class SecurityGroupsViewTests(test.TestCase):
    def setUp(self):
        super(SecurityGroupsViewTests, self).setUp()
        sec_group = self.security_groups.first()
        self.detail_url = reverse('horizon:project:access_and_security:'
                                  'security_groups:detail',
                                  args=[sec_group.id])
        self.edit_url = reverse('horizon:project:access_and_security:'
                                'security_groups:add_rule',
                                args=[sec_group.id])

    def test_create_security_groups_get(self):
        res = self.client.get(SG_CREATE_URL)
        self.assertTemplateUsed(res,
                    'project/access_and_security/security_groups/create.html')

    def test_create_security_groups_post(self):
        sec_group = self.security_groups.first()
        self.mox.StubOutWithMock(api.nova, 'security_group_create')
        api.nova.security_group_create(IsA(http.HttpRequest),
                                       sec_group.name,
                                       sec_group.description) \
            .AndReturn(sec_group)
        self.mox.ReplayAll()

        formData = {'method': 'CreateGroup',
                    'name': sec_group.name,
                    'description': sec_group.description}
        res = self.client.post(SG_CREATE_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_create_security_groups_post_exception(self):
        sec_group = self.security_groups.first()
        self.mox.StubOutWithMock(api.nova, 'security_group_create')
        api.nova.security_group_create(IsA(http.HttpRequest),
                                       sec_group.name,
                                       sec_group.description) \
            .AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        formData = {'method': 'CreateGroup',
                    'name': sec_group.name,
                    'description': sec_group.description}
        res = self.client.post(SG_CREATE_URL, formData)
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_create_security_groups_post_wrong_name(self):
        sec_group = self.security_groups.first()
        self.mox.StubOutWithMock(api.nova, 'security_group_create')
        fail_name = sec_group.name + ' invalid'
        self.mox.ReplayAll()

        formData = {'method': 'CreateGroup',
                    'name': fail_name,
                    'description': sec_group.description}
        res = self.client.post(SG_CREATE_URL, formData)
        self.assertTemplateUsed(res,
                    'project/access_and_security/security_groups/create.html')
        self.assertContains(res, "ASCII")

    def test_detail_get(self):
        sec_group = self.security_groups.first()

        self.mox.StubOutWithMock(api.nova, 'security_group_get')
        api.nova.security_group_get(IsA(http.HttpRequest),
                                    sec_group.id).AndReturn(sec_group)
        self.mox.ReplayAll()
        res = self.client.get(self.detail_url)
        self.assertTemplateUsed(res,
                'project/access_and_security/security_groups/detail.html')

    def test_detail_get_exception(self):
        sec_group = self.security_groups.first()

        self.mox.StubOutWithMock(api.nova, 'security_group_get')
        api.nova.security_group_get(IsA(http.HttpRequest),
                                    sec_group.id) \
                .AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        res = self.client.get(self.detail_url)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_detail_add_rule_cidr(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.first()

        self.mox.StubOutWithMock(api.nova, 'security_group_rule_create')
        self.mox.StubOutWithMock(api.nova, 'security_group_list')
        api.nova.security_group_rule_create(IsA(http.HttpRequest),
                                            sec_group.id,
                                            rule.ip_protocol,
                                            int(rule.from_port),
                                            int(rule.to_port),
                                            rule.ip_range['cidr'],
                                            None).AndReturn(rule)
        api.nova.security_group_list(
                        IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'port': rule.from_port,
                    'ip_protocol': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr'],
                    'source': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    def test_detail_add_rule_self_as_source_group(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.get(id=3)

        self.mox.StubOutWithMock(api.nova, 'security_group_rule_create')
        self.mox.StubOutWithMock(api.nova, 'security_group_list')
        api.nova.security_group_rule_create(
            IsA(http.HttpRequest),
            sec_group.id,
            rule.ip_protocol,
            int(rule.from_port),
            int(rule.to_port),
            None,
            u'%s' % sec_group.id).AndReturn(rule)
        api.nova.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'port': rule.from_port,
                    'ip_protocol': rule.ip_protocol,
                    'cidr': '0.0.0.0/0',
                    'security_group': sec_group.id,
                    'source': 'sg'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    def test_detail_invalid_port_range(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.first()

        self.mox.StubOutWithMock(api.nova, 'security_group_list')
        api.nova.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'range',
                    'from_port': rule.from_port,
                    'to_port': int(rule.from_port) - 1,
                    'ip_protocol': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr'],
                    'source': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, "greater than or equal to")

    @test.create_stubs({api.nova: ('security_group_get',
                                   'security_group_list')})
    def test_detail_invalid_icmp_rule(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        icmp_rule = self.security_group_rules.list()[1]

        # 1st Test
        api.nova.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)

        # 2nd Test
        api.nova.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)

        # 3rd Test
        api.nova.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)

        # 4th Test
        api.nova.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)

        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'icmp_type': 256,
                    'icmp_code': icmp_rule.to_port,
                    'ip_protocol': icmp_rule.ip_protocol,
                    'cidr': icmp_rule.ip_range['cidr'],
                    'source': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, "The ICMP type not in range (-1, 255)")

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'icmp_type': icmp_rule.from_port,
                    'icmp_code': 256,
                    'ip_protocol': icmp_rule.ip_protocol,
                    'cidr': icmp_rule.ip_range['cidr'],
                    'source': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, "The ICMP code not in range (-1, 255)")

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'icmp_type': icmp_rule.from_port,
                    'icmp_code': None,
                    'ip_protocol': icmp_rule.ip_protocol,
                    'cidr': icmp_rule.ip_range['cidr'],
                    'source_group': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, "The ICMP code is invalid")

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'icmp_type': None,
                    'icmp_code': icmp_rule.to_port,
                    'ip_protocol': icmp_rule.ip_protocol,
                    'cidr': icmp_rule.ip_range['cidr'],
                    'source': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertNoMessages()
        self.assertContains(res, "The ICMP type is invalid")

    def test_detail_add_rule_exception(self):
        sec_group = self.security_groups.first()
        sec_group_list = self.security_groups.list()
        rule = self.security_group_rules.first()

        self.mox.StubOutWithMock(api.nova, 'security_group_rule_create')
        self.mox.StubOutWithMock(api.nova, 'security_group_list')
        api.nova.security_group_rule_create(
            IsA(http.HttpRequest),
            sec_group.id,
            rule.ip_protocol,
            int(rule.from_port),
            int(rule.to_port),
            rule.ip_range['cidr'],
            None).AndRaise(self.exceptions.nova)
        api.nova.security_group_list(
            IsA(http.HttpRequest)).AndReturn(sec_group_list)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'id': sec_group.id,
                    'port_or_range': 'port',
                    'port': rule.from_port,
                    'ip_protocol': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr'],
                    'source': 'cidr'}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, self.detail_url)

    def test_detail_delete_rule(self):
        sec_group = self.security_groups.first()
        rule = self.security_group_rules.first()

        self.mox.StubOutWithMock(api.nova, 'security_group_rule_delete')
        api.nova.security_group_rule_delete(IsA(http.HttpRequest), rule.id)
        self.mox.ReplayAll()

        form_data = {"action": "rules__delete__%s" % rule.id}
        req = self.factory.post(self.edit_url, form_data)
        kwargs = {'security_group_id': sec_group.id}
        table = RulesTable(req, sec_group.rules, **kwargs)
        handled = table.maybe_handle()
        self.assertEqual(strip_absolute_base(handled['location']),
                         self.detail_url)

    def test_detail_delete_rule_exception(self):
        sec_group = self.security_groups.first()
        rule = self.security_group_rules.first()

        self.mox.StubOutWithMock(api.nova, 'security_group_rule_delete')
        api.nova.security_group_rule_delete(
            IsA(http.HttpRequest),
            rule.id).AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        form_data = {"action": "rules__delete__%s" % rule.id}
        req = self.factory.post(self.edit_url, form_data)
        kwargs = {'security_group_id': sec_group.id}
        table = RulesTable(req, self.security_group_rules.list(), **kwargs)
        handled = table.maybe_handle()
        self.assertEqual(strip_absolute_base(handled['location']),
                         self.detail_url)

    def test_delete_group(self):
        sec_group = self.security_groups.get(name="other_group")

        self.mox.StubOutWithMock(api.nova, 'security_group_delete')
        api.nova.security_group_delete(IsA(http.HttpRequest), sec_group.id)
        self.mox.ReplayAll()

        form_data = {"action": "security_groups__delete__%s" % sec_group.id}
        req = self.factory.post(INDEX_URL, form_data)
        table = SecurityGroupsTable(req, self.security_groups.list())
        handled = table.maybe_handle()
        self.assertEqual(strip_absolute_base(handled['location']),
                         INDEX_URL)

    def test_delete_group_exception(self):
        sec_group = self.security_groups.get(name="other_group")

        self.mox.StubOutWithMock(api.nova, 'security_group_delete')
        api.nova.security_group_delete(
            IsA(http.HttpRequest),
            sec_group.id).AndRaise(self.exceptions.nova)

        self.mox.ReplayAll()

        form_data = {"action": "security_groups__delete__%s" % sec_group.id}
        req = self.factory.post(INDEX_URL, form_data)
        table = SecurityGroupsTable(req, self.security_groups.list())
        handled = table.maybe_handle()

        self.assertEqual(strip_absolute_base(handled['location']),
                         INDEX_URL)


class SecurityGroupsQuantumTests(SecurityGroupsViewTests):
    def setUp(self):
        super(SecurityGroupsQuantumTests, self).setUp()

        self._sec_groups_orig = self.security_groups
        self.security_groups = self.security_groups_uuid

        self._sec_group_rules_orig = self.security_group_rules
        self.security_group_rules = self.security_group_rules_uuid

        sec_group = self.security_groups.first()
        self.detail_url = reverse('horizon:project:access_and_security:'
                                  'security_groups:detail',
                                  args=[sec_group.id])
        self.edit_url = reverse('horizon:project:access_and_security:'
                                'security_groups:add_rule',
                                args=[sec_group.id])

    def tearDown(self):
        self.security_groups = self._sec_groups_orig
        self.security_group_rules = self._sec_group_rules_orig
        super(SecurityGroupsQuantumTests, self).tearDown()
