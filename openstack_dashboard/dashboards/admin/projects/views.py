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

from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard import usage
from openstack_dashboard.usage import quotas
from openstack_dashboard.dashboards.admin.users.views import CreateView
from .forms import CreateUser
from .tables import TenantsTable, TenantUsersTable, AddUsersTable
from .workflows import CreateProject, UpdateProject

LOG = logging.getLogger(__name__)

PROJECT_INFO_FIELDS = ("name",
                       "description",
                       "enabled")

INDEX_URL = "horizon:admin:projects:index"


class TenantContextMixin(object):
    def get_object(self):
        if not hasattr(self, "_object"):
            tenant_id = self.kwargs['tenant_id']
            try:
                self._object = api.keystone.tenant_get(self.request,
                                                       tenant_id,
                                                       admin=True)
            except:
                exceptions.handle(self.request,
                                  _('Unable to retrieve project information.'),
                                  redirect=reverse(INDEX_URL))
        return self._object

    def get_context_data(self, **kwargs):
        context = super(TenantContextMixin, self).get_context_data(**kwargs)
        context['tenant'] = self.get_object()
        return context


class IndexView(tables.DataTableView):
    table_class = TenantsTable
    template_name = 'admin/projects/index.html'

    def get_data(self):
        tenants = []
        try:
            tenants = api.keystone.tenant_list(self.request, admin=True)
        except:
            exceptions.handle(self.request,
                              _("Unable to retrieve project list."))
        tenants.sort(key=lambda x: x.id, reverse=True)
        return tenants


class UsersView(tables.MultiTableView):
    table_classes = (TenantUsersTable, AddUsersTable)
    template_name = 'admin/projects/users.html'

    def _get_shared_data(self, *args, **kwargs):
        tenant_id = self.kwargs["tenant_id"]
        if not hasattr(self, "_shared_data"):
            try:
                tenant = api.keystone.tenant_get(self.request,
                                                 tenant_id,
                                                 admin=True)
                all_users = api.keystone.user_list(self.request)
                tenant_users = api.keystone.user_list(self.request, tenant_id)
                self._shared_data = {'tenant': tenant,
                                     'all_users': all_users,
                                     'tenant_users': tenant_users}
            except:
                exceptions.handle(self.request,
                                  _("Unable to retrieve users."),
                                  redirect=reverse(INDEX_URL))
        return self._shared_data

    def get_tenant_users_data(self):
        return self._get_shared_data()["tenant_users"]

    def get_add_users_data(self):
        tenant_users = self._get_shared_data()["tenant_users"]
        all_users = self._get_shared_data()["all_users"]
        tenant_user_ids = [user.id for user in tenant_users]
        return filter(lambda u: u.id not in tenant_user_ids, all_users)

    def get_context_data(self, **kwargs):
        context = super(UsersView, self).get_context_data(**kwargs)
        context['tenant'] = self._get_shared_data()["tenant"]
        return context


class TenantUsageView(usage.UsageView):
    table_class = usage.TenantUsageTable
    usage_class = usage.TenantUsage
    template_name = 'admin/projects/usage.html'

    def get_data(self):
        super(TenantUsageView, self).get_data()
        return self.usage.get_instances()


class CreateProjectView(workflows.WorkflowView):
    workflow_class = CreateProject
    template_name = "admin/projects/create.html"

    def get_initial(self):
        initial = super(CreateProjectView, self).get_initial()

        # get initial quota defaults
        try:
            quota_defaults = quotas.get_default_quota_data(self.request)
            for field in quotas.QUOTA_FIELDS:
                initial[field] = quota_defaults.get(field).limit

        except:
            error_msg = _('Unable to retrieve default quota values.')
            self.add_error_to_step(error_msg, 'update_quotas')

        return initial


class UpdateProjectView(workflows.WorkflowView):
    workflow_class = UpdateProject
    template_name = "admin/projects/update.html"

    def get_initial(self):
        initial = super(UpdateProjectView, self).get_initial()

        project_id = self.kwargs['tenant_id']
        initial['project_id'] = project_id

        try:
            # get initial project info
            project_info = api.keystone.tenant_get(self.request, project_id,
                                                   admin=True)
            for field in PROJECT_INFO_FIELDS:
                initial[field] = getattr(project_info, field, None)

            # get initial project quota
            quota_data = quotas.get_tenant_quota_data(self.request,
                                                      tenant_id=project_id)
            for field in quotas.QUOTA_FIELDS:
                initial[field] = quota_data.get(field).limit
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve project details.'),
                              redirect=reverse(INDEX_URL))
        return initial


class CreateUserView(CreateView):
    form_class = CreateUser
    template_name = "admin/projects/create_user.html"
    success_url = reverse_lazy('horizon:admin:projects:index')

    def get_initial(self):
        default_role = api.keystone.get_default_role(self.request)
        return {'role_id': getattr(default_role, "id", None),
                'tenant_id': self.kwargs['tenant_id']}

    def get_context_data(self, **kwargs):
        context = super(CreateUserView, self).get_context_data(**kwargs)
        context['tenant_id'] = self.kwargs['tenant_id']
        context['tenant_name'] = api.keystone.tenant_get(
            self.request,
            self.kwargs['tenant_id'],
            admin=True).name
        return context
