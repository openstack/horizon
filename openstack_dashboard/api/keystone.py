# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Openstack, LLC
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
import urlparse
from pkg_resources import get_distribution

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from keystoneclient import service_catalog
from keystoneclient.v2_0 import client as keystone_client
from keystoneclient.v2_0 import tokens

from openstack_auth.backend import KEYSTONE_CLIENT_ATTR

from horizon import exceptions

from openstack_dashboard.api import base


LOG = logging.getLogger(__name__)
DEFAULT_ROLE = None


class Service(base.APIDictWrapper):
    """ Wrapper for a dict based on the service data from keystone. """
    _attrs = ['id', 'type', 'name']

    def __init__(self, service, *args, **kwargs):
        super(Service, self).__init__(service, *args, **kwargs)
        self.url = service['endpoints'][0]['internalURL']
        self.host = urlparse.urlparse(self.url).hostname
        self.region = service['endpoints'][0]['region']
        self.disabled = None

    def __unicode__(self):
        if(self.type == "identity"):
            return _("%(type)s (%(backend)s backend)") \
                     % {"type": self.type,
                        "backend": keystone_backend_name()}
        else:
            return self.type

    def __repr__(self):
        return "<Service: %s>" % unicode(self)


def _get_endpoint_url(request, endpoint_type, catalog=None):
    if getattr(request.user, "service_catalog", None):
        return base.url_for(request,
                            service_type='identity',
                            endpoint_type=endpoint_type)
    return request.session.get('region_endpoint',
                               getattr(settings, 'OPENSTACK_KEYSTONE_URL'))


