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

import logging

from django.conf import settings
from django import template
from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext as _

from django_openstack import api
from django_openstack import exceptions
from django_openstack import forms
from openstackx.api import exceptions as api_exceptions
from django_openstack import exceptions


LOG = logging.getLogger('django_openstack.auth')


def _is_admin(token):
    for role in token.user['roles']:
        if role['name'].lower() == 'admin':
            return True
    return False


def _set_session_data(request, token):
    request.session['admin'] = _is_admin(token)
    request.session['serviceCatalog'] = token.serviceCatalog
    request.session['tenant'] = token.tenant['name']
    request.session['tenant_id'] = token.tenant['id']
    request.session['token'] = token.id
    request.session['user'] = token.user['name']


class Login(forms.SelfHandlingForm):
    username = forms.CharField(max_length="20", label=_("User Name"))
    password = forms.CharField(max_length="20", label=_("Password"),
                               widget=forms.PasswordInput(render_value=False))

    def handle(self, request, data):
        try:
            if data.get('tenant'):
                token = api.token_create(request,
                                         data.get('tenant'),
                                         data['username'],
                                         data['password'])

                tenants = api.tenant_list_for_token(request, token.id)
                tenant = None
                for t in tenants:
                    if t.id == data.get('tenant'):
                        tenant = t
            else:
                token = api.token_create(request,
                                         '',
                                         data['username'],
                                         data['password'])

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
                    except exceptions.Unauthorized as e:
                        token = None
                if token is None:
                    raise exceptions.Unauthorized(
                        _("You are not authorized for any available tenants."))

            LOG.info('Login form for user "%s". Service Catalog data:\n%s' %
                     (data['username'], token.serviceCatalog))
            _set_session_data(request, token)

            return shortcuts.redirect('dash_overview')

        except api_exceptions.Unauthorized as e:
            msg = _('Error authenticating: %s') % e.message
            LOG.exception(msg)
            messages.error(request, msg)
        except api_exceptions.ApiException as e:
            messages.error(request,
                           _('Error authenticating with keystone: %s') %
                           e.message)


class LoginWithTenant(Login):
    username = forms.CharField(max_length="20",
                       widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    tenant = forms.CharField(widget=forms.HiddenInput())


def login(request):
    if request.user and request.user.is_authenticated():
        if request.user.is_admin():
            return shortcuts.redirect('syspanel_overview')
        else:
            return shortcuts.redirect('dash_overview')

    form, handled = Login.maybe_handle(request)
    if handled:
        return handled

    return shortcuts.render_to_response('splash.html', {
        'form': form,
    }, context_instance=template.RequestContext(request))


def switch_tenants(request, tenant_id):
    form, handled = LoginWithTenant.maybe_handle(
            request, initial={'tenant': tenant_id,
                              'username': request.user.username})
    if handled:
        return handled

    unscoped_token = request.session.get('unscoped_token', None)
    if unscoped_token:
        try:
            token = api.token_create_scoped(request,
                                            tenant_id,
                                            unscoped_token)
            _set_session_data(request, token)
            return shortcuts.redirect('dash_overview')
        except exceptions.Unauthorized as e:
            messages.error(_("You are not authorized for that tenant."))

    return shortcuts.render_to_response('switch_tenants.html', {
        'to_tenant': tenant_id,
        'form': form,
    }, context_instance=template.RequestContext(request))


def logout(request):
    request.session.clear()
    return shortcuts.redirect('splash')
