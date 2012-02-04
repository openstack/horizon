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

import logging
import operator

from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from keystoneclient import exceptions as api_exceptions

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import usage
from .forms import AddUser, CreateTenant, UpdateTenant, UpdateQuotas
from .tables import TenantsTable, TenantUsersTable, AddUsersTable


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = TenantsTable
    template_name = 'syspanel/projects/index.html'

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
    template_name = 'syspanel/projects/create.html'


class UpdateView(forms.ModalFormView):
    form_class = UpdateTenant
    template_name = 'syspanel/projects/update.html'
    context_object_name = 'tenant'

    def get_object(self, *args, **kwargs):
        tenant_id = kwargs['tenant_id']
        try:
            return api.tenant_get(self.request, tenant_id)
        except Exception as e:
            LOG.exception('Error fetching tenant with id "%s"' % tenant_id)
            messages.error(self.request, _('Unable to update tenant: %s')
                                           % e.message)
            raise http.Http404("Project with ID %s not found." % tenant_id)

    def get_initial(self):
        return {'id': self.object.id,
                'name': self.object.name,
                'description': getattr(self.object, "description", ""),
                'enabled': self.object.enabled}


class UsersView(tables.MultiTableView):
    table_classes = (TenantUsersTable, AddUsersTable)
    template_name = 'syspanel/projects/users.html'

    def get_data(self, *args, **kwargs):
        tenant_id = self.kwargs["tenant_id"]
        try:
            self.tenant = api.keystone.tenant_get(self.request, tenant_id)
            self.all_users = api.keystone.user_list(self.request)
            self.tenant_users = api.keystone.user_list(self.request, tenant_id)
        except:
            redirect = reverse("horizon:syspanel:projects:index")
            exceptions.handle(self.request,
                              _("Unable to retrieve users."),
                              redirect=redirect)
        return super(UsersView, self).get_data(*args, **kwargs)

    def get_tenant_users_data(self):
        return self.tenant_users

    def get_add_users_data(self):
        tenant_user_ids = [user.id for user in self.tenant_users]
        return [user for user in self.all_users if
                user.id not in tenant_user_ids]

    def get_context_data(self, **kwargs):
        context = super(UsersView, self).get_context_data(**kwargs)
        context['tenant'] = self.tenant
        return context


class AddUserView(forms.ModalFormView):
    form_class = AddUser
    template_name = 'syspanel/projects/add_user.html'
    context_object_name = 'tenant'

    def get_object(self, *args, **kwargs):
        return api.keystone.tenant_get(self.request, kwargs["tenant_id"])

    def get_context_data(self, **kwargs):
        context = super(AddUserView, self).get_context_data(**kwargs)
        context['tenant_id'] = self.kwargs["tenant_id"]
        context['user_id'] = self.kwargs["user_id"]
        return context

    def get_form_kwargs(self):
        kwargs = super(AddUserView, self).get_form_kwargs()
        try:
            roles = api.keystone.role_list(self.request)
        except:
            redirect = reverse("horizon:syspanel:projects:users",
                               args=(self.kwargs["tenant_id"],))
            exceptions.handle(self.request,
                              _("Unable to retrieve roles."),
                              redirect=redirect)
        roles.sort(key=operator.attrgetter("id"))
        kwargs['roles'] = roles
        return kwargs

    def get_initial(self):
        default_role = api.keystone.get_default_role(self.request)
        return {'tenant_id': self.kwargs['tenant_id'],
                'user_id': self.kwargs['user_id'],
                'role_id': getattr(default_role, "id", None)}


class QuotasView(forms.ModalFormView):
    form_class = UpdateQuotas
    template_name = 'syspanel/projects/quotas.html'
    context_object_name = 'tenant'

    def get_object(self, *args, **kwargs):
        return api.keystone.tenant_get(self.request, kwargs["tenant_id"])

    def get_initial(self):
        quotas = api.nova.tenant_quota_get(self.request,
                                               self.kwargs['tenant_id'])
        return {
            'tenant_id': self.kwargs['tenant_id'],
            'metadata_items': quotas.metadata_items,
            'injected_file_content_bytes': quotas.injected_file_content_bytes,
            'volumes': quotas.volumes,
            'gigabytes': quotas.gigabytes,
            'ram': int(quotas.ram),
            'floating_ips': quotas.floating_ips,
            'instances': quotas.instances,
            'injected_files': quotas.injected_files,
            'cores': quotas.cores}


class TenantUsageView(usage.UsageView):
    table_class = usage.TenantUsageTable
    usage_class = usage.TenantUsage
    template_name = 'syspanel/projects/usage.html'

    def get_data(self):
        super(TenantUsageView, self).get_data()
        return self.usage.get_instances()
