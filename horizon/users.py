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
"""
Classes and methods related to user handling in Horizon.
"""

import logging

from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions


LOG = logging.getLogger(__name__)


def get_user_from_request(request):
    """ Checks the current session and returns a :class:`~horizon.users.User`.

    If the session contains user data the User will be treated as
    authenticated and the :class:`~horizon.users.User` will have all
    its attributes set.

    If not, the :class:`~horizon.users.User` will have no attributes set.

    If the session contains invalid data,
    :exc:`~horizon.exceptions.NotAuthorized` will be raised.
    """
    if 'user_id' not in request.session:
        return User()
    try:
        return User(id=request.session['user_id'],
                    token=request.session['token'],
                    user=request.session['user_name'],
                    tenant_id=request.session['tenant_id'],
                    tenant_name=request.session['tenant'],
                    service_catalog=request.session['serviceCatalog'],
                    roles=request.session['roles'],
                    request=request)
    except KeyError:
        # If any of those keys are missing from the session it is
        # overwhelmingly likely that we're dealing with an outdated session.
        LOG.exception("Error while creating User from session.")
        request.user_logout()
        raise exceptions.NotAuthorized(_("Your session has expired. "
                                         "Please log in again."))


class LazyUser(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_user'):
            request._cached_user = get_user_from_request(request)
        return request._cached_user


class User(object):
    """ The main user class which Horizon expects.

    .. attribute:: token

        The id of the Keystone token associated with the current user/tenant.

    .. attribute:: username

        The name of the current user.

    .. attribute:: tenant_id

        The id of the Keystone tenant for the current user/token.

    .. attribute:: tenant_name

        The name of the Keystone tenant for the current user/token.

    .. attribute:: service_catalog

        The ``ServiceCatalog`` data returned by Keystone.

    .. attribute:: roles

        A list of dictionaries containing role names and ids as returned
        by Keystone.

    .. attribute:: admin

        Boolean value indicating whether or not this user has admin
        privileges. Internally mapped to :meth:`horizon.users.User.is_admin`.
    """
    def __init__(self, id=None, token=None, user=None, tenant_id=None,
                    service_catalog=None, tenant_name=None, roles=None,
                    authorized_tenants=None, request=None):
        self.id = id
        self.token = token
        self.username = user
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.service_catalog = service_catalog
        self.roles = roles or []
        self._authorized_tenants = authorized_tenants
        # Store the request for lazy fetching of auth'd tenants
        self._request = request

    def is_authenticated(self):
        """
        Evaluates whether this :class:`.User` instance has been authenticated.
        Returns ``True`` or ``False``.
        """
        # TODO: deal with token expiration
        return self.token

    @property
    def admin(self):
        return self.is_admin()

    def is_admin(self):
        """
        Evaluates whether this user has admin privileges. Returns
        ``True`` or ``False``.
        """
        for role in self.roles:
            if role['name'].lower() == 'admin':
                return True
        return False

    def get_and_delete_messages(self):
        """
        Placeholder function for parity with
        ``django.contrib.auth.models.User``.
        """
        return []

    @property
    def authorized_tenants(self):
        if self.is_authenticated() and self._authorized_tenants is None:
            try:
                token = self._request.session.get("unscoped_token", self.token)
                authd = api.tenant_list_for_token(self._request, token)
            except:
                authd = []
                LOG.exception('Could not retrieve tenant list.')
            self._authorized_tenants = authd
        return self._authorized_tenants

    @authorized_tenants.setter
    def authorized_tenants(self, tenant_list):
        self._authorized_tenants = tenant_list
