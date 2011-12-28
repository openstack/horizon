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
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from keystoneclient import exceptions as api_exceptions

from horizon import api
from horizon.dashboards.syspanel.users.forms import (UserForm, UserUpdateForm,
        UserDeleteForm, UserEnableDisableForm)
from horizon.dashboards.syspanel.users.tables import UsersTable


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    users = []
    try:
        users = api.user_list(request)
    except api_exceptions.AuthorizationFailure, e:
        LOG.exception("Unauthorized attempt to list users.")
        messages.error(request, _('Unable to get user info: %s') % e.message)
    except Exception, e:
        LOG.exception('Exception while getting user list')
        if not hasattr(e, 'message'):
            e.message = str(e)
        messages.error(request, _('Unable to get user info: %s') % e.message)

    table = UsersTable(request, users)
    handled = table.maybe_handle()
    if handled:
        return handled

    context = {'table': table}
    template = 'syspanel/users/index.html'
    return shortcuts.render(request, template, context)


@login_required
def update(request, user_id):
    user = api.user_get(request, user_id)
    form, handled = UserUpdateForm.maybe_handle(request, initial={
                                'id': user_id,
                                'tenant_id': getattr(user, 'tenantId', None),
                                'email': getattr(user, 'email', '')})
    if handled:
        return handled

    context = {'form': form,
               'user_id': user_id}
    if request.is_ajax():
        template = 'syspanel/users/_update.html'
        context['hide'] = True
    else:
        template = 'syspanel/users/update.html'

    return shortcuts.render(request, template, context)


@login_required
def create(request):
    form, handled = UserForm.maybe_handle(request)
    if handled:
        return handled

    context = {'form': form}
    if request.is_ajax():
        template = 'syspanel/users/_create.html'
        context['hide'] = True
    else:
        template = 'syspanel/users/create.html'

    return shortcuts.render(request, template, context)
