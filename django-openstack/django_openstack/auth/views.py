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

from django import template
from django import shortcuts
from django.contrib import messages

from django_openstack import api
from django_openstack import forms
from openstackx.api import exceptions as api_exceptions


LOG = logging.getLogger('django_openstack.auth')


class Login(forms.SelfHandlingForm):
    username = forms.CharField(max_length="20", label="User Name")
    password = forms.CharField(max_length="20", label="Password",
                               widget=forms.PasswordInput(render_value=False))

    def handle(self, request, data):

        def is_admin(token):
            for role in token.user['roles']:
                if role['name'].lower() == 'admin':
                    return True
            return False

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
                # We are logging in without tenant
                token = api.token_create(request,
                                         '',
                                         data['username'],
                                         data['password'])

                # Unscoped token
                request.session['unscoped_token'] = token.id

                def get_first_tenant_for_user():
                    tenants = api.tenant_list_for_token(request, token.id)
                    return tenants[0] if len(tenants) else None

                # Get the tenant list, and log in using first tenant
                # FIXME (anthony): add tenant chooser here?
                tenant = get_first_tenant_for_user()

                # Abort if there are no valid tenants for this user
                if not tenant:
                    messages.error(request, 'No tenants present for user: %s' %
                                            data['username'])
                    return

                # Create a token
                token = api.token_create_scoped_with_token(request,
                                         data.get('tenant', tenant.id),
                                         token.id)

            request.session['admin'] = is_admin(token)
            request.session['serviceCatalog'] = token.serviceCatalog

            LOG.info('Login form for user "%s". Service Catalog data:\n%s' %
                     (data['username'], token.serviceCatalog))

            request.session['tenant'] = tenant.name
            request.session['tenant_id'] = tenant.id
            request.session['token'] = token.id
            request.session['user'] = data['username']

            return shortcuts.redirect('dash_overview')

        except api_exceptions.Unauthorized as e:
            msg = 'Error authenticating: %s' % e.message
            LOG.exception(msg)
            messages.error(request, msg)
        except api_exceptions.ApiException as e:
            messages.error(request, 'Error authenticating with keystone: %s' %
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

    return shortcuts.render_to_response('switch_tenants.html', {
        'to_tenant': tenant_id,
        'form': form,
    }, context_instance=template.RequestContext(request))


def logout(request):
    request.session.clear()
    return shortcuts.redirect('splash')
