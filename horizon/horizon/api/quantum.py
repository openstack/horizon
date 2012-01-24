# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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


from __future__ import absolute_import

import logging

from django.conf import settings
from quantum import client as quantum_client

from horizon.api import nova
from horizon.api.base import *


LOG = logging.getLogger(__name__)


def quantum_api(request):
    if hasattr(request, 'user'):
        tenant = request.user.tenant_id
    else:
        tenant = settings.QUANTUM_TENANT

    return quantum_client.Client(settings.QUANTUM_URL, settings.QUANTUM_PORT,
                  False, tenant, 'json')


def quantum_list_networks(request):
    return quantum_api(request).list_networks()


def quantum_network_details(request, network_id):
    return quantum_api(request).show_network_details(network_id)


def quantum_list_ports(request, network_id):
    return quantum_api(request).list_ports(network_id)


def quantum_port_details(request, network_id, port_id):
    return quantum_api(request).show_port_details(network_id, port_id)


def quantum_create_network(request, data):
    return quantum_api(request).create_network(data)


def quantum_delete_network(request, network_id):
    return quantum_api(request).delete_network(network_id)


def quantum_update_network(request, network_id, data):
    return quantum_api(request).update_network(network_id, data)


def quantum_create_port(request, network_id):
    return quantum_api(request).create_port(network_id)


def quantum_delete_port(request, network_id, port_id):
    return quantum_api(request).delete_port(network_id, port_id)


def quantum_attach_port(request, network_id, port_id, data):
    return quantum_api(request).attach_resource(network_id, port_id, data)


def quantum_detach_port(request, network_id, port_id):
    return quantum_api(request).detach_resource(network_id, port_id)


def quantum_set_port_state(request, network_id, port_id, data):
    return quantum_api(request).update_port(network_id, port_id, data)


def quantum_port_attachment(request, network_id, port_id):
    return quantum_api(request).show_port_attachment(network_id, port_id)


def get_vif_ids(request):
    vifs = []
    attached_vifs = []
    # Get a list of all networks
    networks_list = quantum_api(request).list_networks()
    for network in networks_list['networks']:
        ports = quantum_api(request).list_ports(network['id'])
        # Get port attachments
        for port in ports['ports']:
            port_attachment = quantum_api(request).show_port_attachment(
                                                    network['id'],
                                                    port['id'])
            if port_attachment['attachment']:
                attached_vifs.append(
                    port_attachment['attachment']['id'].encode('ascii'))
    # Get all instances
    instances = nova.server_list(request)
    # Get virtual interface ids by instance
    for instance in instances:
        id = instance.id
        instance_vifs = nova.virtual_interfaces_list(request, id)
        for vif in instance_vifs:
            # Check if this VIF is already connected to any port
            if str(vif.id) in attached_vifs:
                vifs.append({
                    'id': vif.id,
                    'instance': instance.id,
                    'instance_name': instance.name,
                    'available': False})
            else:
                vifs.append({
                    'id': vif.id,
                    'instance': instance.id,
                    'instance_name': instance.name,
                    'available': True})
    return vifs
