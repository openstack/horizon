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
Forms used for Horizon's auth mechanisms.
"""

import logging

from django import shortcuts
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.translation import ugettext as _
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
    region = forms.ChoiceField(label=_("Region"), required=False)
    username = forms.CharField(label=_("User Name"))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput(render_value=False))

    def __init__(self, *args, **kwargs):
        super(Login, self).__init__(*args, **kwargs)
        # FIXME(gabriel): When we switch to region-only settings, we can
        # remove this default region business.
        default_region = (settings.OPENSTACK_KEYSTONE_URL, "Default Region")
        regions = getattr(settings, 'AVAILABLE_REGIONS', [default_region])
        self.fields['region'].choices = regions
        if len(regions) == 1:
            self.fields['region'].initial = default_region[0]
            self.fields['region'].widget = forms.widgets.HiddenInput()

    def handle(self, request, data):
        if 'user_name' in request.session:
            if request.session['user_name'] != data['username']:
                # To avoid reusing another user's session, create a
                # new, empty session if the existing session
                # corresponds to a different authenticated user.
                request.session.flush()
        # Always cycle the session key when viewing the login form to
        # prevent session fixation
        request.session.cycle_key()

        # For now we'll allow fallback to OPENSTACK_KEYSTONE_URL if the
        # form post doesn't include a region.
        endpoint = data.get('region', None) or settings.OPENSTACK_KEYSTONE_URL
        region_name = dict(self.fields['region'].choices)[endpoint]
        request.session['region_endpoint'] = endpoint
        request.session['region_name'] = region_name

        redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, "")

        if data.get('tenant', None):
            try:
                token = api.token_create(request,
                                         data.get('tenant'),
                                         data['username'],
                                         data['password'])
                tenants = api.tenant_list_for_token(request, token.id)
            except:
                msg = _('Unable to authenticate for that project.')
                exceptions.handle(request,
                                  message=msg,
                                  escalate=True)
            _set_session_data(request, token)
            user = users.get_user_from_request(request)
            redirect = redirect_to or base.Horizon.get_user_home(user)
            return shortcuts.redirect(redirect)

        elif data.get('username', None):
            try:
                unscoped_token = api.token_create(request,
                                                  '',
                                                  data['username'],
                                                  data['password'])
            except keystone_exceptions.Unauthorized:
                exceptions.handle(request,
                                  _('Invalid user name or password.'))
            except:
                # If we get here we don't want to show a stack trace to the
                # user. However, if we fail here, there may be bad session
                # data that's been cached already.
                request.user_logout()
                exceptions.handle(request,
                                  message=_("An error occurred authenticating."
                                            " Please try again later."),
                                  escalate=True)

            # Unscoped token
            request.session['unscoped_token'] = unscoped_token.id
            request.user.username = data['username']

            # Get the tenant list, and log in using first tenant
            # FIXME (anthony): add tenant chooser here?
            try:
                tenants = api.tenant_list_for_token(request, unscoped_token.id)
            except:
                exceptions.handle(request)
                tenants = []

            # Abort if there are no valid tenants for this user
            if not tenants:
                messages.error(request,
                               _('You are not authorized for any projects.') %
                                {"user": data['username']},
                               extra_tags="login")
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
                                                    unscoped_token.id)
                    break
                except:
                    # This will continue for recognized Unauthorized
                    # exceptions from keystoneclient.
                    exceptions.handle(request, ignore=True)
                    token = None
            if token is None:
                raise exceptions.NotAuthorized(
                    _("You are not authorized for any available projects."))

            _set_session_data(request, token)
            user = users.get_user_from_request(request)
        redirect = redirect_to or base.Horizon.get_user_home(user)
        return shortcuts.redirect(redirect)


class LoginWithTenant(Login):
    """
    Exactly like :class:`.Login` but includes the tenant id as a field
    so that the process of choosing a default tenant is bypassed.
    """
    region = forms.ChoiceField(required=False)
    username = forms.CharField(max_length="20",
                       widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    tenant = forms.CharField(widget=forms.HiddenInput())
