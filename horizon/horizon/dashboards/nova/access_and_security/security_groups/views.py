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
Views for managing Nova instances.
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import shortcuts
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon.dashboards.nova.access_and_security.security_groups.forms import \
                                (CreateGroup, DeleteGroup, AddRule, DeleteRule)


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    tenant_id = request.user.tenant_id
    delete_form, handled = DeleteGroup.maybe_handle(request,
                                initial={'tenant_id': tenant_id})
    form = CreateGroup(initial={'tenant_id': tenant_id})
    if handled:
        return handled

    try:
        security_groups = api.security_group_list(request)
    except novaclient_exceptions.ClientException, e:
        security_groups = []
        LOG.exception("ClientException in security_groups index")
        messages.error(request, _('Error fetching security_groups: %s')
                                 % e.message)

    return shortcuts.render(request,
                    'nova/access_and_security/security_groups/index.html', {
                        'security_groups': security_groups,
                        'form': form,
                        'delete_form': delete_form})


@login_required
def edit_rules(request, security_group_id):
    tenant_id = request.user.tenant_id
    add_form, handled = AddRule.maybe_handle(request,
                           initial={'tenant_id': tenant_id,
                                      'security_group_id': security_group_id})
    if handled:
        return handled

    delete_form, handled = DeleteRule.maybe_handle(request,
                              initial={'tenant_id': tenant_id,
                                       'security_group_id': security_group_id})
    if handled:
        return handled

    try:
        security_group = api.security_group_get(request, security_group_id)
    except novaclient_exceptions.ClientException, e:
        LOG.exception("ClientException in security_groups rules edit")
        messages.error(request, _('Error getting security_group: %s')
                                  % e.message)
        return shortcuts.redirect('horizon:nova:access_and_security:index')

    return shortcuts.render(request,
                'nova/access_and_security/security_groups/edit_rules.html', {
                    'security_group': security_group,
                    'delete_form': delete_form,
                    'form': add_form})


@login_required
def create(request):
    tenant_id = request.user.tenant_id
    form, handled = CreateGroup.maybe_handle(request,
                                initial={'tenant_id': tenant_id})
    if handled:
        return handled

    return shortcuts.render(request,
                    'nova/access_and_security/security_groups/create.html', {
                        'form': form})
