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

from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.api import keystone
from openstack_dashboard import policy
from openstack_dashboard import usage
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.identity.projects \
    import tables as project_tables
from openstack_dashboard.dashboards.identity.projects \
    import tabs as project_tabs
from openstack_dashboard.dashboards.identity.projects \
    import workflows as project_workflows
from openstack_dashboard.dashboards.project.overview \
    import views as project_views
from openstack_dashboard.utils import identity
from openstack_dashboard.utils import settings as setting_utils

PROJECT_INFO_FIELDS = ("domain_id",
                       "domain_name",
                       "name",
                       "description",
                       "enabled")

INDEX_URL = "horizon:identity:projects:index"


class TenantContextMixin(object):
    @memoized.memoized_method
    def get_object(self):
        tenant_id = self.kwargs['tenant_id']
        try:
            return api.keystone.tenant_get(self.request, tenant_id, admin=True)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve project information.'),
                              redirect=reverse(INDEX_URL))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant'] = self.get_object()
        return context


class IndexView(tables.DataTableView):
    table_class = project_tables.TenantsTable
    template_name = 'identity/projects/index.html'
    page_title = _("Projects")

    def needs_filter_first(self, table):
        return self._needs_filter_first

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        tenants = []
        marker = self.request.GET.get(
            project_tables.TenantsTable._meta.pagination_param, None)
        self._more = False
        filters = self.get_filters()

        self._needs_filter_first = False

        if policy.check((("identity", "identity:list_projects"),),
                        self.request):

            # If filter_first is set and if there are not other filters
            # selected, then search criteria must be provided and
            # return an empty list
            if (setting_utils.get_dict_config(
                    'FILTER_DATA_FIRST', 'identity.projects') and not filters):
                self._needs_filter_first = True
                self._more = False
                return tenants

            domain_id = identity.get_domain_id_for_operation(self.request)
            try:
                tenants, self._more = api.keystone.tenant_list(
                    self.request,
                    domain=domain_id,
                    paginate=True,
                    filters=filters,
                    marker=marker)
            except Exception:
                exceptions.handle(self.request,
                                  _("Unable to retrieve project list."))
        elif policy.check((("identity", "identity:list_user_projects"),),
                          self.request):
            try:
                tenants, self._more = api.keystone.tenant_list(
                    self.request,
                    user=self.request.user.id,
                    paginate=True,
                    marker=marker,
                    filters=filters,
                    admin=False)
            except Exception:
                exceptions.handle(self.request,
                                  _("Unable to retrieve project information."))
        else:
            msg = \
                _("Insufficient privilege level to view project information.")
            messages.info(self.request, msg)

        domain_lookup = api.keystone.domain_lookup(self.request)
        for t in tenants:
            t.domain_name = domain_lookup.get(t.domain_id)

        return tenants


class ProjectUsageView(usage.UsageView):
    table_class = usage.ProjectUsageTable
    usage_class = usage.ProjectUsage
    template_name = 'identity/projects/usage.html'
    csv_response_class = project_views.ProjectUsageCsvRenderer
    csv_template_name = 'project/overview/usage.csv'
    page_title = _("Project Usage")

    def get_data(self):
        super().get_data()
        return self.usage.get_instances()


class CreateProjectView(workflows.WorkflowView):
    workflow_class = project_workflows.CreateProject

    def get_initial(self):
        initial = super().get_initial()

        # Set the domain of the project
        domain = api.keystone.get_default_domain(self.request)
        initial["domain_id"] = domain.id
        initial["domain_name"] = domain.name

        return initial


class UpdateProjectView(workflows.WorkflowView):
    workflow_class = project_workflows.UpdateProject

    def get_initial(self):
        initial = super().get_initial()

        project_id = self.kwargs['tenant_id']
        initial['project_id'] = project_id

        try:
            # get initial project info
            project_info = api.keystone.tenant_get(self.request, project_id,
                                                   admin=True)
            for field in PROJECT_INFO_FIELDS:
                initial[field] = getattr(project_info, field, None)

            # get extra columns info
            ex_info = settings.PROJECT_TABLE_EXTRA_INFO
            for ex_field in ex_info:
                initial[ex_field] = getattr(project_info, ex_field, None)

            # Retrieve the domain name where the project belong
            try:
                if policy.check((("identity", "identity:get_domain"),),
                                self.request):
                    domain = api.keystone.domain_get(self.request,
                                                     initial["domain_id"])
                    initial["domain_name"] = domain.name

                else:
                    domain = api.keystone.get_default_domain(self.request)
                    initial["domain_name"] = domain.name

            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve project domain.'),
                                  redirect=reverse(INDEX_URL))
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve project details.'),
                              redirect=reverse(INDEX_URL))
        return initial


class UpdateQuotasView(workflows.WorkflowView):
    workflow_class = project_workflows.UpdateQuota

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.kwargs['tenant_id']
        initial['project_id'] = project_id
        try:
            # get initial project quota
            if keystone.is_cloud_admin(self.request):
                quota_data = quotas.get_tenant_quota_data(self.request,
                                                          tenant_id=project_id)
                for field in quotas.QUOTA_FIELDS:
                    initial[field] = quota_data.get(field).limit
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve project quotas.'),
                              redirect=reverse(INDEX_URL))
        initial['disabled_quotas'] = quotas.get_disabled_quotas(self.request)
        return initial


class DetailProjectView(tabs.TabView):
    tab_group_class = project_tabs.ProjectDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ project.name }}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_data()
        table = project_tables.TenantsTable(self.request)
        context["project"] = project
        context["url"] = reverse(INDEX_URL)
        context["actions"] = table.render_row_actions(project)

        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            project_id = self.kwargs['project_id']
            project = api.keystone.tenant_get(self.request, project_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve project details.'),
                              redirect=reverse(INDEX_URL))
        return project

    def get_tabs(self, request, *args, **kwargs):
        project = self.get_data()
        return self.tab_group_class(request, project=project, **kwargs)
