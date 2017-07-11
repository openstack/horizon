# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import uuid

from django.utils import datetime_safe
from keystoneauth1.access import access
from keystoneauth1.access import service_catalog
from keystoneclient.v2_0 import roles
from keystoneclient.v2_0 import tenants
from keystoneclient.v2_0 import users


class TestDataContainer(object):
    """Arbitrary holder for test data in an object-oriented fashion."""
    pass


def generate_test_data():
    '''Builds a set of test_data data as returned by Keystone V2.'''
    test_data = TestDataContainer()

    keystone_service = {
        'type': 'identity',
        'name': 'keystone',
        'endpoints_links': [],
        'endpoints': [
            {
                'region': 'RegionOne',
                'adminURL': 'http://admin.localhost:35357/v2.0',
                'internalURL': 'http://internal.localhost:5000/v2.0',
                'publicURL': 'http://public.localhost:5000/v2.0'
            }
        ]
    }

    # Users
    user_dict = {'id': uuid.uuid4().hex,
                 'name': 'gabriel',
                 'email': 'gabriel@example.com',
                 'password': 'swordfish',
                 'token': '',
                 'enabled': True}
    test_data.user = users.User(None, user_dict, loaded=True)

    # Tenants
    tenant_dict_1 = {'id': uuid.uuid4().hex,
                     'name': 'tenant_one',
                     'description': '',
                     'enabled': True}
    tenant_dict_2 = {'id': uuid.uuid4().hex,
                     'name': 'tenant_two',
                     'description': '',
                     'enabled': False}
    test_data.tenant_one = tenants.Tenant(None, tenant_dict_1, loaded=True)
    test_data.tenant_two = tenants.Tenant(None, tenant_dict_2, loaded=True)

    nova_service = {
        'type': 'compute',
        'name': 'nova',
        'endpoint_links': [],
        'endpoints': [
            {
                'region': 'RegionOne',
                'adminURL': ('http://nova-admin.localhost:8774/v2.0/%s'
                             % (tenant_dict_1['id'])),
                'internalURL': ('http://nova-internal.localhost:8774/v2.0/%s'
                                % (tenant_dict_1['id'])),
                'publicURL': ('http://nova-public.localhost:8774/v2.0/%s'
                              % (tenant_dict_1['id']))
            },
            {
                'region': 'RegionTwo',
                'adminURL': ('http://nova2-admin.localhost:8774/v2.0/%s'
                             % (tenant_dict_1['id'])),
                'internalURL': ('http://nova2-internal.localhost:8774/v2.0/%s'
                                % (tenant_dict_1['id'])),
                'publicURL': ('http://nova2-public.localhost:8774/v2.0/%s'
                              % (tenant_dict_1['id']))
            }
        ]
    }

    # Roles
    role_dict = {'id': uuid.uuid4().hex,
                 'name': 'Member'}
    test_data.role = roles.Role(roles.RoleManager, role_dict)

    # Tokens
    tomorrow = datetime_safe.datetime.now() + datetime.timedelta(days=1)
    expiration = datetime_safe.datetime.isoformat(tomorrow)

    scoped_token_dict = {
        'access': {
            'token': {
                'id': uuid.uuid4().hex,
                'expires': expiration,
                'tenant': tenant_dict_1,
                'tenants': [tenant_dict_1, tenant_dict_2]},
            'user': {
                'id': user_dict['id'],
                'name': user_dict['name'],
                'roles': [role_dict]},
            'serviceCatalog': [keystone_service, nova_service]
        }
    }

    test_data.scoped_access_info = access.create(
        resp=None,
        body=scoped_token_dict)

    unscoped_token_dict = {
        'access': {
            'token': {
                'id': uuid.uuid4().hex,
                'expires': expiration},
            'user': {
                'id': user_dict['id'],
                'name': user_dict['name'],
                'roles': [role_dict]},
            'serviceCatalog': [keystone_service]
        }
    }
    test_data.unscoped_access_info = access.create(
        resp=None,
        body=unscoped_token_dict)

    # Service Catalog
    test_data.service_catalog = service_catalog.ServiceCatalogV2(
        [keystone_service, nova_service])

    return test_data
