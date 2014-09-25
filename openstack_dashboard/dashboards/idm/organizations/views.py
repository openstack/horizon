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
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.api import keystone
from openstack_dashboard import policy
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.idm.organizations \
    import tables as organization_tables
from openstack_dashboard.dashboards.idm.organizations \
    import workflows as organization_workflows


PROJECT_INFO_FIELDS = ("domain_id",
                       "domain_name",
                       "name",
                       "description",
                       "enabled")

INDEX_URL = "horizon:idm:organizations:index"


class TenantContextMixin(object):
    @memoized.memoized_method
    def get_object(self):
        tenant_id = self.kwargs['tenant_id']
        try:
            return api.keystone.tenant_get(self.request, tenant_id, admin=True)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve organization information.'),
                              redirect=reverse(INDEX_URL))

    def get_context_data(self, **kwargs):
        context = super(TenantContextMixin, self).get_context_data(**kwargs)
        context['tenant'] = self.get_object()
        return context


class IndexView(tables.DataTableView):
    table_class = organization_tables.TenantsTable
    template_name = 'idm/organizations/index.html'

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        tenants = []
        marker = self.request.GET.get(
            organization_tables.TenantsTable._meta.pagination_param, None)
        domain_context = self.request.session.get('domain_context', None)
        if policy.check((("idm", "idm:list_organizations"),),
                        self.request):
            try:
                tenants, self._more = api.keystone.tenant_list(
                    self.request,
                    domain=domain_context,
                    paginate=True,
                    marker=marker)
            except Exception:
                self._more = False
                exceptions.handle(self.request,
                                  _("Unable to retrieve organization list."))
        elif policy.check((("idm", "idm:list_user_organizations"),),
                          self.request):
            try:
                tenants, self._more = api.keystone.tenant_list(
                    self.request,
                    user=self.request.user.id,
                    paginate=True,
                    marker=marker,
                    admin=False)
            except Exception:
                self._more = False
                exceptions.handle(self.request,
                                  _("Unable to retrieve organization information."))
        else:
            self._more = False
            msg = \
                _("Insufficient privilege level to view organization information.")
            messages.info(self.request, msg)
        return tenants




class CreateOrganizationView(workflows.WorkflowView):
    workflow_class = organization_workflows.CreateOrganization

    def get_initial(self):
        initial = super(CreateOrganizationView, self).get_initial()

        # Set the domain of the organization
        domain = api.keystone.get_default_domain(self.request)
        initial["domain_id"] = domain.id
        initial["domain_name"] = domain.name

        try:
            organization_id = self.request.user.organization_id
        except Exception:
            error_msg = _('Unable to retrieve default Neutron quota '
                          'values.')
            self.add_error_to_step(error_msg, 'update_quotas')
 

        return initial


class UpdateOrganizationView(workflows.WorkflowView):
    workflow_class = organization_workflows.UpdateOrganization

    def get_initial(self):
        initial = super(UpdateOrganizationView, self).get_initial()

        organization_id = self.kwargs['tenant_id']
        initial['organization_id'] = organization_id

        try:
            # get initial organization info
            organization_info = api.keystone.tenant_get(self.request, organization_id,
                                                   admin=True)
            for field in PROJECT_INFO_FIELDS:
                initial[field] = getattr(organization_info, field, None)

            # Retrieve the domain name where the organization belong
            if keystone.VERSIONS.active >= 3:
                try:
                    domain = api.keystone.domain_get(self.request,
                                                     initial["domain_id"])
                    initial["domain_name"] = domain.name
                except Exception:
                    exceptions.handle(self.request,
                        _('Unable to retrieve organization domain.'),
                        redirect=reverse(INDEX_URL))


        #     # get initial organization quota
        #     quota_data = quotas.get_tenant_quota_data(self.request,
        #                                               tenant_id=organization_id)
        #     if api.base.is_service_enabled(self.request, 'network') and \
        #             api.neutron.is_quotas_extension_supported(self.request):
        #         quota_data += api.neutron.tenant_quota_get(self.request,
        #                                                   tenant_id=organization_id)
        #     for field in quotas.QUOTA_FIELDS:
        #         initial[field] = quota_data.get(field).limit
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve organization details.'),
                              redirect=reverse(INDEX_URL))
        return initial         
