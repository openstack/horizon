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

import copy
from datetime import timedelta

from django.conf import settings
from django.utils import datetime_safe

from keystoneclient import access
from keystoneclient.v2_0 import roles
from keystoneclient.v2_0 import tenants
from keystoneclient.v2_0 import users
from keystoneclient.v3 import application_credentials
from keystoneclient.v3.contrib.federation import identity_providers
from keystoneclient.v3.contrib.federation import mappings
from keystoneclient.v3.contrib.federation import protocols
from keystoneclient.v3 import credentials
from keystoneclient.v3 import domains
from keystoneclient.v3 import groups
from keystoneclient.v3 import role_assignments

from openstack_auth import user as auth_user

from openstack_dashboard.test.test_data import utils


# Dummy service catalog with all service. All data should match
# scoped_auth_ref.service_catalog.catalog from keystoneauth1.
# All endpoint URLs should point to example.com.
# Try to keep them as accurate to real data as possible (ports, URIs, etc.)
# TODO(e0ne): make RegionOne and RegionTwo links unique.
SERVICE_CATALOG = [
    {"type": "compute",
     "name": "nova",
     "endpoints_links": [],
     "endpoints": [
         {"region": "RegionOne",
          "interface": "admin",
          "url": "http://admin.nova.example.com:8774/v2"},
         {"region": "RegionOne",
          "interface": "internal",
          "url": "http://int.nova.example.com:8774/v2"},
         {"region": "RegionOne",
          "interface": "public",
          "url": "http://public.nova.example.com:8774/v2"},
         {"region": "RegionTwo",
          "interface": "admin",
          "url": "http://admin.nova2.example.com:8774/v2"},
         {"region": "RegionTwo",
          "interface": "internal",
          "url": "http://int.nova2.example.com:8774/v2"},
         {"region": "RegionTwo",
          "interface": "public",
          "url": "http://public.nova2.example.com:8774/v2"}
     ]},
    {"type": "volumev3",
     "name": "cinderv3",
     "endpoints_links": [],
     "endpoints": [
         {"region": "RegionOne",
          "interface": "admin",
          "url": "http://admin.cinder.example.com:8776/v3"},
         {"region": "RegionOne",
          "interface": "internal",
          "url": "http://int.cinder.example.com:8776/v3"},
         {"region": "RegionOne",
          "interface": "public",
          "url": "http://public.cinder.example.com:8776/v3"},
         {"region": "RegionTwo",
          "interface": "admin",
          "url": "http://admin.cinder2.example.com:8776/v3"},
         {"region": "RegionTwo",
          "interface": "internal",
          "url": "http://int.cinder2.example.com:8776/v3"},
         {"region": "RegionTwo",
          "interface": "public",
          "url": "http://public.cinder2.example.com:8776/v3"}
     ]},
    {"type": "image",
     "name": "glance",
     "endpoints_links": [],
     "endpoints": [
         {"region": "RegionOne",
          "interface": "admin",
          "url": "http://admin.glance.example.com:9292",
          },
         {"region": "RegionOne",
          "interface": "internal",
          "url": "http://int.glance.example.com:9292"},
         {"region": "RegionOne",
          "interface": "public",
          "url": "http://public.glance.example.com:9292"}
     ]},
    {"type": "identity",
     "name": "keystone",
     "endpoints_links": [],
     "endpoints": [
         {"region": "RegionOne",
          "interface": "admin",
          "url": "http://admin.keystone.example.com/identity/v3"},
         {"region": "RegionOne",
          "interface": "internal",
          "url": "http://int.keystone.example.com/identity/v3"},
         {"region": "RegionOne",
          "interface": "public",
          "url": "http://public.keystone.example.com/identity/v3"}
     ]},
    {"type": "object-store",
     "name": "swift",
     "endpoints_links": [],
     "endpoints": [
         {"region": "RegionOne",
          "interface": "admin",
          "url": "http://admin.swift.example.com:8080/"},
         {"region": "RegionOne",
          "interface": "internal",
          "url": "http://int.swift.example.com:8080/"},
         {"region": "RegionOne",
          "interface": "public",
          "url": "http://public.swift.example.com:8080/"}
     ]},
    {"type": "network",
     "name": "neutron",
     "endpoints_links": [],
     "endpoints": [
         {"region": "RegionOne",
          "interface": "admin",
          "url": "http://admin.neutron.example.com:9696/"},
         {"region": "RegionOne",
          "interface": "internal",
          "url": "http://int.neutron.example.com:9696/"},
         {"region": "RegionOne",
          "interface": "public",
          "url": "http://public.neutron.example.com:9696/"}
     ]}
]


