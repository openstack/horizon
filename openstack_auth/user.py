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
import logging

from django.contrib.auth import models
from django.db import models as db_models
from keystoneauth1 import exceptions as keystone_exceptions
import six

from openstack_auth import utils


LOG = logging.getLogger(__name__)


def set_session_from_user(request, user):
    request.session['token'] = user.token
    request.session['user_id'] = user.id
    request.session['region_endpoint'] = user.endpoint
    request.session['services_region'] = user.services_region
    # Update the user object cached in the request
    request._cached_user = user
    request.user = user


def unset_session_user_variables(request):
    request.session['token'] = None
    request.session['user_id'] = None
    request.session['region_endpoint'] = None
    request.session['services_region'] = None
    # Update the user object cached in the request
    request._cached_user = None
    request.user = None


def create_user_from_token(request, token, endpoint, services_region=None):
    # if the region is provided, use that, otherwise use the preferred region
    svc_region = services_region or \
        utils.default_services_region(token.serviceCatalog, request, endpoint)
    return User(id=token.user['id'],
                token=token,
                user=token.user['name'],
                password_expires_at=token.user['password_expires_at'],
                user_domain_id=token.user_domain_id,
                # We need to consider already logged-in users with an old
                # version of Token without user_domain_name.
                user_domain_name=getattr(token, 'user_domain_name', None),
                project_id=token.project['id'],
                project_name=token.project['name'],
                domain_id=token.domain['id'],
                domain_name=token.domain['name'],
                enabled=True,
                service_catalog=token.serviceCatalog,
                roles=token.roles,
                endpoint=endpoint,
                services_region=svc_region,
                is_federated=getattr(token, 'is_federated', False),
                unscoped_token=getattr(token, 'unscoped_token',
                                       request.session.get('unscoped_token')))


class Token(object):
    """Encapsulates the AccessInfo object from keystoneclient.

    Token object provides a consistent interface for accessing the keystone
    token information and service catalog.

    Added for maintaining backward compatibility with horizon that expects
    Token object in the user object.
    """
    def __init__(self, auth_ref, unscoped_token=None):
        # User-related attributes
        user = {'id': auth_ref.user_id, 'name': auth_ref.username}
        data = getattr(auth_ref, '_data', {})
        expiration_date = data.get('token', {}).get('user', {})\
            .get('password_expires_at')
        user['password_expires_at'] = expiration_date
        self.user = user
        self.user_domain_id = auth_ref.user_domain_id
        self.user_domain_name = auth_ref.user_domain_name

        # Token-related attributes
        self.id = auth_ref.auth_token
        self.unscoped_token = unscoped_token
        self.expires = auth_ref.expires

        # Project-related attributes
        project = {}
        project['id'] = auth_ref.project_id
        project['name'] = auth_ref.project_name
        project['is_admin_project'] = getattr(auth_ref, 'is_admin_project',
                                              False)
        project['domain_id'] = getattr(auth_ref, 'project_domain_id', None)
        self.project = project
        self.tenant = self.project

        # Domain-related attributes
        domain = {}
        domain['id'] = auth_ref.domain_id
        domain['name'] = auth_ref.domain_name
        self.domain = domain

        # Federation-related attributes
        self.is_federated = auth_ref.is_federated
        self.roles = [{'name': role} for role in auth_ref.role_names]
        self.serviceCatalog = auth_ref.service_catalog.catalog


