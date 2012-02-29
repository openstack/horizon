# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

"""
Views for managing Quantum networks.
"""

import logging

from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.dashboards.nova.networks.forms import (CreateNetwork,
        RenameNetwork, AttachPort, CreatePort)
from .tables import NetworksTable, NetworkDetailsTable


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = NetworksTable
    template_name = 'nova/networks/index.html'

    def get_data(self):
        tenant_id = self.request.user.tenant_id
        networks = []

        try:
            networks_list = api.quantum_list_networks(self.request)
            details = []
            for network in networks_list['networks']:
                net_stats = _calc_network_stats(self.request, network['id'])
                # Get network details like name and id
                details = api.quantum_network_details(self.request,
                                                      network['id'])
                networks.append({
                        'name': details['network']['name'],
                        'id': network['id'],
                        'total': net_stats['total'],
                        'available': net_stats['available'],
                        'used': net_stats['used'],
                        'tenant': tenant_id})
        except Exception, e:
            LOG.exception("Unable to get network list.")
            if not hasattr(e, 'message'):
                e.message = str(e)
            messages.error(self.request,
                           _('Unable to get network list: %s') % e.message)
        return networks


class CreateView(forms.ModalFormView):
    form_class = CreateNetwork
    template_name = 'nova/networks/create.html'


class RenameView(forms.ModalFormView):
    form_class = RenameNetwork
    template_name = 'nova/networks/rename.html'
    context_object_name = 'network'

    def get_object(self, *args, **kwargs):
        network_id = kwargs['network_id']
        try:
            return api.quantum_network_details(self.request,
                                               network_id)['network']
        except:
            redirect = reverse("horizon:nova:networks:detail",
                               args=(network_id,))
            exceptions.handle(self.request,
                              _('Unable to retrieve network information.'),
                              redirect=redirect)

    def get_initial(self):
        return {'network': self.object['id']}


class DetailView(tables.DataTableView):
    table_class = NetworkDetailsTable
    template_name = 'nova/networks/detail.html'

    def get_data(self):
        network_id = self.kwargs['network_id']
        network_details = api.quantum_network_details(self.request, network_id)
        self.network = {'id': network_id,
                        'name': network_details['network']['name'],
                        'ports': _get_port_states(self.request, network_id)}
        return self.network['ports']

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['network'] = self.network
        return context


def _get_port_states(request, network_id):
    """
    Helper method to find port states for a network
    """
    network_ports = []
    # Get all vifs for comparison with port attachments
    vifs = api.get_vif_ids(request)

    # Get all ports on this network
    ports = api.quantum_list_ports(request, network_id)
    for port in ports['ports']:
        port_details = api.quantum_port_details(request,
                                                network_id, port['id'])
        # Get port attachments
        port_attachment = api.quantum_port_attachment(request,
                                                      network_id, port['id'])
        # Find instance the attachment belongs to
        connected_instance = None
        if port_attachment['attachment']:
            for vif in vifs:
                if str(vif['id']) == str(port_attachment['attachment']['id']):
                    connected_instance = vif['id']
                    break
        network_ports.append({
            'id': port_details['port']['id'],
            'state': port_details['port']['state'],
            'attachment': port_attachment['attachment'],
            'instance': connected_instance})
    return network_ports


def _calc_network_stats(request, network_id):
    """
    Helper method to calculate statistics for a network
    """
    # Get all ports statistics for the network
    total = 0
    available = 0
    used = 0
    ports = api.quantum_list_ports(request, network_id)
    for port in ports['ports']:
        total += 1
        # Get port attachment
        port_attachment = api.quantum_port_attachment(request,
                                                      network_id, port['id'])
        if port_attachment['attachment']:
            used += 1
        else:
            available += 1

    return {'total': total, 'used': used, 'available': available}


class CreatePortView(forms.ModalFormView):
    form_class = CreatePort
    template_name = 'nova/networks/ports/create.html'
    context_object_name = 'port'

    def get_object(self, *args, **kwargs):
        network_id = kwargs['network_id']
        try:
            return api.quantum_network_details(self.request,
                                               network_id)['network']
        except:
            redirect = reverse("horizon:nova:networks:detail",
                               args=(network_id,))
            exceptions.handle(self.request,
                              _('Unable to retrieve network information.'),
                              redirect=redirect)

    def get_initial(self):
        return {'network': self.object['id']}


class AttachPortView(forms.ModalFormView):
    form_class = AttachPort
    template_name = 'nova/networks/ports/attach.html'
    context_object_name = 'network'

    def get_object(self, *args, **kwargs):
        network_id = kwargs['network_id']
        try:
            return api.quantum_network_details(self.request,
                                               network_id)['network']
        except:
            redirect = reverse("horizon:nova:networks:detail",
                               args=(network_id,))
            exceptions.handle(self.request,
                              _('Unable to attach port.'),
                              redirect=redirect)

    def get_initial(self):
        return {'network': self.object['id']}
