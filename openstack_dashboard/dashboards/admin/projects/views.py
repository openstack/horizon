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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard import usage
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.admin.projects.tables import TenantsTable
from openstack_dashboard.dashboards.admin.projects.workflows \
    import CreateProject
from openstack_dashboard.dashboards.admin.projects.workflows \
    import UpdateProject

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
            except Exception:
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

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        tenants = []
        marker = self.request.GET.get(
                        TenantsTable._meta.pagination_param, None)
        domain_context = self.request.session.get('domain_context', None)
        try:
            tenants, self._more = api.keystone.tenant_list(
                                               self.request,
                                               domain=domain_context,
                                               paginate=True,
                                               marker=marker)
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              _("Unable to retrieve project list."))
        return tenants


class ProjectUsageView(usage.UsageView):
    table_class = usage.ProjectUsageTable
    usage_class = usage.ProjectUsage
    template_name = 'admin/projects/usage.html'

    def get_data(self):
        super(ProjectUsageView, self).get_data()
        return self.usage.get_instances()


class CreateProjectView(workflows.WorkflowView):
    workflow_class = CreateProject

    def get_initial(self):
        initial = super(CreateProjectView, self).get_initial()

        # get initial quota defaults
        try:
            quota_defaults = quotas.get_default_quota_data(self.request)
            for field in quotas.QUOTA_FIELDS:
                initial[field] = quota_defaults.get(field).limit

        except Exception:
            error_msg = _('Unable to retrieve default quota values.')
            self.add_error_to_step(error_msg, 'update_quotas')

        return initial


class UpdateProjectView(workflows.WorkflowView):
    workflow_class = UpdateProject

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
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve project details.'),
                              redirect=reverse(INDEX_URL))
        return initial
