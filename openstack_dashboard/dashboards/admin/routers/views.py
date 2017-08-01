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

from django.conf import settings
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
    template_name = 'horizon/common/_data_table_view.html'
    FILTERS_MAPPING = {'admin_state_up': {_("up"): True, _("down"): False}}

    def needs_filter_first(self, table):
        return getattr(self, '_needs_filter_first', False)

    def _get_routers(self):
        try:
            filters = self.get_filters(filters_map=self.FILTERS_MAPPING)

            # If admin_filter_first is set and if there are not other filters
            # selected, then search criteria must be provided and return an
            # empty list
            filter_first = getattr(settings, 'FILTER_DATA_FIRST', {})
            if filter_first.get('admin.routers', False) and not filters:
                self._needs_filter_first = True
                return []
            self._needs_filter_first = False

            routers = api.neutron.router_list(self.request, **filters)
        except Exception:
            routers = []
            exceptions.handle(self.request,
                              _('Unable to retrieve router list.'))
        self._set_router_tenant_info(routers)
        return routers

    def _set_router_tenant_info(self, routers):
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

    def get_filters(self, filters=None, filters_map=None):
        filters = super(IndexView, self).get_filters(filters, filters_map)
        if 'project' in filters:
            tenants = api.keystone.tenant_list(self.request)[0]
            tenants_filter_ids = [t.id for t in tenants
                                  if t.name == filters['project']]
            del filters['project']
            filters['tenant_id'] = tenants_filter_ids
        return filters


class DetailView(r_views.DetailView):
    tab_group_class = rtabs.RouterDetailTabs
    failure_url = reverse_lazy('horizon:admin:routers:index')
    network_url = 'horizon:admin:networks:detail'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        table = rtbl.RoutersTable(self.request)
        context["url"] = self.failure_url
        router = context["router"]
        # try to lookup the l3 agent location so we know where to troubleshoot
        if api.neutron.is_extension_supported(self.request,
                                              'l3_agent_scheduler'):
            try:
                agents = api.neutron.list_l3_agent_hosting_router(self.request,
                                                                  router.id)
                router.l3_host_agents = agents
            except Exception:
                exceptions.handle(self.request,
                                  _('The L3 agent information could not '
                                    'be located.'))
        else:
            router.l3_host_agents = []
        context["actions"] = table.render_row_actions(router)
        return context


class UpdateView(r_views.UpdateView):
    form_class = rforms.UpdateForm
    template_name = 'project/routers/update.html'
    success_url = reverse_lazy("horizon:admin:routers:index")
    submit_url = "horizon:admin:routers:update"


class L3AgentView(IndexView):

    def _get_routers(self, search_opts=None):
        try:
            agent_id = self.kwargs['l3_agent_id']
            agents = api.neutron.agent_list(self.request, id=agent_id)
            if agents:
                self.page_title = _("Routers on %(host)s") % {'host':
                                                              agents[0].host}
            routers = api.neutron.\
                router_list_on_l3_agent(self.request, agent_id,
                                        search_opts=search_opts)
        except Exception:
            routers = []
            exceptions.handle(self.request,
                              _('Unable to retrieve router list.'))
        self._set_router_tenant_info(routers)
        return routers
