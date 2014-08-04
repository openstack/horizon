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

from django.core.urlresolvers import reverse_lazy
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks import views as user_views

from openstack_dashboard.dashboards.admin.networks.agents \
    import tables as agents_tables
from openstack_dashboard.dashboards.admin.networks \
    import forms as project_forms
from openstack_dashboard.dashboards.admin.networks.ports \
    import tables as ports_tables
from openstack_dashboard.dashboards.admin.networks.subnets \
    import tables as subnets_tables
from openstack_dashboard.dashboards.admin.networks \
    import tables as networks_tables


class IndexView(tables.DataTableView):
    table_class = networks_tables.NetworksTable
    template_name = 'admin/networks/index.html'

    @memoized.memoized_method
    def _get_tenant_list(self):
        try:
            tenants, has_more = api.keystone.tenant_list(self.request)
        except Exception:
            tenants = []
            msg = _('Unable to retrieve instance project information.')
            exceptions.handle(self.request, msg)

        tenant_dict = SortedDict([(t.id, t) for t in tenants])
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
            self.exception = True
        return data

    def get_data(self):
        try:
            networks = api.neutron.network_list(self.request)
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
                # If name is empty use UUID as name
                n.set_id_as_name_if_empty()
                n.num_agents = self._get_agents_data(n.id)

            if self.exception:
                msg = _('Unable to list dhcp agents hosting network.')
                exceptions.handle(self.request, msg)
        return networks


class CreateView(forms.ModalFormView):
    form_class = project_forms.CreateNetwork
    template_name = 'admin/networks/create.html'
    success_url = reverse_lazy('horizon:admin:networks:index')


class DetailView(tables.MultiTableView):
    table_classes = (subnets_tables.SubnetsTable,
                     ports_tables.PortsTable,
                     agents_tables.DHCPAgentsTable)
    template_name = 'project/networks/detail.html'
    failure_url = reverse_lazy('horizon:admin:networks:index')

    def get_subnets_data(self):
        try:
            network_id = self.kwargs['network_id']
            subnets = api.neutron.subnet_list(self.request,
                                              network_id=network_id)
        except Exception:
            subnets = []
            msg = _('Subnet list can not be retrieved.')
            exceptions.handle(self.request, msg)
        for s in subnets:
            s.set_id_as_name_if_empty()
        return subnets

    def get_ports_data(self):
        try:
            network_id = self.kwargs['network_id']
            ports = api.neutron.port_list(self.request, network_id=network_id)
        except Exception:
            ports = []
            msg = _('Port list can not be retrieved.')
            exceptions.handle(self.request, msg)
        for p in ports:
            p.set_id_as_name_if_empty()
        return ports

    def get_agents_data(self):
        agents = []
        try:
            network_id = self.kwargs['network_id']
            agents = api.neutron.list_dhcp_agent_hosting_networks(self.request,
                                                                  network_id)
        except Exception:
            msg = _('Unable to list dhcp agents hosting network.')
            exceptions.handle(self.request, msg)
        return agents

    @memoized.memoized_method
    def _get_data(self):
        try:
            network_id = self.kwargs['network_id']
            network = api.neutron.network_get(self.request, network_id)
            network.set_id_as_name_if_empty(length=0)
        except Exception:
            redirect = self.failure_url
            exceptions.handle(self.request,
                              _('Unable to retrieve details for '
                                'network "%s".') % network_id,
                                redirect=redirect)
        return network

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["network"] = self._get_data()
        # Needs to exclude agents table if dhcp-agent-scheduler extension
        # is not supported.
        try:
            dhcp_agent_support = api.neutron.is_extension_supported(
                self.request, 'dhcp_agent_scheduler')
            context['dhcp_agent_support'] = dhcp_agent_support
        except Exception:
            context['dhcp_agent_support'] = False
        return context


class UpdateView(user_views.UpdateView):
    form_class = project_forms.UpdateNetwork
    template_name = 'admin/networks/update.html'
    success_url = reverse_lazy('horizon:admin:networks:index')

    def get_initial(self):
        network = self._get_object()
        return {'network_id': network['id'],
                'tenant_id': network['tenant_id'],
                'name': network['name'],
                'admin_state': network['admin_state_up'],
                'shared': network['shared'],
                'external': network['router__external']}