def data(TEST):
    # Make a deep copy of the catalog to avoid persisting side-effects
    # when tests modify the catalog.
    TEST.service_catalog = copy.deepcopy(SERVICE_CATALOG)
    TEST.tokens = utils.TestDataContainer()
    TEST.domains = utils.TestDataContainer()
    TEST.users = utils.TestDataContainer()
    TEST.groups = utils.TestDataContainer()
    TEST.user_group_membership = utils.TestDataContainer()
    TEST.tenants = utils.TestDataContainer()
    TEST.role_assignments = utils.TestDataContainer()
    TEST.roles = utils.TestDataContainer()

    TEST.identity_providers = utils.TestDataContainer()
    TEST.idp_mappings = utils.TestDataContainer()
    TEST.idp_protocols = utils.TestDataContainer()

    TEST.application_credentials = utils.TestDataContainer()
    TEST.credentials = utils.TestDataContainer()

    admin_role_dict = {'id': '1',
                       'name': 'admin'}
    admin_role = roles.Role(roles.RoleManager, admin_role_dict, loaded=True)
    member_role_dict = {'id': "2",
                        'name': settings.OPENSTACK_KEYSTONE_DEFAULT_ROLE}
    member_role = roles.Role(roles.RoleManager, member_role_dict, loaded=True)
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
    domain_dict_3 = {'id': "3",
                     'name': 'another_test_domain',
                     'description': "another test domain.",
                     'enabled': True}
    domain = domains.Domain(domains.DomainManager, domain_dict)
    disabled_domain = domains.Domain(domains.DomainManager, domain_dict_2)
    another_domain = domains.Domain(domains.DomainManager, domain_dict_3)
    TEST.domains.add(domain, disabled_domain, another_domain)
    TEST.domain = domain  # Your "current" domain

    user_dict = {'id': "1",
                 'name': 'test_user',
                 'description': 'test_description',
                 'email': 'test@example.com',
                 'password': 'password',
                 'token': 'test_token',
                 'project_id': '1',
                 'enabled': True,
                 'domain_id': "1"}
    user = users.User(None, user_dict)
    user_dict = {'id': "2",
                 'name': 'user_two',
                 'description': 'test_description',
                 'email': 'two@example.com',
                 'password': 'password',
                 'token': 'test_token',
                 'project_id': '1',
                 'enabled': True,
                 'domain_id': "1"}
    user2 = users.User(None, user_dict)
    user_dict = {'id': "3",
                 'name': 'user_three',
                 'description': 'test_description',
                 'email': 'three@example.com',
                 'password': 'password',
                 'token': 'test_token',
                 'project_id': '1',
                 'enabled': True,
                 'domain_id': "1"}
    user3 = users.User(None, user_dict)
    user_dict = {'id': "4",
                 'name': 'user_four',
                 'description': 'test_description',
                 'email': 'four@example.com',
                 'password': 'password',
                 'token': 'test_token',
                 'project_id': '2',
                 'enabled': True,
                 'domain_id': "2"}
    user4 = users.User(None, user_dict)
    user_dict = {'id': "5",
                 'name': 'user_five',
                 'description': 'test_description',
                 'email': None,
                 'password': 'password',
                 'token': 'test_token',
                 'project_id': '2',
                 'enabled': True,
                 'domain_id': "1"}
    user5 = users.User(None, user_dict)
    user_dict = {'id': "6",
                 'name': 'user_six',
                 'description': 'test_description',
                 'email': 'test@example.com',
                 'password': 'password',
                 'token': 'test_token',
                 'project_id': '1',
                 'enabled': True,
                 'domain_id': "1",
                 'lock_password': True}
    user6 = users.User(None, user_dict)
    TEST.users.add(user, user2, user3, user4, user5, user6)
    TEST.user = user  # Your "current" user
    TEST.user.service_catalog = copy.deepcopy(SERVICE_CATALOG)

    group_dict = {'id': "1",
                  'name': 'group_one',
                  'description': 'group one description',
                  'project_id': '1',
                  'domain_id': '1'}
    group = groups.Group(groups.GroupManager(None), group_dict)
    group_dict = {'id': "2",
                  'name': 'group_two',
                  'description': 'group two description',
                  'project_id': '1',
                  'domain_id': '1'}
    group2 = groups.Group(groups.GroupManager(None), group_dict)
    group_dict = {'id': "3",
                  'name': 'group_three',
                  'description': 'group three description',
                  'project_id': '1',
                  'domain_id': '1'}
    group3 = groups.Group(groups.GroupManager(None), group_dict)
    group_dict = {'id': "4",
                  'name': 'group_four',
                  'description': 'group four description',
                  'project_id': '2',
                  'domain_id': '2'}
    group4 = groups.Group(groups.GroupManager(None), group_dict)
    # this group intentionally only has id/domain_id to match data
    # returned from Keystone backends like LDAP
    group_dict = {'id': "5",
                  'domain_id': '2'}
    group5 = groups.Group(groups.GroupManager(None), group_dict)

    TEST.groups.add(group, group2, group3, group4, group5)

    user_group_membership = {"user_id": "1", "group_id": "1"}
    TEST.user_group_membership.add(user_group_membership)
    user_group_membership = {"user_id": "1", "group_id": "2"}
    TEST.user_group_membership.add(user_group_membership)
    user_group_membership = {"user_id": "2", "group_id": "2"}
    TEST.user_group_membership.add(user_group_membership)
    user_group_membership = {"user_id": "2", "group_id": "3"}
    TEST.user_group_membership.add(user_group_membership)
    user_group_membership = {"user_id": "3", "group_id": "1"}
    TEST.user_group_membership.add(user_group_membership)
    user_group_membership = {"user_id": "4", "group_id": "1"}
    TEST.user_group_membership.add(user_group_membership)

    role_assignments_dict = {'user': {'id': '1'},
                             'role': {'id': '1'},
                             'scope': {'project': {'id': '1'}}}
    proj_role_assignment1 = role_assignments.RoleAssignment(
        role_assignments.RoleAssignmentManager, role_assignments_dict)
    role_assignments_dict = {'user': {'id': '2'},
                             'role': {'id': '2'},
                             'scope': {'project': {'id': '1'}}}
    proj_role_assignment2 = role_assignments.RoleAssignment(
        role_assignments.RoleAssignmentManager, role_assignments_dict)
    role_assignments_dict = {'group': {'id': '1'},
                             'role': {'id': '2'},
                             'scope': {'project': {'id': '1'}}}
    proj_role_assignment3 = role_assignments.RoleAssignment(
        role_assignments.RoleAssignmentManager, role_assignments_dict)
    role_assignments_dict = {'user': {'id': '3'},
                             'role': {'id': '2'},
                             'scope': {'project': {'id': '1'}}}
    proj_role_assignment4 = role_assignments.RoleAssignment(
        role_assignments.RoleAssignmentManager, role_assignments_dict)
    role_assignments_dict = {'user': {'id': '1'},
                             'role': {'id': '1'},
                             'scope': {'domain': {'id': '1'}}}
    domain_role_assignment1 = role_assignments.RoleAssignment(
        role_assignments.RoleAssignmentManager, role_assignments_dict)
    role_assignments_dict = {'user': {'id': '2'},
                             'role': {'id': '2'},
                             'scope': {'domain': {'id': '1'}}}
    domain_role_assignment2 = role_assignments.RoleAssignment(
        role_assignments.RoleAssignmentManager, role_assignments_dict)
    role_assignments_dict = {'group': {'id': '1'},
                             'role': {'id': '2'},
                             'scope': {'domain': {'id': '1'}}}
    domain_role_assignment3 = role_assignments.RoleAssignment(
        role_assignments.RoleAssignmentManager, role_assignments_dict)
    role_assignments_dict = {'user': {'id': '3'},
                             'role': {'id': '2'},
                             'scope': {'domain': {'id': '1'}}}
    domain_role_assignment4 = role_assignments.RoleAssignment(
        role_assignments.RoleAssignmentManager, role_assignments_dict)
    TEST.role_assignments.add(proj_role_assignment1,
                              proj_role_assignment2,
                              proj_role_assignment3,
                              proj_role_assignment4,
                              domain_role_assignment1,
                              domain_role_assignment2,
                              domain_role_assignment3,
                              domain_role_assignment4)

    tenant_dict = {'id': "1",
                   'name': 'test_tenant',
                   'description': "a test tenant.",
                   'enabled': True,
                   'domain_id': '1',
                   'domain_name': 'test_domain'}
    tenant_dict_2 = {'id': "2",
                     'name': 'disabled_tenant',
                     'description': "a disabled test tenant.",
                     'enabled': False,
                     'domain_id': '2',
                     'domain_name': 'disabled_domain'}
    tenant_dict_3 = {'id': "3",
                     'name': '\u4e91\u89c4\u5219',
                     'description': "an unicode-named tenant.",
                     'enabled': True,
                     'domain_id': '2',
                     'domain_name': 'disabled_domain'}
    tenant = tenants.Tenant(tenants.TenantManager, tenant_dict)
    disabled_tenant = tenants.Tenant(tenants.TenantManager, tenant_dict_2)
    tenant_unicode = tenants.Tenant(tenants.TenantManager, tenant_dict_3)

    TEST.tenants.add(tenant, disabled_tenant, tenant_unicode)
    TEST.tenant = tenant  # Your "current" tenant

    tomorrow = datetime_safe.datetime.now() + timedelta(days=1)
    expiration = tomorrow.isoformat()

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

    scoped_access_info = access.AccessInfo.factory(resp=None,
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
    unscoped_access_info = access.AccessInfo.factory(resp=None,
                                                     body=unscoped_token_dict)

    scoped_token = auth_user.Token(scoped_access_info)
    unscoped_token = auth_user.Token(unscoped_access_info)
    TEST.tokens.add(scoped_token, unscoped_token)
    TEST.token = scoped_token  # your "current" token.
    TEST.tokens.scoped_token = scoped_token
    TEST.tokens.unscoped_token = unscoped_token

    idp_dict_1 = {'id': 'idp_1',
                  'description': 'identity provider 1',
                  'enabled': True,
                  'remote_ids': ['rid_1', 'rid_2']}
    idp_1 = identity_providers.IdentityProvider(
        identity_providers.IdentityProviderManager,
        idp_dict_1, loaded=True)
    idp_dict_2 = {'id': 'idp_2',
                  'description': 'identity provider 2',
                  'enabled': True,
                  'remote_ids': ['rid_3', 'rid_4']}
    idp_2 = identity_providers.IdentityProvider(
        identity_providers.IdentityProviderManager,
        idp_dict_2, loaded=True)
    TEST.identity_providers.add(idp_1, idp_2)

    idp_mapping_dict = {
        "id": "mapping_1",
        "rules": [
            {
                "local": [
                    {
                        "user": {
                            "name": "{0}"
                        }
                    },
                    {
                        "group": {
                            "id": "0cd5e9"
                        }
                    }
                ],
                "remote": [
                    {
                        "type": "UserName"
                    },
                    {
                        "type": "orgPersonType",
                        "not_any_of": [
                            "Contractor",
                            "Guest"
                        ]
                    }
                ]
            }
        ]
    }
    idp_mapping = mappings.Mapping(
        mappings.MappingManager(None),
        idp_mapping_dict)
    TEST.idp_mappings.add(idp_mapping)

    idp_protocol_dict_1 = {'id': 'protocol_1',
                           'mapping_id': 'mapping_1'}
    idp_protocol = protocols.Protocol(
        protocols.ProtocolManager,
        idp_protocol_dict_1,
        loaded=True)
    TEST.idp_protocols.add(idp_protocol)

    app_cred_dict = {
        'id': 'ac1',
        'name': 'created',
        'secret': 'secret',
        'project': 'p1',
        'description': 'newly created application credential',
        'expires_at': None,
        'unrestricted': False,
        'roles': [
            {'id': 'r1',
             'name': 'Member',
             'domain': None},
            {'id': 'r2',
             'name': 'admin',
             'domain': None}
        ]
    }
    app_cred_create = application_credentials.ApplicationCredential(
        None, app_cred_dict)
    app_cred_dict = {
        'id': 'ac2',
        'name': 'detail',
        'project': 'p1',
        'description': 'existing application credential',
        'expires_at': None,
        'unrestricted': False,
        'roles': [
            {'id': 'r1',
             'name': 'Member',
             'domain': None},
            {'id': 'r2',
             'name': 'admin',
             'domain': None}
        ]
    }
    app_cred_detail = application_credentials.ApplicationCredential(
        None, app_cred_dict)
    TEST.application_credentials.add(app_cred_create, app_cred_detail)

    user_cred_dict = {
        'id': 'cred1',
        'user_id': '1',
        'type': 'totp',
        'blob': 'ONSWG4TFOQYTM43FMNZGK5BRGYFA',
        'project_id': 'project1'
    }
    user_cred_create = credentials.Credential(None, user_cred_dict)
    user_cred_dict = {
        'id': 'cred2',
        'user_id': '2',
        'type': 'totp',
        'blob': 'ONSWG4TFOQYTM43FMNZGK5BRGYFA',
        'project_id': 'project2'
    }
    user_cred_detail = credentials.Credential(None, user_cred_dict)
    TEST.credentials.add(user_cred_create, user_cred_detail)
