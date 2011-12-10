# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
# Copyright 2011 OpenStack LLC
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
Views for Instances and Volumes.
"""
import datetime
import logging

from django import http
from django import shortcuts
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions
import openstackx.api.exceptions as api_exceptions

from horizon import api
from horizon import forms
from horizon import test
from horizon.dashboards.nova.access_and_security.keypairs.forms import \
                                                                (DeleteKeypair)
from horizon.dashboards.nova.access_and_security.security_groups.forms import \
                                                                  (CreateGroup,
                                                                   DeleteGroup)
from horizon.dashboards.nova.access_and_security.floating_ips.forms import \
                                                       (ReleaseFloatingIp,
                                                        FloatingIpDisassociate,
                                                        FloatingIpAllocate)


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    tenant_id = request.user.tenant_id
    for f in (CreateGroup, DeleteGroup, DeleteKeypair, ReleaseFloatingIp,
              FloatingIpDisassociate, FloatingIpAllocate):
        _unused, handled = f.maybe_handle(request)
        if handled:
            return handled

    try:
        security_groups = api.security_group_list(request)
    except novaclient_exceptions.ClientException, e:
        security_groups = []
        LOG.exception("ClientException in security_groups index")
        messages.error(request, _('Error fetching security_groups: %s')
                                 % e.message)
    try:
        floating_ips = api.tenant_floating_ip_list(request)
    except novaclient_exceptions.ClientException, e:
        floating_ips = []
        LOG.exception("ClientException in floating ip index")
        messages.error(request,
                    _('Error fetching floating ips: %s') % e.message)
    allocate_form = FloatingIpAllocate(initial={
                                     'tenant_id': request.user.tenant_id})
    try:
        keypairs = api.keypair_list(request)
    except novaclient_exceptions.ClientException, e:
        keypairs = []
        LOG.exception("ClientException in keypair index")
        messages.error(request, _('Error fetching keypairs: %s') % e.message)

    context = {'keypairs': keypairs,
               'floating_ips': floating_ips,
               'security_groups': security_groups,
               'keypair_delete_form': DeleteKeypair(),
               'allocate_form': FloatingIpAllocate(),
               'disassociate_form': FloatingIpDisassociate(),
               'release_form': ReleaseFloatingIp(),
               'sec_group_create_form': CreateGroup(
                                            initial={'tenant_id': tenant_id}),
               'sec_group_delete_form': DeleteGroup.maybe_handle(request,
                                            initial={'tenant_id': tenant_id})}

    if request.is_ajax():
        template = 'nova/access_and_security/index_ajax.html'
        context['hide'] = True
    else:
        template = 'nova/access_and_security/index.html'

    return shortcuts.render(request, template, context)
