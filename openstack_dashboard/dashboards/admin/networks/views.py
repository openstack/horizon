# Copyright 2012 NEC Corporation
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

from collections import OrderedDict

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.tabs import OverviewTab
from openstack_dashboard.dashboards.project.networks import views as user_views
from openstack_dashboard.utils import filters
from openstack_dashboard.utils import settings as setting_utils

from openstack_dashboard.dashboards.admin.networks.agents import tabs \
    as agents_tabs
from openstack_dashboard.dashboards.admin.networks \
    import forms as project_forms
from openstack_dashboard.dashboards.admin.networks.ports \
    import tables as ports_tables
from openstack_dashboard.dashboards.admin.networks.subnets \
    import tables as subnets_tables
from openstack_dashboard.dashboards.admin.networks \
    import tables as networks_tables
from openstack_dashboard.dashboards.admin.networks import workflows


class IndexView(tables.DataTableView):
    table_class = networks_tables.NetworksTable
    page_title = _("Networks")
    FILTERS_MAPPING = {'shared': {_("yes"): True, _("no"): False},
                       'router:external': {_("yes"): True, _("no"): False},
                       'admin_state_up': {_("up"): True, _("down"): False}}

    @memoized.memoized_method
    def _get_tenant_list(self):
        try:
            tenants, has_more = api.keystone.tenant_list(self.request)
        except Exception:
            tenants = []
            msg = _("Unable to retrieve information about the "
                    "networks' projects.")
            exceptions.handle(self.request, msg)

        tenant_dict = OrderedDict([(t.id, t) for t in tenants])
        return tenant_dict

    def _get_agents_data(self, network):
        agents = []
        data = _("Unknown")

        try:
            if api.neutron.is_extension_supported(self.request,
                                                  'dhcp_agent_scheduler'):
                # This method is called for each network. If agent-list cannot
                # be retrieved, we will see many pop-ups. So the error message
                # will be popup-ed in get_data() below.
                agents = api.neutron.list_dhcp_agent_hosting_networks(
                    self.request, network)
                data = len(agents)
        except Exception:
            msg = _('Unable to list dhcp agents hosting network.')
            exceptions.handle(self.request, msg)
        return data

    def needs_filter_first(self, table):
        return getattr(self, "_needs_filter_first", False)

    def get_data(self):
        try:
            search_opts = self.get_filters(filters_map=self.FILTERS_MAPPING)

            # If the tenant filter selected and the tenant does not exist.
            # We do not need to retrieve the list from neutron,just return
            # an empty list.
            if 'tenant_id' in search_opts and not search_opts['tenant_id']:
                return []

            # If filter_first is set and if there are not other filters
            # selected, then search criteria must be provided and return an
            # empty list
            if (setting_utils.get_dict_config('FILTER_DATA_FIRST',
                                              'admin.networks') and
                    not search_opts):
                self._needs_filter_first = True
                return []
            self._needs_filter_first = False

            networks = api.neutron.network_list(self.request, **search_opts)
        except Exception:
            networks = []
            msg = _('Network list can not be retrieved.')
            exceptions.handle(self.request, msg)
        if networks:
            self.exception = False
            tenant_dict = self._get_tenant_list()
            for n in networks:
                # Set tenant name
                tenant = tenant_dict.get(n.tenant_id, None)
                n.tenant_name = getattr(tenant, 'name', None)
                n.num_agents = self._get_agents_data(n.id)
        return networks

    def get_filters(self, filters=None, filters_map=None):
        filters = super(IndexView, self).get_filters(filters, filters_map)
        if 'project' in filters:
            tenants = api.keystone.tenant_list(self.request)[0]
            tenant_filter_ids = [t.id for t in tenants
                                 if t.name == filters['project']]
            filters['tenant_id'] = tenant_filter_ids
            del filters['project']
        return filters


class CreateView(user_views.CreateView):
    workflow_class = workflows.CreateNetwork


class UpdateView(user_views.UpdateView):
    form_class = project_forms.UpdateNetwork
    template_name = 'admin/networks/update.html'
    success_url = reverse_lazy('horizon:admin:networks:index')
    submit_url = "horizon:admin:networks:update"

    def get_initial(self):
        network = self._get_object()
        return {'network_id': network['id'],
                'tenant_id': network['tenant_id'],
                'name': network['name'],
                'admin_state': network['admin_state_up'],
                'shared': network['shared'],
                'external': network['router__external']}


class NetworkDetailsTabs(tabs.DetailTabsGroup):
    slug = "network_tabs"
    tabs = (OverviewTab, subnets_tables.SubnetsTab, ports_tables.PortsTab,
            agents_tabs.DHCPAgentsTab, )
    sticky = True


class DetailView(tabs.TabbedTableView):
    tab_group_class = NetworkDetailsTabs
    template_name = 'horizon/common/_detail.html'
    page_title = '{{ network.name | default:network.id }}'

    @memoized.memoized_method
    def _get_data(self):
        try:
            network_id = self.kwargs['network_id']
            network = api.neutron.network_get(self.request, network_id)
            network.set_id_as_name_if_empty(length=0)
        except Exception:
            network = None
            msg = _('Unable to retrieve details for network "%s".') \
                % (network_id)
            exceptions.handle(self.request, msg,
                              redirect=self.get_redirect_url())
        return network

    @staticmethod
    def get_redirect_url():
        return reverse_lazy('horizon:admin:networks:index')

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        network = self._get_data()
        context["network"] = network
        table = networks_tables.NetworksTable(self.request)
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(network)
        choices = networks_tables.DISPLAY_CHOICES
        network.admin_state_label = (
            filters.get_display_label(choices, network.admin_state))
        return context
