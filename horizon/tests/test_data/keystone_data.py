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

from django.conf import settings
from keystoneclient.v2_0 import users, tenants, tokens, roles, ec2

from .utils import TestDataContainer


# Dummy service catalog with all service.
# All endpoint URLs should point to example.com.
# Try to keep them as accurate to real data as possible (ports, URIs, etc.)
SERVICE_CATALOG = [
    {"type": "compute",
     "name": "nova",
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.nova.example.com:8774/v2",
         "internalURL": "http://internal.nova.example.com:8774/v2",
         "publicURL": "http://public.nova.example.com:8774/v2"}]},
    {"type": "volume",
     "name": "nova",
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.nova.example.com:8776/v1",
         "internalURL": "http://internal.nova.example.com:8776/v1",
         "publicURL": "http://public.nova.example.com:8776/v1"}]},
    {"type": "image",
     "name": "glance",
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.glance.example.com:9292/v1",
         "internalURL": "http://internal.glance.example.com:9292/v1",
         "publicURL": "http://public.glance.example.com:9292/v1"}]},
    {"type": "identity",
     "name": "keystone",
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.keystone.example.com:35357/v2.0",
         "internalURL": "http://internal.keystone.example.com:5000/v2.0",
         "publicURL": "http://public.keystone.example.com:5000/v2.0"}]},
    {"type": "object-store",
     "name": "swift",
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.swift.example.com:8080/",
         "internalURL": "http://internal.swift.example.com:8080/",
         "publicURL": "http://public.swift.example.com:8080/"}]},
    {"type": "network",
     "name": "quantum",
     "endpoints": [
        {"region": "RegionOne",
         "adminURL": "http://admin.quantum.example.com:9696/",
         "internalURL": "http://internal.quantum.example.com:9696/",
         "publicURL": "http://public.quantum.example.com:9696/"}]},
]


def data(TEST):
    TEST.service_catalog = SERVICE_CATALOG
    TEST.tokens = TestDataContainer()
    TEST.users = TestDataContainer()
    TEST.tenants = TestDataContainer()
    TEST.roles = TestDataContainer()
    TEST.ec2 = TestDataContainer()

    admin_role_dict = {'id': '1',
                       'name': 'admin'}
    admin_role = roles.Role(roles.RoleManager, admin_role_dict)
    member_role_dict = {'id': "2",
                        'name': settings.OPENSTACK_KEYSTONE_DEFAULT_ROLE}
    member_role = roles.Role(roles.RoleManager, member_role_dict)
    TEST.roles.add(member_role, admin_role)
    TEST.roles.admin = admin_role
    TEST.roles.member = member_role

    user_dict = {'id': "1",
                 'name': 'test_user',
                 'email': 'test@example.com',
                 'password': 'password',
                 'token': 'test_token'}
    user = users.User(users.UserManager, user_dict)
    user_dict.update({'id': "2",
                      'name': 'user_two',
                      'email': 'two@example.com'})
    user2 = users.User(users.UserManager, user_dict)
    TEST.users.add(user, user2)
    TEST.user = user  # Your "current" user
    TEST.user.service_catalog = SERVICE_CATALOG

    tenant_dict = {'id': "1",
                   'name': 'test_tenant',
                   'description': "a test tenant.",
                   'enabled': True}
    tenant = tenants.Tenant(tenants.TenantManager, tenant_dict)
    TEST.tenants.add(tenant)
    TEST.tenant = tenant  # Your "current" tenant

    scoped_token = tokens.Token(tokens.TokenManager,
                                dict(token={"id": "test_token_id",
                                            "expires": "#FIXME",
                                            "tenant": tenant_dict,
                                            "tenants": [tenant_dict]},
                                     user={"id": "test_user_id",
                                           "name": "test_user",
                                           "roles": [member_role_dict]},
                                     serviceCatalog=TEST.service_catalog))
    unscoped_token = tokens.Token(tokens.TokenManager,
                                  dict(token={"id": "test_token_id",
                                              "expires": "#FIXME"},
                                       user={"id": "test_user_id",
                                             "name": "test_user",
                                             "roles": [member_role_dict]},
                                       serviceCatalog=TEST.service_catalog))
    TEST.tokens.add(scoped_token, unscoped_token)
    TEST.token = scoped_token  # your "current" token.
    TEST.tokens.scoped_token = scoped_token
    TEST.tokens.unscoped_token = unscoped_token

    access_secret = ec2.EC2(ec2.CredentialsManager, {"access": "access",
                                                     "secret": "secret"})
    TEST.ec2.add(access_secret)
