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
from django.views import generic

from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.utils import memoized
from horizon import workflows
from horizon import tabs
from horizon import forms

from openstack_dashboard import api
from openstack_dashboard.api import keystone
from openstack_dashboard import policy

from openstack_dashboard.dashboards.idm.organizations \
    import tables as organization_tables
from openstack_dashboard.dashboards.idm.organizations \
    import workflows as organization_workflows
from openstack_dashboard.dashboards.idm.organizations \
    import tabs as organization_tabs
from openstack_dashboard.dashboards.idm.organizations \
    import forms as organization_forms


PROJECT_INFO_FIELDS = ("domain_id",
                       "domain_name",
                       "name",
                       "description",
                       "enabled")

INDEX_URL = "horizon:idm:organizations:index"




class IndexView(tabs.TabbedTableView):
    tab_group_class = organization_tabs.PanelTabs
    template_name = 'idm/organizations/index.html'


class CreateOrganizationView(forms.ModalFormView):
    form_class = organization_forms.CreateOrganizationForm
    template_name = 'idm/organizations/create.html'



# class UpdateOrganizationView(forms.ModalFormView):
#     template_name = 'idm/organiztions/update.html'
#     def get_initial(self):
#         initial = super(UpdateOrganizationView, self).get_initial()

#         organization_id = self.kwargs['tenant_id']
#         initial['organization_id'] = organization_id

#         try:
#             # get initial organization info
#             organization_info = api.keystone.tenant_get(self.request, organization_id,
#                                                    admin=True)
#             for field in PROJECT_INFO_FIELDS:
#                 initial[field] = getattr(organization_info, field, None)

#             # Retrieve the domain name where the organization belong
#             if keystone.VERSIONS.active >= 3:
#                 try:
#                     domain = api.keystone.domain_get(self.request,
#                                                      initial["domain_id"])
#                     initial["domain_name"] = domain.name
#                 except Exception:
#                     exceptions.handle(self.request,
#                         _('Unable to retrieve organization domain.'),
#                         redirect=reverse(INDEX_URL))
#         except Exception:
#             exceptions.handle(self.request,
#                               _('Unable to retrieve organization details.'),
#                               redirect=reverse(INDEX_URL))
#         return initial         

class DetailOrganizationView(generic.DetailView):
    template_name = 'idm/organizations/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailOrganizationView, self).get_context_data(**kwargs)
        organization_id = self.kwargs['tenant_id']
        context['organization_id'] = organization_id

        try:
            # get initial organization info
            organization_info = api.keystone.tenant_get(self.request, organization_id,
                                                admin=True)
            for field in PROJECT_INFO_FIELDS:
                context[field] = getattr(organization_info, field, None)

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
        except Exception:
            exceptions.handle(self.request,
                        _('Unable to retrieve organization details.'),
                        redirect=reverse(INDEX_URL))
        return context

    def get_queryset(self,**kwargs):
        context = super(DetailOrganizationView, self).get_context_data(**kwargs)
        organization_id = self.kwargs['tenant_id']
        context['organization_id'] = organization_id

        try:
            # get initial organization info
            organization_info = api.keystone.tenant_get(self.request, organization_id,
                                                admin=True)
            for field in PROJECT_INFO_FIELDS:
                context[field] = getattr(organization_info, field, None)

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
        except Exception:
            exceptions.handle(self.request,
                        _('Unable to retrieve organization details.'),
                        redirect=reverse(INDEX_URL))
        return context