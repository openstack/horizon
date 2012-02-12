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
from novaclient import exceptions as novaclient_exceptions
from mox import IsA

from horizon import api
from horizon import test
from .tables import SecurityGroupsTable, RulesTable

INDEX_URL = reverse('horizon:nova:access_and_security:index')
SG_CREATE_URL = \
            reverse('horizon:nova:access_and_security:security_groups:create')


def strip_absolute_base(uri):
    return uri.split(settings.TESTSERVER, 1)[-1]


class SecurityGroupsViewTests(test.TestCase):
    def setUp(self):
        super(SecurityGroupsViewTests, self).setUp()
        sec_group = self.security_groups.first()
        self.edit_url = reverse('horizon:nova:access_and_security:'
                                'security_groups:edit_rules',
                                args=[sec_group.id])

    def test_create_security_groups_get(self):
        res = self.client.get(SG_CREATE_URL)
        self.assertTemplateUsed(res,
                        'nova/access_and_security/security_groups/create.html')

    def test_create_security_groups_post(self):
        sec_group = self.security_groups.first()
        self.mox.StubOutWithMock(api, 'security_group_create')
        api.security_group_create(IsA(http.HttpRequest),
                                  sec_group.name,
                                  sec_group.description).AndReturn(sec_group)
        self.mox.ReplayAll()

        formData = {'method': 'CreateGroup',
                    'tenant_id': self.tenant.id,
                    'name': sec_group.name,
                    'description': sec_group.description}
        res = self.client.post(SG_CREATE_URL, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_create_security_groups_post_exception(self):
        sec_group = self.security_groups.first()
        self.mox.StubOutWithMock(api, 'security_group_create')
        exc = novaclient_exceptions.ClientException('ClientException')
        api.security_group_create(IsA(http.HttpRequest),
                                  sec_group.name,
                                  sec_group.description).AndRaise(exc)
        self.mox.ReplayAll()

        formData = {'method': 'CreateGroup',
                    'tenant_id': self.tenant.id,
                    'name': sec_group.name,
                    'description': sec_group.description}
        res = self.client.post(SG_CREATE_URL, formData)
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_edit_rules_get(self):
        sec_group = self.security_groups.first()
        self.mox.StubOutWithMock(api, 'security_group_get')
        api.security_group_get(IsA(http.HttpRequest),
                               sec_group.id).AndReturn(sec_group)
        self.mox.ReplayAll()

        res = self.client.get(self.edit_url)
        self.assertTemplateUsed(res,
                    'nova/access_and_security/security_groups/edit_rules.html')
        self.assertItemsEqual(res.context['security_group'].name,
                              sec_group.name)

    def test_edit_rules_get_exception(self):
        sec_group = self.security_groups.first()

        self.mox.StubOutWithMock(api, 'security_group_get')
        exc = novaclient_exceptions.ClientException('ClientException')
        api.security_group_get(IsA(http.HttpRequest),
                               sec_group.id).AndRaise(exc)
        self.mox.ReplayAll()

        res = self.client.get(self.edit_url)
        self.assertRedirects(res, INDEX_URL)

    def test_edit_rules_add_rule(self):
        sec_group = self.security_groups.first()
        rule = self.security_group_rules.first()

        self.mox.StubOutWithMock(api, 'security_group_rule_create')
        api.security_group_rule_create(IsA(http.HttpRequest),
                                       sec_group.id,
                                       rule.ip_protocol,
                                       rule.from_port,
                                       rule.to_port,
                                       rule.ip_range['cidr']).AndReturn(rule)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'tenant_id': self.tenant.id,
                    'security_group_id': sec_group.id,
                    'from_port': rule.from_port,
                    'to_port': rule.to_port,
                    'ip_protocol': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr']}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_edit_rules_add_rule_exception(self):
        sec_group = self.security_groups.first()
        rule = self.security_group_rules.first()
        exc = novaclient_exceptions.ClientException('ClientException')

        self.mox.StubOutWithMock(api, 'security_group_rule_create')
        api.security_group_rule_create(IsA(http.HttpRequest),
                                       sec_group.id,
                                       rule.ip_protocol,
                                       rule.from_port,
                                       rule.to_port,
                                       rule.ip_range['cidr']).AndRaise(exc)
        self.mox.ReplayAll()

        formData = {'method': 'AddRule',
                    'tenant_id': self.tenant.id,
                    'security_group_id': sec_group.id,
                    'from_port': rule.from_port,
                    'to_port': rule.to_port,
                    'ip_protocol': rule.ip_protocol,
                    'cidr': rule.ip_range['cidr']}
        res = self.client.post(self.edit_url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_edit_rules_delete_rule(self):
        sec_group = self.security_groups.first()
        rule = self.security_group_rules.first()

        self.mox.StubOutWithMock(api, 'security_group_rule_delete')
        api.security_group_rule_delete(IsA(http.HttpRequest), rule.id)
        self.mox.ReplayAll()

        form_data = {"action": "rules__delete__%s" % rule.id}
        req = self.factory.post(self.edit_url, form_data)
        table = RulesTable(req, sec_group.rules)
        handled = table.maybe_handle()
        self.assertEqual(strip_absolute_base(handled['location']), INDEX_URL)

    def test_edit_rules_delete_rule_exception(self):
        rule = self.security_group_rules.first()

        self.mox.StubOutWithMock(api, 'security_group_rule_delete')
        exc = novaclient_exceptions.ClientException('ClientException')
        api.security_group_rule_delete(IsA(http.HttpRequest),
                                       rule.id).AndRaise(exc)
        self.mox.ReplayAll()

        form_data = {"action": "rules__delete__%s" % rule.id}
        req = self.factory.post(self.edit_url, form_data)
        table = RulesTable(req, self.security_group_rules.list())
        handled = table.maybe_handle()
        self.assertEqual(strip_absolute_base(handled['location']),
                         INDEX_URL)

    def test_delete_group(self):
        sec_group = self.security_groups.get(name="other_group")

        self.mox.StubOutWithMock(api, 'security_group_delete')
        api.security_group_delete(IsA(http.HttpRequest), sec_group.id)
        self.mox.ReplayAll()

        form_data = {"action": "security_groups__delete__%s" % sec_group.id}
        req = self.factory.post(INDEX_URL, form_data)
        table = SecurityGroupsTable(req, self.security_groups.list())
        handled = table.maybe_handle()
        self.assertEqual(strip_absolute_base(handled['location']),
                         INDEX_URL)

    def test_delete_group_exception(self):
        sec_group = self.security_groups.get(name="other_group")

        self.mox.StubOutWithMock(api, 'security_group_delete')
        exc = novaclient_exceptions.ClientException('ClientException')
        api.security_group_delete(IsA(http.HttpRequest),
                                  sec_group.id).AndRaise(exc)

        self.mox.ReplayAll()

        form_data = {"action": "security_groups__delete__%s" % sec_group.id}
        req = self.factory.post(INDEX_URL, form_data)
        table = SecurityGroupsTable(req, self.security_groups.list())
        handled = table.maybe_handle()

        self.assertEqual(strip_absolute_base(handled['location']),
                         INDEX_URL)
