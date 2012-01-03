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
from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from keystoneclient import exceptions as api_exceptions

from horizon import api
from horizon import forms
from horizon import tables
from .forms import (AddUser, RemoveUser, CreateTenant, UpdateTenant,
                    UpdateQuotas)
from .tables import TenantsTable


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = TenantsTable
    template_name = 'syspanel/tenants/index.html'

    def get_data(self):
        tenants = []
        try:
            tenants = api.tenant_list(self.request)
        except api_exceptions.AuthorizationFailure, e:
            LOG.exception("Unauthorized attempt to list tenants.")
            messages.error(self.request, _('Unable to get tenant info: %s')
                                         % e.message)
        except Exception, e:
            LOG.exception('Exception while getting tenant list')
            if not hasattr(e, 'message'):
                e.message = str(e)
            messages.error(self.request, _('Unable to get tenant info: %s')
                                         % e.message)
        tenants.sort(key=lambda x: x.id, reverse=True)
        return tenants


class CreateView(forms.ModalFormView):
    form_class = CreateTenant
    template_name = 'syspanel/tenants/create.html'


class UpdateView(forms.ModalFormView):
    form_class = UpdateTenant
    template_name = 'syspanel/tenants/update.html'
    context_object_name = 'tenant'

    def get_object(self, tenant_id):
        try:
            return api.tenant_get(self.request, tenant_id)
        except Exception as e:
            LOG.exception('Error fetching tenant with id "%s"' % tenant_id)
            messages.error(request, _('Unable to update tenant: %s')
                                      % e.message)
            raise http.Http404("Tenant with ID %s not found." % tenant_id)

    def get_initial(self):
        return {'id': self.object.id,
                'name': self.object.name,
                'description': self.object.description,
                'enabled': self.object.enabled}


def users(request, tenant_id):
    for f in (AddUser, RemoveUser,):
        form, handled = f.maybe_handle(request)
        if handled:
            return handled

    add_user_form = AddUser()
    remove_user_form = RemoveUser()

    users = api.user_list(request, tenant_id)
    all_users = api.user_list(request)
    user_ids = [u.id for u in users]
    new_users = [u for u in all_users if not u.id in user_ids]
    return shortcuts.render(request,
                            'syspanel/tenants/users.html', {
                                'add_user_form': add_user_form,
                                'remove_user_form': remove_user_form,
                                'tenant_id': tenant_id,
                                'users': users,
                                'new_users': new_users})


class QuotasView(forms.ModalFormView):
    form_class = UpdateQuotas
    template_name = 'syspanel/tenants/quotas.html'
    context_object_name = 'tenant'

    def get_object(self, tenant_id):
        return api.tenant_get(self.request, tenant_id)

    def get_initial(self):
        admin_api = api.admin_api(self.request)
        quotas = admin_api.quota_sets.get(self.kwargs['tenant_id'])
        return {
            'tenant_id': quotas.id,
            'metadata_items': quotas.metadata_items,
            'injected_file_content_bytes': quotas.injected_file_content_bytes,
            'volumes': quotas.volumes,
            'gigabytes': quotas.gigabytes,
            'ram': int(quotas.ram),
            'floating_ips': quotas.floating_ips,
            'instances': quotas.instances,
            'injected_files': quotas.injected_files,
            'cores': quotas.cores}
