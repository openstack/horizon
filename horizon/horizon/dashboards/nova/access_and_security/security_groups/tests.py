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
from django.conf import settings
from django.core.urlresolvers import reverse
from glance.common import exception as glance_exception
from openstackx.api import exceptions as api_exceptions
from novaclient import exceptions as novaclient_exceptions
from novaclient.v1_1 import security_group_rules as nova_rules
from mox import IgnoreArg, IsA

from horizon import api
from horizon import test
from .tables import SecurityGroupsTable, RulesTable

SECGROUP_ID = '2'
INDEX_URL = reverse('horizon:nova:access_and_security:index')
SG_CREATE_URL = \
            reverse('horizon:nova:access_and_security:security_groups:create')
SG_EDIT_RULE_URL = \
        reverse('horizon:nova:access_and_security:security_groups:edit_rules',
                           args=[SECGROUP_ID])


def strip_absolute_base(uri):
    return uri.split(settings.TESTSERVER, 1)[-1]


class SecurityGroupsViewTests(test.BaseViewTests):
    def setUp(self):
        super(SecurityGroupsViewTests, self).setUp()

        sg1 = api.SecurityGroup(None)
        sg1.id = 1
        sg1.name = 'default'

        sg2 = api.SecurityGroup(None)
        sg2.id = 2
        sg2.name = 'group_2'

        rule = {'id': 1,
                'ip_protocol': u"tcp",
                'from_port': "80",
                'to_port': "80",
                'parent_group_id': "2",
                'ip_range': {'cidr': "0.0.0.0/32"}}
        manager = nova_rules.SecurityGroupRuleManager
        rule_obj = nova_rules.SecurityGroupRule(manager, rule)
        self.rules = [rule_obj]
        sg1.rules = self.rules
        sg2.rules = self.rules

        self.security_groups = (sg1, sg2)

    def test_create_security_groups_get(self):
        res = self.client.get(SG_CREATE_URL)

        self.assertTemplateUsed(res,
                        'nova/access_and_security/security_groups/create.html')

    def test_create_security_groups_post(self):
        SECGROUP_NAME = 'fakegroup'
        SECGROUP_DESC = 'fakegroup_desc'

        new_group = self.mox.CreateMock(api.SecurityGroup)
        new_group.name = SECGROUP_NAME

        formData = {'method': 'CreateGroup',
                    'tenant_id': self.TEST_TENANT,
                    'name': SECGROUP_NAME,
                    'description': SECGROUP_DESC,
                   }

        self.mox.StubOutWithMock(api, 'security_group_create')
        api.security_group_create(IsA(http.HttpRequest),
                           SECGROUP_NAME, SECGROUP_DESC).AndReturn(new_group)

        self.mox.ReplayAll()

        res = self.client.post(SG_CREATE_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_create_security_groups_post_exception(self):
        SECGROUP_NAME = 'fakegroup'
        SECGROUP_DESC = 'fakegroup_desc'

        exception = novaclient_exceptions.ClientException('ClientException',
                                                  message='ClientException')

        formData = {'method': 'CreateGroup',
                    'tenant_id': self.TEST_TENANT,
                    'name': SECGROUP_NAME,
                    'description': SECGROUP_DESC,
                   }

        self.mox.StubOutWithMock(api, 'security_group_create')
        api.security_group_create(IsA(http.HttpRequest),
                           SECGROUP_NAME, SECGROUP_DESC).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.post(SG_CREATE_URL, formData)

        self.assertTemplateUsed(res,
                        'nova/access_and_security/security_groups/create.html')

    def test_edit_rules_get(self):
        self.mox.StubOutWithMock(api, 'security_group_get')
        api.security_group_get(IsA(http.HttpRequest), SECGROUP_ID).AndReturn(
                                   self.security_groups[1])

        self.mox.ReplayAll()

        res = self.client.get(SG_EDIT_RULE_URL)

        self.assertTemplateUsed(res,
                    'nova/access_and_security/security_groups/edit_rules.html')
        self.assertItemsEqual(res.context['security_group'].name,
                              self.security_groups[1].name)

    def test_edit_rules_get_exception(self):
        exception = novaclient_exceptions.ClientException('ClientException',
                                                  message='ClientException')

        self.mox.StubOutWithMock(api, 'security_group_get')
        api.security_group_get(IsA(http.HttpRequest), SECGROUP_ID) \
                               .AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.get(SG_EDIT_RULE_URL)

        self.assertRedirects(res, INDEX_URL)

    def test_edit_rules_add_rule(self):
        RULE_ID = '1'
        FROM_PORT = '-1'
        TO_PORT = '-1'
        IP_PROTOCOL = 'icmp'
        CIDR = '0.0.0.0/0'

        new_rule = self.mox.CreateMock(api.SecurityGroup)
        new_rule.from_port = FROM_PORT
        new_rule.to_port = TO_PORT
        new_rule.ip_protocol = IP_PROTOCOL
        new_rule.cidr = CIDR
        new_rule.security_group_id = SECGROUP_ID
        new_rule.id = RULE_ID

        formData = {'method': 'AddRule',
                    'tenant_id': self.TEST_TENANT,
                    'security_group_id': SECGROUP_ID,
                    'from_port': FROM_PORT,
                    'to_port': TO_PORT,
                    'ip_protocol': IP_PROTOCOL,
                    'cidr': CIDR}

        self.mox.StubOutWithMock(api, 'security_group_rule_create')
        api.security_group_rule_create(IsA(http.HttpRequest),
                           SECGROUP_ID, IP_PROTOCOL, FROM_PORT, TO_PORT, CIDR)\
                           .AndReturn(new_rule)

        self.mox.ReplayAll()

        res = self.client.post(SG_EDIT_RULE_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_edit_rules_add_rule_exception(self):
        exception = novaclient_exceptions.ClientException('ClientException',
                                                  message='ClientException')

        RULE_ID = '1'
        FROM_PORT = '-1'
        TO_PORT = '-1'
        IP_PROTOCOL = 'icmp'
        CIDR = '0.0.0.0/0'

        formData = {'method': 'AddRule',
                    'tenant_id': self.TEST_TENANT,
                    'security_group_id': SECGROUP_ID,
                    'from_port': FROM_PORT,
                    'to_port': TO_PORT,
                    'ip_protocol': IP_PROTOCOL,
                    'cidr': CIDR}

        self.mox.StubOutWithMock(api, 'security_group_rule_create')
        api.security_group_rule_create(IsA(http.HttpRequest),
                           SECGROUP_ID, IP_PROTOCOL, FROM_PORT,
                           TO_PORT, CIDR).AndRaise(exception)

        self.mox.ReplayAll()

        res = self.client.post(SG_EDIT_RULE_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_edit_rules_delete_rule(self):
        RULE_ID = 1

        self.mox.StubOutWithMock(api, 'security_group_rule_delete')
        api.security_group_rule_delete(IsA(http.HttpRequest), RULE_ID)

        self.mox.ReplayAll()

        form_data = {"action": "rules__delete__%s" % RULE_ID}
        req = self.factory.post(SG_EDIT_RULE_URL, form_data)
        table = RulesTable(req, self.rules)
        handled = table.maybe_handle()

        self.assertEqual(strip_absolute_base(handled['location']),
                         INDEX_URL)

    def test_edit_rules_delete_rule_exception(self):
        RULE_ID = 1

        self.mox.StubOutWithMock(api, 'security_group_rule_delete')

        exception = novaclient_exceptions.ClientException('ClientException',
                                                  message='ClientException')
        api.security_group_rule_delete(IsA(http.HttpRequest), RULE_ID) \
                                       .AndRaise(exception)

        self.mox.ReplayAll()

        form_data = {"action": "rules__delete__%s" % RULE_ID}
        req = self.factory.post(SG_EDIT_RULE_URL, form_data)
        table = RulesTable(req, self.rules)
        handled = table.maybe_handle()

        self.assertEqual(strip_absolute_base(handled['location']),
                         INDEX_URL)

    def test_delete_group(self):
        self.mox.StubOutWithMock(api, 'security_group_delete')
        api.security_group_delete(IsA(http.HttpRequest), 2)

        self.mox.ReplayAll()

        form_data = {"action": "security_groups__delete__%s" % '2'}
        req = self.factory.post(INDEX_URL, form_data)
        table = SecurityGroupsTable(req, self.security_groups)
        handled = table.maybe_handle()

        self.assertEqual(strip_absolute_base(handled['location']),
                         INDEX_URL)

    def test_delete_group_exception(self):
        self.mox.StubOutWithMock(api, 'security_group_delete')
        exception = novaclient_exceptions.ClientException('ClientException',
                                                  message='ClientException')
        api.security_group_delete(IsA(http.HttpRequest), 2).\
                                  AndRaise(exception)

        self.mox.ReplayAll()

        form_data = {"action": "security_groups__delete__%s" % '2'}
        req = self.factory.post(INDEX_URL, form_data)
        table = SecurityGroupsTable(req, self.security_groups)
        handled = table.maybe_handle()

        self.assertEqual(strip_absolute_base(handled['location']),
                         INDEX_URL)
