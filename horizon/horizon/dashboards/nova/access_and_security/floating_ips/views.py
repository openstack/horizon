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

"""
Views for managing Nova floating IPs.
"""
import logging

from django import template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import shortcuts
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon.dashboards.nova.access_and_security.floating_ips.forms import \
                             (ReleaseFloatingIp, FloatingIpAssociate,
                              FloatingIpDisassociate, FloatingIpAllocate)


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    for f in (ReleaseFloatingIp, FloatingIpDisassociate, FloatingIpAllocate):
        _unused, handled = f.maybe_handle(request)
        if handled:
            return handled
    try:
        floating_ips = api.tenant_floating_ip_list(request)
    except novaclient_exceptions.ClientException, e:
        floating_ips = []
        LOG.exception("ClientException in floating ip index")
        messages.error(request,
                       _('Error fetching floating ips: %s') % e.message)
    allocate_form = FloatingIpAllocate(initial={
                                        'tenant_id': request.user.tenant_id})
    return shortcuts.render(request,
                        'nova/access_and_security/floating_ips/index.html', {
                            'allocate_form': allocate_form,
                            'disassociate_form': FloatingIpDisassociate(),
                            'floating_ips': floating_ips,
                            'release_form': ReleaseFloatingIp()})


@login_required
def associate(request, ip_id):
    instancelist = [(server.id, 'id: %s, name: %s' %
            (server.id, server.name))
            for server in api.server_list(request)]

    form, handled = FloatingIpAssociate().maybe_handle(request, initial={
                'floating_ip_id': ip_id,
                'floating_ip': api.tenant_floating_ip_get(request, ip_id).ip,
                'instances': instancelist})
    if handled:
        return handled

    context = {'floating_ip_id': ip_id,
               'form': form}

    if request.is_ajax():
        template = 'nova/access_and_security/floating_ips/_associate.html'
        context['hide'] = True
    else:
        template = 'nova/access_and_security/floating_ips/associate.html'

    return shortcuts.render(request, template, context)


@login_required
def disassociate(request, ip_id):
    form, handled = FloatingIpDisassociate().maybe_handle(request)
    if handled:
        return handled

    return shortcuts.render(request,
                    'nova/access_and_security/floating_ips/associate.html', {
                    'floating_ip_id': ip_id})
