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

"""
Forms used for Horizon's auth mechanisms.
"""

import logging

from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext as _
from openstackx.api import exceptions as api_exceptions
from keystoneclient import exceptions as keystone_exceptions

from horizon import api
from horizon import base
from horizon import exceptions
from horizon import forms
from horizon import users


LOG = logging.getLogger(__name__)


def _set_session_data(request, token):
    request.session['serviceCatalog'] = token.serviceCatalog
    request.session['tenant'] = token.tenant['name']
    request.session['tenant_id'] = token.tenant['id']
    request.session['token'] = token.id
    request.session['user_name'] = token.user['name']
    request.session['user_id'] = token.user['id']
    request.session['roles'] = token.user['roles']


class Login(forms.SelfHandlingForm):
    """ Form used for logging in a user.

    Handles authentication with Keystone, choosing a tenant, and fetching
    a scoped token token for that tenant. Redirects to the URL returned
    by :meth:`horizon.get_user_home` if successful.

    Subclass of :class:`~horizon.forms.SelfHandlingForm`.
    """
    username = forms.CharField(max_length="20", label=_("User Name"))
    password = forms.CharField(max_length="20", label=_("Password"),
                               widget=forms.PasswordInput(render_value=False))

    def handle(self, request, data):
        try:
            if data.get('tenant', None):
                token = api.token_create(request,
                                         data.get('tenant'),
                                         data['username'],
                                         data['password'])

                tenants = api.tenant_list_for_token(request, token.id)
                tenant = None
                for t in tenants:
                    if t.id == data.get('tenant'):
                        tenant = t
                _set_session_data(request, token)
                user = users.get_user_from_request(request)
                return shortcuts.redirect(base.Horizon.get_user_home(user))

            elif data.get('username', None):
                try:
                    token = api.token_create(request,
                                             '',
                                             data['username'],
                                             data['password'])
                except keystone_exceptions.Unauthorized:
                    messages.error(request, _('Bad user name or password.'))
                    return

                # Unscoped token
                request.session['unscoped_token'] = token.id
                request.user.username = data['username']

                # Get the tenant list, and log in using first tenant
                # FIXME (anthony): add tenant chooser here?
                tenants = api.tenant_list_for_token(request, token.id)

                # Abort if there are no valid tenants for this user
                if not tenants:
                    messages.error(request,
                                   _('No tenants present for user: %(user)s') %
                                    {"user": data['username']})
                    return

                # Create a token.
                # NOTE(gabriel): Keystone can return tenants that you're
                # authorized to administer but not to log into as a user, so in
                # the case of an Unauthorized error we should iterate through
                # the tenants until one succeeds or we've failed them all.
                while tenants:
                    tenant = tenants.pop()
                    try:
                        token = api.token_create_scoped(request,
                                                        tenant.id,
                                                        token.id)
                        break
                    except api_exceptions.Unauthorized as e:
                        token = None
                if token is None:
                    raise exceptions.NotAuthorized(
                        _("You are not authorized for any available tenants."))

                _set_session_data(request, token)
                user = users.get_user_from_request(request)
                return shortcuts.redirect(base.Horizon.get_user_home(user))

        except api_exceptions.Unauthorized as e:
            msg = _('Error authenticating: %s') % e.message
            LOG.exception(msg)
            messages.error(request, msg)
        except api_exceptions.ApiException as e:
            messages.error(request,
                           _('Error authenticating with keystone: %s') %
                           e.message)


class LoginWithTenant(Login):
    """
    Exactly like :class:`.Login` but includes the tenant id as a field
    so that the process of choosing a default tenant is bypassed.
    """
    username = forms.CharField(max_length="20",
                       widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    tenant = forms.CharField(widget=forms.HiddenInput())
