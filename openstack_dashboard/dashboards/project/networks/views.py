# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
Views for managing Quantum Networks.
"""
import logging

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import workflows

from openstack_dashboard import api
from .tables import NetworksTable
from .subnets.tables import SubnetsTable
from .ports.tables import PortsTable
from .forms import UpdateNetwork
from .workflows import CreateNetwork


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = NetworksTable
    template_name = 'project/networks/index.html'

    def get_data(self):
        try:
            tenant_id = self.request.user.tenant_id
            networks = api.quantum.network_list_for_tenant(self.request,
                                                           tenant_id)
        except:
            networks = []
            msg = _('Network list can not be retrieved.')
            exceptions.handle(self.request, msg)
        for n in networks:
            n.set_id_as_name_if_empty()
        return networks


class CreateView(workflows.WorkflowView):
    workflow_class = CreateNetwork
    template_name = 'project/networks/create.html'

    def get_initial(self):
        pass


class UpdateView(forms.ModalFormView):
    form_class = UpdateNetwork
    template_name = 'project/networks/update.html'
    context_object_name = 'network'
    success_url = reverse_lazy("horizon:project:networks:index")

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context["network_id"] = self.kwargs['network_id']
        return context

    def _get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            network_id = self.kwargs['network_id']
            try:
                self._object = api.quantum.network_get(self.request,
                                                       network_id)
            except:
                redirect = self.success_url
                msg = _('Unable to retrieve network details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_initial(self):
        network = self._get_object()
        return {'network_id': network['id'],
                'tenant_id': network['tenant_id'],
                'name': network['name'],
                'admin_state': network['admin_state_up']}


class DetailView(tables.MultiTableView):
    table_classes = (SubnetsTable, PortsTable)
    template_name = 'project/networks/detail.html'
    failure_url = reverse_lazy('horizon:project:networks:index')

    def get_subnets_data(self):
        try:
            network = self._get_data()
            subnets = api.quantum.subnet_list(self.request,
                                              network_id=network.id)
        except:
            subnets = []
            msg = _('Subnet list can not be retrieved.')
            exceptions.handle(self.request, msg)
        for s in subnets:
            s.set_id_as_name_if_empty()
        return subnets

    def get_ports_data(self):
        try:
            network_id = self.kwargs['network_id']
            ports = api.quantum.port_list(self.request, network_id=network_id)
        except:
            ports = []
            msg = _('Port list can not be retrieved.')
            exceptions.handle(self.request, msg)
        for p in ports:
            p.set_id_as_name_if_empty()
        return ports

    def _get_data(self):
        if not hasattr(self, "_network"):
            try:
                network_id = self.kwargs['network_id']
                network = api.quantum.network_get(self.request, network_id)
                network.set_id_as_name_if_empty(length=0)
            except:
                msg = _('Unable to retrieve details for network "%s".') \
                      % (network_id)
                exceptions.handle(self.request, msg, redirect=self.failure_url)
            self._network = network
        return self._network

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["network"] = self._get_data()
        return context
