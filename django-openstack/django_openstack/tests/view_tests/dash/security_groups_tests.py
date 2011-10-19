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
from glance.common import exception as glance_exception
from openstackx.api import exceptions as api_exceptions
from novaclient import exceptions as novaclient_exceptions
from mox import IgnoreArg, IsA


class SecurityGroupsViewTests(base.BaseViewTests):
    def setUp(self):
        super(SecurityGroupsViewTests, self).setUp()

        security_group = self.mox.CreateMock(api.SecurityGroup)
        security_group.name = 'default'
        self.security_groups = (security_group,)

    def test_index(self):
        self.mox.StubOutWithMock(api, 'security_group_list')
        api.security_group_list(IsA(http.HttpRequest)).\
                                AndReturn(self.security_groups)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_security_groups',
                              args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/security_groups/index.html')
        self.assertItemsEqual(res.context['security_groups'],
                              self.security_groups)

        self.mox.VerifyAll()

    def test_index_exception(self):
        exception = novaclient_exceptions.ClientException('ClientException',
                                                  message='ClientException')
        self.mox.StubOutWithMock(api, 'security_group_list')
        api.security_group_list(IsA(http.HttpRequest)).AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_security_groups',
                              args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/security_groups/index.html')
        self.assertEqual(len(res.context['security_groups']), 0)

        self.mox.VerifyAll()

    def test_create_security_groups_get(self):
        res = self.client.get(reverse('dash_security_groups_create',
                                      args=[self.TEST_TENANT]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/security_groups/create.html')

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

        res = self.client.post(reverse('dash_security_groups_create',
                                       args=[self.TEST_TENANT]),
                                       formData)

        self.assertRedirectsNoFollow(res, reverse('dash_security_groups',
                                          args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

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

        res = self.client.post(reverse('dash_security_groups_create',
                                       args=[self.TEST_TENANT]),
                                       formData)

        self.assertTemplateUsed(res,
                'django_openstack/dash/security_groups/create.html')

        self.mox.VerifyAll()

    def test_edit_rules_get(self):
        SECGROUP_ID = '1'

        self.mox.StubOutWithMock(api, 'security_group_get')
        api.security_group_get(IsA(http.HttpRequest), SECGROUP_ID).AndReturn(
                                   self.security_groups[0])

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_security_groups_edit_rules',
                                       args=[self.TEST_TENANT, SECGROUP_ID]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/security_groups/edit_rules.html')
        self.assertItemsEqual(res.context['security_group'].name,
                              self.security_groups[0].name)

        self.mox.VerifyAll()

    def test_edit_rules_get_exception(self):
        SECGROUP_ID = '1'

        exception = novaclient_exceptions.ClientException('ClientException',
                                                  message='ClientException')

        self.mox.StubOutWithMock(api, 'security_group_get')
        api.security_group_get(IsA(http.HttpRequest), SECGROUP_ID).AndRaise(
                                   exception)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_security_groups_edit_rules',
                                       args=[self.TEST_TENANT, SECGROUP_ID]))

        self.assertRedirectsNoFollow(res, reverse('dash_security_groups',
                                          args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def test_edit_rules_add_rule(self):
        SECGROUP_ID = '1'
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

        self.mox.StubOutWithMock(messages, 'info')
        messages.info(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_security_groups_edit_rules',
                                       args=[self.TEST_TENANT, SECGROUP_ID]),
                                       formData)

        self.assertRedirectsNoFollow(res,
                                     reverse('dash_security_groups_edit_rules',
                                     args=[self.TEST_TENANT, SECGROUP_ID]))

        self.mox.VerifyAll()

    def test_edit_rules_add_rule_exception(self):
        exception = novaclient_exceptions.ClientException('ClientException',
                                                  message='ClientException')

        SECGROUP_ID = '1'
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

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_security_groups_edit_rules',
                                       args=[self.TEST_TENANT, SECGROUP_ID]),
                                       formData)

        self.assertRedirectsNoFollow(res,
                                     reverse('dash_security_groups_edit_rules',
                                     args=[self.TEST_TENANT, SECGROUP_ID]))

        self.mox.VerifyAll()

    def test_edit_rules_delete_rule(self):
        SECGROUP_ID = '1'
        RULE_ID = '1'

        formData = {'method': 'DeleteRule',
                    'tenant_id': self.TEST_TENANT,
                    'security_group_rule_id': RULE_ID,
                   }

        self.mox.StubOutWithMock(api, 'security_group_rule_delete')
        api.security_group_rule_delete(IsA(http.HttpRequest), RULE_ID)

        self.mox.StubOutWithMock(messages, 'info')
        messages.info(IsA(http.HttpRequest), IsA(unicode))

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_security_groups_edit_rules',
                                       args=[self.TEST_TENANT, SECGROUP_ID]),
                                       formData)

        self.assertRedirectsNoFollow(res,
                                     reverse('dash_security_groups_edit_rules',
                                     args=[self.TEST_TENANT, SECGROUP_ID]))

        self.mox.VerifyAll()

    def test_edit_rules_delete_rule_exception(self):
        exception = novaclient_exceptions.ClientException('ClientException',
                                                  message='ClientException')

        SECGROUP_ID = '1'
        RULE_ID = '1'

        formData = {'method': 'DeleteRule',
                    'tenant_id': self.TEST_TENANT,
                    'security_group_rule_id': RULE_ID,
                   }

        self.mox.StubOutWithMock(api, 'security_group_rule_delete')
        api.security_group_rule_delete(IsA(http.HttpRequest), RULE_ID).\
                                       AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_security_groups_edit_rules',
                                       args=[self.TEST_TENANT, SECGROUP_ID]),
                                       formData)

        self.assertRedirectsNoFollow(res,
                                     reverse('dash_security_groups_edit_rules',
                                     args=[self.TEST_TENANT, SECGROUP_ID]))

        self.mox.VerifyAll()

    def test_delete_group(self):
        SECGROUP_ID = '1'

        formData = {'method': 'DeleteGroup',
                    'tenant_id': self.TEST_TENANT,
                    'security_group_id': SECGROUP_ID,
                   }

        self.mox.StubOutWithMock(api, 'security_group_delete')
        api.security_group_delete(IsA(http.HttpRequest), SECGROUP_ID)

        self.mox.StubOutWithMock(messages, 'info')
        messages.info(IsA(http.HttpRequest), IsA(unicode))

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_security_groups',
                                       args=[self.TEST_TENANT]),
                                       formData)

        self.assertRedirectsNoFollow(res, reverse('dash_security_groups',
                                          args=[self.TEST_TENANT]))

        self.mox.VerifyAll()

    def test_delete_group_exception(self):
        exception = novaclient_exceptions.ClientException('ClientException',
                                                  message='ClientException')

        SECGROUP_ID = '1'

        formData = {'method': 'DeleteGroup',
                    'tenant_id': self.TEST_TENANT,
                    'security_group_id': SECGROUP_ID,
                   }

        self.mox.StubOutWithMock(api, 'security_group_delete')
        api.security_group_delete(IsA(http.HttpRequest), SECGROUP_ID).\
                                  AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')
        messages.error(IsA(http.HttpRequest), IsA(basestring))

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_security_groups',
                                       args=[self.TEST_TENANT]),
                                       formData)

        self.assertRedirectsNoFollow(res, reverse('dash_security_groups',
                                          args=[self.TEST_TENANT]))

        self.mox.VerifyAll()
