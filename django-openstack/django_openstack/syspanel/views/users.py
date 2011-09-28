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

from django import shortcuts
from django import template
from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

import datetime
import json
import logging

from django.contrib import messages

from django_openstack import api
from django_openstack import forms
from django_openstack.dash.views import instances as dash_instances
from django_openstack.decorators import enforce_admin_access
from openstackx.api import exceptions as api_exceptions


LOG = logging.getLogger('django_openstack.syspanel.views.users')


class UserForm(forms.Form):
    def __init__(self, *args, **kwargs):
        tenant_list = kwargs.pop('tenant_list', None)
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['tenant_id'].choices = [[tenant.id, tenant.id]
                for tenant in tenant_list]

    id = forms.CharField(label="ID (username)")
    email = forms.CharField(label="Email")
    password = forms.CharField(label="Password",
                               widget=forms.PasswordInput(render_value=False),
                               required=False)
    tenant_id = forms.ChoiceField(label="Primary Tenant")


class UserDeleteForm(forms.SelfHandlingForm):
    user = forms.CharField(required=True)

    def handle(self, request, data):
        user_id = data['user']
        LOG.info('Deleting user with id "%s"' % user_id)
        api.user_delete(request, user_id)
        messages.info(request, '%s was successfully deleted.'
                                % user_id)
        return redirect(request.build_absolute_uri())


class UserEnableDisableForm(forms.SelfHandlingForm):
    id = forms.CharField(label="ID (username)", widget=forms.HiddenInput())
    enabled = forms.ChoiceField(label="enabled", widget=forms.HiddenInput(),
                                choices=[[c, c]
                                         for c in ("disable", "enable")])

    def handle(self, request, data):
        user_id = data['id']
        enabled = data['enabled'] == "enable"

        try:
            api.user_update_enabled(request, user_id, enabled)
            messages.info(request, "User %s %s" %
                                   (user_id,
                                    "enabled" if enabled else "disabled"))
        except api_exceptions.ApiException:
            messages.error(request, "Unable to %s user %s" %
                                    ("enable" if enabled else "disable",
                                     user_id))

        return redirect(request.build_absolute_uri())


@login_required
@enforce_admin_access
def index(request):
    for f in (UserDeleteForm, UserEnableDisableForm):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled

    users = []
    try:
        users = api.user_list(request)
    except api_exceptions.ApiException, e:
        messages.error(request, 'Unable to list users: %s' %
                                 e.message)

    user_delete_form = UserDeleteForm()
    user_enable_disable_form = UserEnableDisableForm()

    return shortcuts.render_to_response('django_openstack/syspanel/users/index.html', {
        'users': users,
        'user_delete_form': user_delete_form,
        'user_enable_disable_form': user_enable_disable_form,
    }, context_instance=template.RequestContext(request))


@login_required
@enforce_admin_access
def update(request, user_id):
    if request.method == "POST":
        tenants = api.tenant_list(request)
        form = UserForm(request.POST, tenant_list=tenants)
        if form.is_valid():
            user = form.clean()
            updated = []
            if user['email']:
                updated.append('email')
                api.user_update_email(request, user['id'], user['email'])
            if user['password']:
                updated.append('password')
                api.user_update_password(request, user['id'], user['password'])
            if user['tenant_id']:
                updated.append('tenant')
                api.user_update_tenant(request, user['id'], user['tenant_id'])
            messages.success(request,
                             'Updated %s for %s.'
                             % (', '.join(updated), user_id))
            return redirect('syspanel_users')
        else:
            # TODO add better error management
            messages.error(request, 'Unable to update user,\
                                    please try again.')

            return render_to_response(
            'django_openstack/syspanel/users/update.html', {
                'form': form,
                'user_id': user_id,
            }, context_instance=template.RequestContext(request))

    else:
        u = api.user_get(request, user_id)
        tenants = api.tenant_list(request)
        try:
            # FIXME
            email = u.email
        except:
            email = ''

        try:
            tenant_id = u.tenantId
        except:
            tenant_id = None
        form = UserForm(initial={'id': user_id,
                                 'tenant_id': tenant_id,
                                 'email': email},
                                 tenant_list=tenants)
        return render_to_response(
        'django_openstack/syspanel/users/update.html', {
            'form': form,
            'user_id': user_id,
        }, context_instance=template.RequestContext(request))


@login_required
@enforce_admin_access
def create(request):
    try:
        tenants = api.tenant_list(request)
    except api_exceptions.ApiException, e:
        messages.error(request, 'Unable to retrieve tenant list: %s' %
                                 e.message)
        return redirect('syspanel_users')

    if request.method == "POST":
        form = UserForm(request.POST, tenant_list=tenants)
        if form.is_valid():
            user = form.clean()
            # TODO Make this a real request
            try:
                LOG.info('Creating user with id "%s"' % user['id'])
                api.user_create(request,
                                user['id'],
                                user['email'],
                                user['password'],
                                user['tenant_id'],
                                True)
                messages.success(request,
                                 '%s was successfully created.'
                                 % user['id'])
                try:
                    api.role_add_for_tenant_user(
                        request, user['tenant_id'], user['id'],
                        settings.OPENSTACK_KEYSTONE_DEFAULT_ROLE)
                except api_exceptions.ApiException, e:
                    LOG.exception('ApiException while assigning\
                                   role to new user: %s' % user['id'])
                    messages.error(request, 'Error assigning role to user: %s' 
                                             % e.message)

                return redirect('syspanel_users')

            except api_exceptions.ApiException, e:
                LOG.exception('ApiException while creating user\n'
                          'id: "%s", email: "%s", tenant_id: "%s"' %
                          (user['id'], user['email'], user['tenant_id']))
                messages.error(request,
                                 'Error creating user: %s'
                                 % e.message)
                return redirect('syspanel_users')
        else:
            return render_to_response(
            'django_openstack/syspanel/users/create.html', {
                'form': form,
            }, context_instance=template.RequestContext(request))

    else:
        form = UserForm(tenant_list=tenants)
        return render_to_response(
        'django_openstack/syspanel/users/create.html', {
            'form': form,
        }, context_instance=template.RequestContext(request))
