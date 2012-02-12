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

import logging

from django.conf import settings

from keystoneclient import service_catalog
from keystoneclient.v2_0 import client as keystone_client
from keystoneclient.v2_0 import tokens

from horizon import exceptions


LOG = logging.getLogger(__name__)
DEFAULT_ROLE = None


def _get_endpoint_url(request):
    return request.session.get('region_endpoint',
                               getattr(settings, 'OPENSTACK_KEYSTONE_URL'))


def keystoneclient(request, username=None, password=None, tenant_id=None,
                   token_id=None, endpoint=None, endpoint_type=None):
    """Returns a client connected to the Keystone backend.

    Several forms of authentication are supported:

        * Username + password -> Unscoped authentication
        * Username + password + tenant id -> Scoped authentication
        * Unscoped token -> Unscoped authentication
        * Unscoped token + tenant id -> Scoped authentication
        * Scoped token -> Scoped authentication

    Available services and data from the backend will vary depending on
    whether the authentication was scoped or unscoped.

    Lazy authentication if an ``endpoint`` parameter is provided.

    The client is cached so that subsequent API calls during the same
    request/response cycle don't have to be re-authenticated.
    """

    # Take care of client connection caching/fetching a new client
    user = request.user
    if hasattr(request, '_keystone') and \
            request._keystone.auth_token == token_id:
        LOG.debug("Using cached client for token: %s" % user.token)
        conn = request._keystone
    else:
        LOG.debug("Creating a new client connection with endpoint: %s."
                  % endpoint)
        conn = keystone_client.Client(username=username or user.username,
                                      password=password,
                                      tenant_id=tenant_id or user.tenant_id,
                                      token=token_id or user.token,
                                      auth_url=_get_endpoint_url(request),
                                      endpoint=endpoint)
        request._keystone = conn

    # Fetch the correct endpoint for the user type
    catalog = getattr(conn, 'service_catalog', None)
    if catalog and "serviceCatalog" in catalog.catalog.keys():
        if endpoint_type:
            endpoint = catalog.url_for(service_type='identity',
                                       endpoint_type=endpoint_type)
        elif user.is_admin():
            endpoint = catalog.url_for(service_type='identity',
                                       endpoint_type='adminURL')
        else:
            endpoint = catalog.url_for(service_type='identity',
                                       endpoint_type='publicURL')
    else:
        endpoint = _get_endpoint_url(request)
    conn.management_url = endpoint

    return conn


def tenant_create(request, tenant_name, description, enabled):
    return keystoneclient(request).tenants.create(tenant_name,
                                                  description,
                                                  enabled)


def tenant_get(request, tenant_id):
    return keystoneclient(request).tenants.get(tenant_id)


def tenant_delete(request, tenant_id):
    keystoneclient(request).tenants.delete(tenant_id)


def tenant_list(request):
    return keystoneclient(request).tenants.list()


def tenant_update(request, tenant_id, tenant_name, description, enabled):
    return keystoneclient(request).tenants.update(tenant_id,
                                                  tenant_name,
                                                  description,
                                                  enabled)


def tenant_list_for_token(request, token, endpoint_type=None):
    c = keystoneclient(request,
                       token_id=token,
                       endpoint=_get_endpoint_url(request),
                       endpoint_type=endpoint_type)
    return c.tenants.list()


def token_create(request, tenant, username, password):
    '''
    Creates a token using the username and password provided. If tenant
    is provided it will retrieve a scoped token and the service catalog for
    the given tenant. Otherwise it will return an unscoped token and without
    a service catalog.
    '''
    c = keystoneclient(request,
                       username=username,
                       password=password,
                       tenant_id=tenant,
                       endpoint=_get_endpoint_url(request))
    token = c.tokens.authenticate(username=username,
                                  password=password,
                                  tenant_id=tenant)
    return token


def token_create_scoped(request, tenant, token):
    '''
    Creates a scoped token using the tenant id and unscoped token; retrieves
    the service catalog for the given tenant.
    '''
    if hasattr(request, '_keystone'):
        del request._keystone
    c = keystoneclient(request,
                       tenant_id=tenant,
                       token_id=token,
                       endpoint=_get_endpoint_url(request))
    raw_token = c.tokens.authenticate(tenant_id=tenant,
                                      token=token,
                                      return_raw=True)
    c.service_catalog = service_catalog.ServiceCatalog(raw_token)
    if request.user.is_admin():
        c.management_url = c.service_catalog.url_for(service_type='identity',
                                                     endpoint_type='adminURL')
    else:
        c.management_url = c.service_catalog.url_for(service_type='identity',
                                                     endpoint_type='publicURL')
    scoped_token = tokens.Token(tokens.TokenManager, raw_token)
    return scoped_token


def user_list(request, tenant_id=None):
    return keystoneclient(request).users.list(tenant_id=tenant_id)


def user_create(request, user_id, email, password, tenant_id, enabled):
    return keystoneclient(request).users.create(user_id,
                                                password,
                                                email,
                                                tenant_id,
                                                enabled)


def user_delete(request, user_id):
    keystoneclient(request).users.delete(user_id)


def user_get(request, user_id):
    return keystoneclient(request).users.get(user_id)


def user_update_email(request, user_id, email):
    return keystoneclient(request).users.update_email(user_id, email)


def user_update_enabled(request, user_id, enabled):
    return keystoneclient(request).users.update_enabled(user_id, enabled)


def user_update_password(request, user_id, password):
    return keystoneclient(request).users.update_password(user_id, password)


def user_update_tenant(request, user_id, tenant_id):
    return keystoneclient(request).users.update_tenant(user_id, tenant_id)


def role_list(request):
    """ Returns a global list of available roles. """
    return keystoneclient(request).roles.list()


def add_tenant_user_role(request, tenant_id, user_id, role_id):
    """ Adds a role for a user on a tenant. """
    return keystoneclient(request).roles.add_user_role(user_id,
                                                       role_id,
                                                       tenant_id)


def remove_tenant_user(request, tenant_id, user_id):
    """ Removes all roles from a user on a tenant, removing them from it. """
    client = keystoneclient(request)
    roles = client.roles.roles_for_user(user_id, tenant_id)
    for role in roles:
        client.roles.remove_user_role(user_id, role.id, tenant_id)


def get_default_role(request):
    """
    Gets the default role object from Keystone and saves it as a global
    since this is configured in settings and should not change from request
    to request. Supports lookup by name or id.
    """
    global DEFAULT_ROLE
    default = getattr(settings, "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
    if default and DEFAULT_ROLE is None:
        try:
            roles = keystoneclient(request).roles.list()
        except:
            exceptions.handle(request)
        for role in roles:
            if role.id == default or role.name == default:
                DEFAULT_ROLE = role
                break
    return DEFAULT_ROLE