def keystoneclient(request, admin=False):
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

    Calls requiring the admin endpoint should have ``admin=True`` passed in
    as a keyword argument.

    The client is cached so that subsequent API calls during the same
    request/response cycle don't have to be re-authenticated.
    """
    user = request.user
    if admin:
        if not user.is_superuser:
            raise exceptions.NotAuthorized
        endpoint_type = 'adminURL'
    else:
        endpoint_type = getattr(settings,
                                'OPENSTACK_ENDPOINT_TYPE',
                                'internalURL')

    # Take care of client connection caching/fetching a new client.
    # Admin vs. non-admin clients are cached separately for token matching.
    cache_attr = "_keystoneclient_admin" if admin else KEYSTONE_CLIENT_ATTR
    if hasattr(request, cache_attr) and (not user.token.id
            or getattr(request, cache_attr).auth_token == user.token.id):
        LOG.debug("Using cached client for token: %s" % user.token.id)
        conn = getattr(request, cache_attr)
    else:
        endpoint = _get_endpoint_url(request, endpoint_type)
        insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
        LOG.debug("Creating a new keystoneclient connection to %s." % endpoint)

        conn = keystone_client.Client(
            token=user.token.id, endpoint=endpoint,
            original_ip=request.environ.get('REMOTE_ADDR', ''),
            insecure=insecure)
        setattr(request, cache_attr, conn)
    return conn


def tenant_create(request, tenant_name, description, enabled):
    return keystoneclient(request, admin=True).tenants.create(tenant_name,
                                                              description,
                                                              enabled)


def tenant_get(request, tenant_id, admin=False):
    return keystoneclient(request, admin=admin).tenants.get(tenant_id)


def tenant_delete(request, tenant_id):
    keystoneclient(request, admin=True).tenants.delete(tenant_id)


def tenant_list(request, admin=False):
    return keystoneclient(request, admin=admin).tenants.list()


def tenant_update(request, tenant_id, tenant_name, description, enabled):
    return keystoneclient(request, admin=True).tenants.update(tenant_id,
                                                              tenant_name,
                                                              description,
                                                              enabled)


def token_create_scoped(request, tenant, token):
    '''
    Creates a scoped token using the tenant id and unscoped token; retrieves
    the service catalog for the given tenant.
    '''
    if hasattr(request, '_keystone'):
        del request._keystone
    c = keystoneclient(request)
    raw_token = c.tokens.authenticate(tenant_id=tenant,
                                      token=token,
                                      return_raw=True)
    c.service_catalog = service_catalog.ServiceCatalog(raw_token)
    if request.user.is_superuser:
        c.management_url = c.service_catalog.url_for(service_type='identity',
                                                     endpoint_type='adminURL')
    else:
        endpoint_type = getattr(settings,
                                'OPENSTACK_ENDPOINT_TYPE',
                                'internalURL')
        c.management_url = c.service_catalog.url_for(
                service_type='identity', endpoint_type=endpoint_type)
    scoped_token = tokens.Token(tokens.TokenManager, raw_token)
    return scoped_token


def user_list(request, tenant_id=None):
    return keystoneclient(request, admin=True).users.list(tenant_id=tenant_id)


def user_create(request, user_id, email, password, tenant_id, enabled):
    return keystoneclient(request, admin=True).users.create(user_id,
                                                            password,
                                                            email,
                                                            tenant_id,
                                                            enabled)


def user_delete(request, user_id):
    keystoneclient(request, admin=True).users.delete(user_id)


def user_get(request, user_id, admin=True):
    return keystoneclient(request, admin=admin).users.get(user_id)


def user_update(request, user, **data):
    return keystoneclient(request, admin=True).users.update(user, **data)


def user_update_enabled(request, user_id, enabled):
    return keystoneclient(request, admin=True).users.update_enabled(user_id,
                                                                    enabled)


def user_update_password(request, user_id, password, admin=True):
    return keystoneclient(request, admin=admin).users.update_password(user_id,
                                                                      password)


def user_update_tenant(request, user_id, tenant_id, admin=True):
    return keystoneclient(request, admin=admin).users.update_tenant(user_id,
                                                                    tenant_id)


def role_list(request):
    """ Returns a global list of available roles. """
    return keystoneclient(request, admin=True).roles.list()


def roles_for_user(request, user, project):
    return keystoneclient(request, admin=True).roles.roles_for_user(user,
                                                                    project)


def add_tenant_user_role(request, tenant_id, user_id, role_id):
    """ Adds a role for a user on a tenant. """
    return keystoneclient(request, admin=True).roles.add_user_role(user_id,
                                                                   role_id,
                                                                   tenant_id)


def remove_tenant_user_role(request, tenant_id, user_id, role_id):
    """ Removes a given single role for a user from a tenant. """
    client = keystoneclient(request, admin=True)
    client.roles.remove_user_role(user_id, role_id, tenant_id)


def remove_tenant_user(request, tenant_id, user_id):
    """ Removes all roles from a user on a tenant, removing them from it. """
    client = keystoneclient(request, admin=True)
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
            roles = keystoneclient(request, admin=True).roles.list()
        except:
            roles = []
            exceptions.handle(request)
        for role in roles:
            if role.id == default or role.name == default:
                DEFAULT_ROLE = role
                break
    return DEFAULT_ROLE


def list_ec2_credentials(request, user_id):
    return keystoneclient(request).ec2.list(user_id)


def create_ec2_credentials(request, user_id, tenant_id):
    return keystoneclient(request).ec2.create(user_id, tenant_id)


def get_user_ec2_credentials(request, user_id, access_token):
    return keystoneclient(request).ec2.get(user_id, access_token)


def keystone_can_edit_user():
    backend_settings = getattr(settings, "OPENSTACK_KEYSTONE_BACKEND", {})
    return backend_settings.get('can_edit_user', True)


def keystone_can_edit_project():
    backend_settings = getattr(settings, "OPENSTACK_KEYSTONE_BACKEND", {})
    return backend_settings.get('can_edit_project', True)


def keystone_backend_name():
    if hasattr(settings, "OPENSTACK_KEYSTONE_BACKEND"):
        return settings.OPENSTACK_KEYSTONE_BACKEND['name']
    else:
        return 'unknown'
