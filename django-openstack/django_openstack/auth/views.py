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
        try:
            token = api.token_create(request,
                                     data.get('tenant', ''),
                                     data['username'],
                                     data['password'])
            info = api.token_info(request, token)

            request.session['token'] = token.id
            request.session['user'] = info['user']
            request.session['tenant'] = data.get('tenant', info['tenant'])
            request.session['admin'] = info['admin']
            request.session['serviceCatalog'] = token.serviceCatalog
            LOG.info('Login form for user "%s". Service Catalog data:\n%s' %
                     (data['username'], token.serviceCatalog))

            return shortcuts.redirect('dash_overview')

        except api_exceptions.Unauthorized as e:
            msg = 'Error authenticating: %s' % e.message
            LOG.error(msg, exc_info=True)
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
