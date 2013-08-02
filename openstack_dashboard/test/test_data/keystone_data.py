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

from datetime import timedelta

from django.conf import settings
from django.utils import datetime_safe

from keystoneclient.access import AccessInfo
from keystoneclient.v2_0 import ec2
from keystoneclient.v2_0 import roles
from keystoneclient.v2_0 import tenants
from keystoneclient.v2_0 import users
from keystoneclient.v3 import domains
from keystoneclient.v3 import groups

from openstack_auth.user import Token

from openstack_dashboard.test.test_data.utils import TestDataContainer


# Dummy service catalog with all service.
# All endpoint URLs should point to example.com.
# Try to keep them as accurate to real data as possible (ports, URIs, etc.)
SERVICE_CATALOG = [
    {"type": "compute",
     "name": "nova",
     "endpoints_links": [],
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.nova.example.com:8774/v2",
         "internalURL": "http://int.nova.example.com:8774/v2",
         "publicURL": "http://public.nova.example.com:8774/v2"},
        {"region": "RegionTwo",
         "adminURL": "http://admin.nova2.example.com:8774/v2",
         "internalURL": "http://int.nova2.example.com:8774/v2",
         "publicURL": "http://public.nova2.example.com:8774/v2"}]},
    {"type": "volume",
     "name": "nova",
     "endpoints_links": [],
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.nova.example.com:8776/v1",
         "internalURL": "http://int.nova.example.com:8776/v1",
         "publicURL": "http://public.nova.example.com:8776/v1"},
        {"region": "RegionTwo",
         "adminURL": "http://admin.nova.example.com:8776/v1",
         "internalURL": "http://int.nova.example.com:8776/v1",
         "publicURL": "http://public.nova.example.com:8776/v1"}]},
    {"type": "image",
     "name": "glance",
     "endpoints_links": [],
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.glance.example.com:9292/v1",
         "internalURL": "http://int.glance.example.com:9292/v1",
         "publicURL": "http://public.glance.example.com:9292/v1"}]},
    {"type": "identity",
     "name": "keystone",
     "endpoints_links": [],
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.keystone.example.com:35357/v2.0",
         "internalURL": "http://int.keystone.example.com:5000/v2.0",
         "publicURL": "http://public.keystone.example.com:5000/v2.0"}]},
    {"type": "object-store",
     "name": "swift",
     "endpoints_links": [],
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.swift.example.com:8080/",
         "internalURL": "http://int.swift.example.com:8080/",
         "publicURL": "http://public.swift.example.com:8080/"}]},
    {"type": "network",
     "name": "neutron",
     "endpoints_links": [],
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.neutron.example.com:9696/",
         "internalURL": "http://int.neutron.example.com:9696/",
         "publicURL": "http://public.neutron.example.com:9696/"}]},
    {"type": "ec2",
     "name": "EC2 Service",
     "endpoints_links": [],
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.nova.example.com:8773/services/Admin",
         "publicURL": "http://public.nova.example.com:8773/services/Cloud",
         "internalURL": "http://int.nova.example.com:8773/services/Cloud"}]},
    {"type": "orchestration",
     "name": "Heat",
     "endpoints_links": [],
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.heat.example.com:8004/v1",
         "publicURL": "http://public.heat.example.com:8004/v1",
         "internalURL": "http://int.heat.example.com:8004/v1"}]}
]


