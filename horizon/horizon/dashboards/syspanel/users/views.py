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

from django import shortcuts
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from openstackx.api import exceptions as api_exceptions

from horizon import api
from horizon.dashboards.syspanel.users.forms import (UserForm, UserUpdateForm,
        UserDeleteForm, UserEnableDisableForm)


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    for f in (UserDeleteForm, UserEnableDisableForm):
        form, handled = f.maybe_handle(request)
        if handled:
            return handled

    users = []
    try:
        users = api.user_list(request)
    except api_exceptions.ApiException, e:
        messages.error(request, _('Unable to list users: %s') %
                                 e.message)

    user_delete_form = UserDeleteForm()
    toggle_form = UserEnableDisableForm()

    return shortcuts.render(request,
                            'syspanel/users/index.html', {
                                'users': users,
                                'user_delete_form': user_delete_form,
                                'user_enable_disable_form': toggle_form})


@login_required
def update(request, user_id):
    if request.method == "POST":
        tenants = api.tenant_list(request)
        form = UserUpdateForm(request.POST, tenant_list=tenants)
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
                             _('Updated %(attrib)s for %(user)s.') %
                             {"attrib": ', '.join(updated), "user": user_id})
            return shortcuts.redirect('horizon:syspanel:users:index')
        else:
            # TODO add better error management
            messages.error(request,
                           _('Unable to update user, please try again.'))

            return shortcuts.render(request,
                                    'syspanel/users/update.html', {
                                        'form': form,
                                        'user_id': user_id})

    else:
        user = api.user_get(request, user_id)
        tenants = api.tenant_list(request)
        form = UserUpdateForm(tenant_list=tenants,
                              initial={'id': user_id,
                                       'tenant_id': getattr(user,
                                                            'tenantId',
                                                            None),
                                       'email': getattr(user, 'email', '')})
        return shortcuts.render(request,
                                'syspanel/users/update.html', {
                                    'form': form,
                                    'user_id': user_id})


@login_required
def create(request):
    try:
        tenants = api.tenant_list(request)
    except api_exceptions.ApiException, e:
        messages.error(request, _('Unable to retrieve tenant list: %s') %
                                 e.message)
        return shortcuts.redirect('horizon:syspanel:users:index')

    if request.method == "POST":
        form = UserForm(request.POST, tenant_list=tenants)
        if form.is_valid():
            user = form.clean()
            # TODO Make this a real request
            try:
                LOG.info('Creating user with name "%s"' % user['name'])
                new_user = api.user_create(request,
                                user['name'],
                                user['email'],
                                user['password'],
                                user['tenant_id'],
                                True)
                messages.success(request,
                                 _('User "%s" was successfully created.')
                                 % user['name'])
                try:
                    api.role_add_for_tenant_user(
                        request, user['tenant_id'], new_user.id,
                        settings.OPENSTACK_KEYSTONE_DEFAULT_ROLE)
                except Exception, e:
                    LOG.exception('Exception while assigning \
                                   role to new user: %s' % new_user.id)
                    messages.error(request,
                                   _('Error assigning role to user: %s')
                                   % e.message)

                return shortcuts.redirect('horizon:syspanel:users:index')

            except Exception, e:
                LOG.exception('Exception while creating user\n'
                          'name: "%s", email: "%s", tenant_id: "%s"' %
                          (user['name'], user['email'], user['tenant_id']))
                messages.error(request,
                                _('Error creating user: %s')
                                 % e.message)
                return shortcuts.redirect('horizon:syspanel:users:index')
        else:
            return shortcuts.render(request,
                                    'syspanel/users/create.html', {
                                        'form': form})

    else:
        form = UserForm(tenant_list=tenants)
        return shortcuts.render(request,
                                'syspanel/users/create.html', {
                                    'form': form})
