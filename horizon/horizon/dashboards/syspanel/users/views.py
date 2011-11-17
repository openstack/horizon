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
    user = api.user_get(request, user_id)
    form, handled = UserUpdateForm.maybe_handle(request, initial={
                                'id': user_id,
                                'tenant_id': getattr(user, 'tenantId', None),
                                'email': getattr(user, 'email', '')})
    if handled:
        return handled
    return shortcuts.render(request,
                            'syspanel/users/update.html', {
                                'form': form,
                                'user_id': user_id})


@login_required
def create(request):
    form, handled = UserForm.maybe_handle(request)
    if handled:
        return handled
    return shortcuts.render(request,
                            'syspanel/users/create.html',
                            {'form': form})
