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
from django.utils.translation import ugettext as _
from keystoneclient import exceptions as api_exceptions

from horizon import api
from horizon import forms
from horizon import tables
from .forms import CreateUserForm, UpdateUserForm
from .tables import UsersTable


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = UsersTable
    template_name = 'syspanel/users/index.html'

    def get_data(self):
        users = []
        try:
            users = api.user_list(self.request)
        except api_exceptions.AuthorizationFailure, e:
            LOG.exception("Unauthorized attempt to list users.")
            messages.error(self.request,
                           _('Unable to get user info: %s') % e.message)
        except Exception, e:
            LOG.exception('Exception while getting user list')
            if not hasattr(e, 'message'):
                e.message = str(e)
            messages.error(self.request,
                           _('Unable to get user info: %s') % e.message)
        return users


class UpdateView(forms.ModalFormView):
    form_class = UpdateUserForm
    template_name = 'syspanel/users/update.html'
    context_object_name = 'user'

    def get_object(self, *args, **kwargs):
        user_id = kwargs['user_id']
        try:
            return api.user_get(self.request, user_id)
        except Exception as e:
            LOG.exception('Error fetching user with id "%s"' % user_id)
            messages.error(self.request,
                           _('Unable to update user: %s') % e.message)
            raise http.Http404("User with id %s not found." % user_id)

    def get_initial(self):
        return {'id': self.object.id,
                'tenant_id': getattr(self.object, 'tenantId', None),
                'email': getattr(self.object, 'email', '')}


class CreateView(forms.ModalFormView):
    form_class = CreateUserForm
    template_name = 'syspanel/users/create.html'
