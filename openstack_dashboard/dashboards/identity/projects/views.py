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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.utils import memoized
from horizon import views
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.api import keystone
from openstack_dashboard import policy
from openstack_dashboard import usage
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.identity.projects \
    import tables as project_tables
from openstack_dashboard.dashboards.identity.projects \
    import workflows as project_workflows
from openstack_dashboard.dashboards.project.overview \
    import views as project_views

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
        context = super(TenantContextMixin, self).get_context_data(**kwargs)
        context['tenant'] = self.get_object()
        return context


class IndexView(tables.DataTableView):
    table_class = project_tables.TenantsTable
    template_name = 'identity/projects/index.html'
    page_title = _("Projects")

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        tenants = []
        marker = self.request.GET.get(
            project_tables.TenantsTable._meta.pagination_param, None)

        self._more = False

        if policy.check((("identity", "identity:list_projects"),),
                        self.request):
            domain_context = api.keystone.get_effective_domain_id(self.request)
            try:
                tenants, self._more = api.keystone.tenant_list(
                    self.request,
                    domain=domain_context,
                    paginate=True,
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
                    admin=False)
            except Exception:
                exceptions.handle(self.request,
                                  _("Unable to retrieve project information."))
        else:
            msg = \
                _("Insufficient privilege level to view project information.")
            messages.info(self.request, msg)

        if api.keystone.VERSIONS.active >= 3:
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
        super(ProjectUsageView, self).get_data()
        return self.usage.get_instances()


class CreateProjectView(workflows.WorkflowView):
    workflow_class = project_workflows.CreateProject

    def get_initial(self):

        if (api.keystone.is_multi_domain_enabled() and
                not api.keystone.is_cloud_admin(self.request)):
            self.workflow_class = project_workflows.CreateProjectNoQuota

        initial = super(CreateProjectView, self).get_initial()

        # Set the domain of the project
        domain = api.keystone.get_default_domain(self.request)
        initial["domain_id"] = domain.id
        initial["domain_name"] = domain.name

        # TODO(esp): fix this for Domain Admin or find a work around
        # get initial quota defaults
        if api.keystone.is_cloud_admin(self.request):
            try:
                quota_defaults = quotas.get_default_quota_data(self.request)

                try:
                    if api.base.is_service_enabled(
                            self.request, 'network') and \
                            api.neutron.is_quotas_extension_supported(
                                self.request):
                        # TODO(jpichon): There is no API to access the Neutron
                        # default quotas (LP#1204956). For now, use the values
                        # from the current project.
                        project_id = self.request.user.project_id
                        quota_defaults += api.neutron.tenant_quota_get(
                            self.request,
                            tenant_id=project_id)
                except Exception:
                    error_msg = _('Unable to retrieve default Neutron quota '
                                  'values.')
                    self.add_error_to_step(error_msg, 'create_quotas')

                for field in quotas.QUOTA_FIELDS:
                    initial[field] = quota_defaults.get(field).limit

            except Exception:
                error_msg = _('Unable to retrieve default quota values.')
                self.add_error_to_step(error_msg, 'create_quotas')

        return initial


class UpdateProjectView(workflows.WorkflowView):
    workflow_class = project_workflows.UpdateProject

    def get_initial(self):

        if (api.keystone.is_multi_domain_enabled() and
                not api.keystone.is_cloud_admin(self.request)):
            self.workflow_class = project_workflows.UpdateProjectNoQuota

        initial = super(UpdateProjectView, self).get_initial()

        project_id = self.kwargs['tenant_id']
        initial['project_id'] = project_id

        try:
            # get initial project info
            project_info = api.keystone.tenant_get(self.request, project_id,
                                                   admin=True)
            for field in PROJECT_INFO_FIELDS:
                initial[field] = getattr(project_info, field, None)

            # Retrieve the domain name where the project belong
            if keystone.VERSIONS.active >= 3:
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

            # get initial project quota
            if keystone.is_cloud_admin(self.request):
                quota_data = quotas.get_tenant_quota_data(self.request,
                                                          tenant_id=project_id)
                if api.base.is_service_enabled(self.request, 'network') and \
                        api.neutron.is_quotas_extension_supported(
                            self.request):
                    quota_data += api.neutron.tenant_quota_get(
                        self.request, tenant_id=project_id)
                for field in quotas.QUOTA_FIELDS:
                    initial[field] = quota_data.get(field).limit
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve project details.'),
                              redirect=reverse(INDEX_URL))
        return initial


class DetailProjectView(views.HorizonTemplateView):
    template_name = 'identity/projects/detail.html'
    page_title = "{{ project.name }}"

    def get_context_data(self, **kwargs):
        context = super(DetailProjectView, self).get_context_data(**kwargs)
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