class User(models.AbstractBaseUser, models.AnonymousUser):
    """A User class with some extra special sauce for Keystone.

    In addition to the standard Django user attributes, this class also has
    the following:

    .. attribute:: token

        The Keystone token object associated with the current user/tenant.

        The token object is deprecated, user auth_ref instead.

    .. attribute:: tenant_id

        The id of the Keystone tenant for the current user/token.

        The tenant_id keyword argument is deprecated, use project_id instead.

    .. attribute:: tenant_name

        The name of the Keystone tenant for the current user/token.

        The tenant_name keyword argument is deprecated, use project_name
        instead.

    .. attribute:: project_id

        The id of the Keystone project for the current user/token.

    .. attribute:: project_name

        The name of the Keystone project for the current user/token.

    .. attribute:: service_catalog

        The ``ServiceCatalog`` data returned by Keystone.

    .. attribute:: roles

        A list of dictionaries containing role names and ids as returned
        by Keystone.

    .. attribute:: services_region

        A list of non-identity service endpoint regions extracted from the
        service catalog.

    .. attribute:: user_domain_id

        The domain id of the current user.

    .. attribute:: user_domain_name

        The domain name of the current user.

    .. attribute:: domain_id

        The id of the Keystone domain scoped for the current user/token.

    .. attribute:: is_federated

        Whether user is federated Keystone user. (Boolean)

    .. attribute:: unscoped_token

        Unscoped Keystone token.

    .. attribute:: password_expires_at

        Password expiration date. This attribute could be None when using
        keystone version < 3.0 or if the feature is not enabled in keystone.

    """

    keystone_user_id = db_models.CharField(primary_key=True, max_length=255)
    USERNAME_FIELD = 'keystone_user_id'

    def __init__(self, id=None, token=None, user=None, tenant_id=None,
                 service_catalog=None, tenant_name=None, roles=None,
                 authorized_tenants=None, endpoint=None, enabled=False,
                 services_region=None, user_domain_id=None,
                 user_domain_name=None, domain_id=None, domain_name=None,
                 project_id=None, project_name=None, is_federated=False,
                 unscoped_token=None, password=None, password_expires_at=None):
        self.id = id
        self.pk = id
        self.token = token
        self.keystone_user_id = id
        self.username = user
        self.user_domain_id = user_domain_id
        self.user_domain_name = user_domain_name
        self.domain_id = domain_id
        self.domain_name = domain_name
        self.project_id = project_id or tenant_id
        self.project_name = project_name or tenant_name
        self.service_catalog = service_catalog
        self._services_region = (
            services_region or
            utils.default_services_region(service_catalog)
        )
        self.roles = roles or []
        self.endpoint = endpoint
        self.enabled = enabled
        self._authorized_tenants = authorized_tenants
        self.is_federated = is_federated
        self.password_expires_at = password_expires_at

        # Unscoped token is used for listing user's project that works
        # for both federated and keystone user.
        self.unscoped_token = unscoped_token

        # List of variables to be deprecated.
        self.tenant_id = self.project_id
        self.tenant_name = self.project_name

        # Required by AbstractBaseUser
        self.password = None

    def __unicode__(self):
        return self.username

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.username)

    def is_token_expired(self, margin=None):
        """Determine if the token is expired.

        :returns:
          ``True`` if the token is expired, ``False`` if not, and
          ``None`` if there is no token set.

        :param margin:
           A security time margin in seconds before real expiration.
           Will return ``True`` if the token expires in less than ``margin``
           seconds of time.
           A default margin can be set by the TOKEN_TIMEOUT_MARGIN in the
           django settings.

        """
        if self.token is None:
            return None
        return not utils.is_token_valid(self.token, margin)

    @property
    def is_authenticated(self):
        """Checks for a valid authentication."""
        return self.token is not None and utils.is_token_valid(self.token)

    @property
    def is_anonymous(self):
        """Return if the user is not authenticated.

        :returns: ``True`` if not authenticated,``False`` otherwise.
        """
        return not self.is_authenticated

    @property
    def is_active(self):
        return self.enabled

    @property
    def is_superuser(self):
        """Evaluates whether this user has admin privileges.

        :returns: ``True`` or ``False``.
        """
        admin_roles = utils.get_admin_roles()
        user_roles = {role['name'].lower() for role in self.roles}
        return not admin_roles.isdisjoint(user_roles)

    @property
    def authorized_tenants(self):
        """Returns a memoized list of tenants this user may access."""
        if self.is_authenticated and self._authorized_tenants is None:
            endpoint = self.endpoint
            try:
                self._authorized_tenants = utils.get_project_list(
                    user_id=self.id,
                    auth_url=endpoint,
                    token=self.unscoped_token,
                    is_federated=self.is_federated)
            except (keystone_exceptions.ClientException,
                    keystone_exceptions.AuthorizationFailure):
                LOG.exception('Unable to retrieve project list.')
        return self._authorized_tenants or []

    @authorized_tenants.setter
    def authorized_tenants(self, tenant_list):
        self._authorized_tenants = tenant_list

    @property
    def services_region(self):
        return self._services_region

    @services_region.setter
    def services_region(self, region):
        self._services_region = region

    @property
    def available_services_regions(self):
        """Returns list of unique region name values in service catalog."""
        regions = []
        if self.service_catalog:
            for service in self.service_catalog:
                service_type = service.get('type')
                if service_type is None or service_type == 'identity':
                    continue
                for endpoint in service.get('endpoints', []):
                    region = utils.get_endpoint_region(endpoint)
                    if region not in regions:
                        regions.append(region)
        return regions

    def save(self, *args, **kwargs):
        # Presume we can't write to Keystone.
        pass

    def delete(self, *args, **kwargs):
        # Presume we can't write to Keystone.
        pass

    # Check for OR'd permission rules, check that user has one of the
    # required permission.
    def has_a_matching_perm(self, perm_list, obj=None):
        """Returns True if the user has one of the specified permissions.

        If object is passed, it checks if the user has any of the required
        perms for this object.
        """
        # If there are no permissions to check, just return true
        if not perm_list:
            return True
        # Check that user has at least one of the required permissions.
        for perm in perm_list:
            if self.has_perm(perm, obj):
                return True
        return False

    # Override the default has_perms method. Allowing for more
    # complex combinations of permissions.  Will check for logical AND of
    # all top level permissions.  Will use logical OR for all first level
    # tuples (check that use has one permissions in the tuple)
    #
    # Examples:
    #   Checks for all required permissions
    #   ('openstack.roles.admin', 'openstack.roles.L3-support')
    #
    #   Checks for admin AND (L2 or L3)
    #   ('openstack.roles.admin', ('openstack.roles.L3-support',
    #                              'openstack.roles.L2-support'),)
    def has_perms(self, perm_list, obj=None):
        """Returns True if the user has all of the specified permissions.

        Tuples in the list will possess the required permissions if
        the user has a permissions matching one of the elements of
        that tuple
        """
        # If there are no permissions to check, just return true
        if not perm_list:
            return True
        for perm in perm_list:
            if isinstance(perm, six.string_types):
                # check that the permission matches
                if not self.has_perm(perm, obj):
                    return False
            else:
                # check that a permission in the tuple matches
                if not self.has_a_matching_perm(perm, obj):
                    return False
        return True

    def time_until_expiration(self):
        """Returns the number of remaining days until user's password expires.

        Calculates the number days until the user must change their password,
        once the password expires the user will not able to log in until an
        admin changes its password.
        """
        if self.password_expires_at is not None:
            expiration_date = datetime.datetime.strptime(
                self.password_expires_at, "%Y-%m-%dT%H:%M:%S.%f")
            return expiration_date - datetime.datetime.now()

    class Meta(object):
        app_label = 'openstack_auth'
