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

"""
Views for managing Neutron Networks.
"""
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.networks \
    import forms as project_forms
from openstack_dashboard.dashboards.project.networks.ports \
    import tables as port_tables
from openstack_dashboard.dashboards.project.networks.subnets \
    import tables as subnet_tables
from openstack_dashboard.dashboards.project.networks \
    import tables as project_tables
from openstack_dashboard.dashboards.project.networks \
    import workflows as project_workflows


class IndexView(tables.DataTableView):
    table_class = project_tables.NetworksTable
    template_name = 'project/networks/index.html'
    page_title = _("Networks")

    def get_data(self):
        try:
            tenant_id = self.request.user.tenant_id
            networks = api.neutron.network_list_for_tenant(self.request,
                                                           tenant_id)
        except Exception:
            networks = []
            msg = _('Network list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return networks


class CreateView(workflows.WorkflowView):
    workflow_class = project_workflows.CreateNetwork
    ajax_template_name = 'project/networks/create.html'


class UpdateView(forms.ModalFormView):
    context_object_name = 'network'
    form_class = project_forms.UpdateNetwork
    form_id = "update_network_form"
    modal_header = _("Edit Network")
    submit_label = _("Save Changes")
    submit_url = "horizon:project:networks:update"
    success_url = reverse_lazy("horizon:project:networks:index")
    template_name = 'project/networks/update.html'
    page_title = _("Update Network")

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        args = (self.kwargs['network_id'],)
        context["network_id"] = self.kwargs['network_id']
        context["submit_url"] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        network_id = self.kwargs['network_id']
        try:
            return api.neutron.network_get(self.request, network_id)
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve network details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        network = self._get_object()
        return {'network_id': network['id'],
                'tenant_id': network['tenant_id'],
                'name': network['name'],
                'admin_state': network['admin_state_up']}


class DetailView(tables.MultiTableView):
    table_classes = (subnet_tables.SubnetsTable, port_tables.PortsTable)
    template_name = 'project/networks/detail.html'
    page_title = _("Network Details: {{ network.name }}")

    def get_subnets_data(self):
        try:
            network = self._get_data()
            subnets = api.neutron.subnet_list(self.request,
                                              network_id=network.id)
        except Exception:
            subnets = []
            msg = _('Subnet list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return subnets

    def get_ports_data(self):
        try:
            network_id = self.kwargs['network_id']
            ports = api.neutron.port_list(self.request, network_id=network_id)
        except Exception:
            ports = []
            msg = _('Port list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return ports

    @memoized.memoized_method
    def _get_data(self):
        try:
            network_id = self.kwargs['network_id']
            network = api.neutron.network_get(self.request, network_id)
            network.set_id_as_name_if_empty(length=0)
        except Exception:
            msg = _('Unable to retrieve details for network "%s".') \
                % (network_id)
            exceptions.handle(self.request, msg,
                              redirect=self.get_redirect_url())
        return network

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        network = self._get_data()
        context["network"] = network
        table = project_tables.NetworksTable(self.request)
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(network)
        return context

    @staticmethod
    def get_redirect_url():
        return reverse_lazy('horizon:project:networks:index')