def data(TEST):
    TEST.service_catalog = SERVICE_CATALOG
    TEST.tokens = TestDataContainer()
    TEST.domains = TestDataContainer()
    TEST.users = TestDataContainer()
    TEST.groups = TestDataContainer()
    TEST.tenants = TestDataContainer()
    TEST.roles = TestDataContainer()
    TEST.ec2 = TestDataContainer()

    admin_role_dict = {'id': '1',
                       'name': 'admin'}
    admin_role = roles.Role(roles.RoleManager, admin_role_dict)
    member_role_dict = {'id': "2",
                        'name': settings.OPENSTACK_KEYSTONE_DEFAULT_ROLE}
    member_role = roles.Role(roles.RoleManager, member_role_dict)
    TEST.roles.add(admin_role, member_role)
    TEST.roles.admin = admin_role
    TEST.roles.member = member_role

    domain_dict = {'id': "1",
                   'name': 'test_domain',
                   'description': "a test domain.",
                   'enabled': True}
    domain_dict_2 = {'id': "2",
                     'name': 'disabled_domain',
                     'description': "a disabled test domain.",
                     'enabled': False}
    domain = domains.Domain(domains.DomainManager, domain_dict)
    disabled_domain = domains.Domain(domains.DomainManager, domain_dict_2)
    TEST.domains.add(domain, disabled_domain)
    TEST.domain = domain  # Your "current" domain

    user_dict = {'id': "1",
                 'name': 'test_user',
                 'email': 'test@example.com',
                 'password': 'password',
                 'token': 'test_token',
                 'project_id': '1',
                 'enabled': True,
                 'domain_id': "1"}
    user = users.User(users.UserManager(None), user_dict)
    user_dict = {'id': "2",
                 'name': 'user_two',
                 'email': 'two@example.com',
                 'password': 'password',
                 'token': 'test_token',
                 'project_id': '1',
                 'enabled': True,
                 'domain_id': "1"}
    user2 = users.User(users.UserManager(None), user_dict)
    user_dict = {'id': "3",
                 'name': 'user_three',
                 'email': 'three@example.com',
                 'password': 'password',
                 'token': 'test_token',
                 'project_id': '1',
                 'enabled': True,
                 'domain_id': "1"}
    user3 = users.User(users.UserManager(None), user_dict)
    user_dict = {'id': "4",
                 'name': 'user_four',
                 'email': 'four@example.com',
                 'password': 'password',
                 'token': 'test_token',
                 'project_id': '2',
                 'enabled': True,
                 'domain_id': "2"}
    user4 = users.User(users.UserManager(None), user_dict)
    TEST.users.add(user, user2, user3, user4)
    TEST.user = user  # Your "current" user
    TEST.user.service_catalog = SERVICE_CATALOG

    group_dict = {'id': "1",
                 'name': 'group_one',
                 'description': 'group one description',
                 'domain_id': '1'}
    group = groups.Group(groups.GroupManager(None), group_dict)
    group_dict = {'id': "2",
                 'name': 'group_two',
                 'description': 'group two description',
                 'domain_id': '1'}
    group2 = groups.Group(groups.GroupManager(None), group_dict)
    group_dict = {'id': "3",
                 'name': 'group_three',
                 'description': 'group three description',
                 'domain_id': '2'}
    group3 = groups.Group(groups.GroupManager(None), group_dict)
    TEST.groups.add(group, group2, group3)

    tenant_dict = {'id': "1",
                   'name': 'test_tenant',
                   'description': "a test tenant.",
                   'enabled': True,
                   'domain_id': '1'}
    tenant_dict_2 = {'id': "2",
                     'name': 'disabled_tenant',
                     'description': "a disabled test tenant.",
                     'enabled': False,
                     'domain_id': '2'}
    tenant_dict_3 = {'id': "3",
                     'name': u'\u4e91\u89c4\u5219',
                     'description': "an unicode-named tenant.",
                     'enabled': True,
                     'domain_id': '2'}
    tenant = tenants.Tenant(tenants.TenantManager, tenant_dict)
    disabled_tenant = tenants.Tenant(tenants.TenantManager, tenant_dict_2)
    tenant_unicode = tenants.Tenant(tenants.TenantManager, tenant_dict_3)

    TEST.tenants.add(tenant, disabled_tenant, tenant_unicode)
    TEST.tenant = tenant  # Your "current" tenant

    tomorrow = datetime_safe.datetime.now() + timedelta(days=1)
    expiration = datetime_safe.datetime.isoformat(tomorrow)

    scoped_token_dict = {
        'access': {
            'token': {
                'id': "test_token_id",
                'expires': expiration,
                'tenant': tenant_dict,
                'tenants': [tenant_dict]},
            'user': {
                'id': "test_user_id",
                'name': "test_user",
                'roles': [member_role_dict]},
            'serviceCatalog': TEST.service_catalog
        }
    }

    scoped_access_info = AccessInfo.factory(resp=None,
                                            body=scoped_token_dict)

    unscoped_token_dict = {
        'access': {
            'token': {
                'id': "test_token_id",
                'expires': expiration},
            'user': {
                     'id': "test_user_id",
                     'name': "test_user",
                     'roles': [member_role_dict]},
            'serviceCatalog': TEST.service_catalog
        }
    }
    unscoped_access_info = AccessInfo.factory(resp=None,
                                              body=unscoped_token_dict)

    scoped_token = Token(scoped_access_info)
    unscoped_token = Token(unscoped_access_info)
    TEST.tokens.add(scoped_token, unscoped_token)
    TEST.token = scoped_token  # your "current" token.
    TEST.tokens.scoped_token = scoped_token
    TEST.tokens.unscoped_token = unscoped_token

    access_secret = ec2.EC2(ec2.CredentialsManager, {"access": "access",
                                                     "secret": "secret"})
    TEST.ec2.add(access_secret)
