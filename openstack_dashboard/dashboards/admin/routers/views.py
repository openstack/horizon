# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
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

"""
Views for managing Neutron Routers.
"""

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.networks import views as n_views
from openstack_dashboard.dashboards.admin.routers import forms as rforms
from openstack_dashboard.dashboards.admin.routers import tables as rtbl
from openstack_dashboard.dashboards.admin.routers import tabs as rtabs
from openstack_dashboard.dashboards.project.routers import views as r_views


class IndexView(r_views.IndexView, n_views.IndexView):
    table_class = rtbl.RoutersTable
    template_name = 'admin/routers/index.html'

    def _get_routers(self, search_opts=None):
        try:
            routers = api.neutron.router_list(self.request,
                                              search_opts=search_opts)
        except Exception:
            routers = []
            exceptions.handle(self.request,
                              _('Unable to retrieve router list.'))
        if routers:
            tenant_dict = self._get_tenant_list()
            ext_net_dict = self._list_external_networks()
            for r in routers:
                # Set tenant name
                tenant = tenant_dict.get(r.tenant_id, None)
                r.tenant_name = getattr(tenant, 'name', None)
                # If name is empty use UUID as name
                r.name = r.name_or_id
                # Set external network name
                self._set_external_network(r, ext_net_dict)
        return routers

    def get_data(self):
        routers = self._get_routers()
        return routers


class DetailView(r_views.DetailView):
    tab_group_class = rtabs.RouterDetailTabs
    template_name = 'admin/routers/detail.html'
    failure_url = reverse_lazy('horizon:admin:routers:index')

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        table = rtbl.RoutersTable(self.request)
        context["url"] = self.failure_url
        context["actions"] = table.render_row_actions(context["router"])
        return context


class UpdateView(r_views.UpdateView):
    form_class = rforms.UpdateForm
    template_name = 'project/routers/update.html'
    success_url = reverse_lazy("horizon:admin:routers:index")
    submit_url = "horizon:admin:routers:update"
