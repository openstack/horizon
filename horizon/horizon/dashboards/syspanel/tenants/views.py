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

import logging

from django import shortcuts
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from openstackx.api import exceptions as api_exceptions

from horizon import api
from horizon.dashboards.syspanel.tenants.forms import (AddUser, RemoveUser,
        CreateTenant, UpdateTenant, UpdateQuotas, DeleteTenant)


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    form, handled = DeleteTenant.maybe_handle(request)
    if handled:
        return handled

    tenant_delete_form = DeleteTenant()

    tenants = []
    try:
        tenants = api.tenant_list(request)
    except api_exceptions.ApiException, e:
        LOG.exception('ApiException while getting tenant list')
        messages.error(request, _('Unable to get tenant info: %s') % e.message)
    tenants.sort(key=lambda x: x.id, reverse=True)
    return shortcuts.render(request,
                            'syspanel/tenants/index.html', {
                                'tenants': tenants,
                                'tenant_delete_form': tenant_delete_form})


@login_required
def create(request):
    form, handled = CreateTenant.maybe_handle(request)
    if handled:
        return handled

    return shortcuts.render(request,
                            'syspanel/tenants/create.html', {
                                'form': form})


@login_required
def update(request, tenant_id):
    form, handled = UpdateTenant.maybe_handle(request)
    if handled:
        return handled

    if request.method == 'GET':
        try:
            tenant = api.tenant_get(request, tenant_id)
            form = UpdateTenant(initial={'id': tenant.id,
                                         'name': tenant.name,
                                         'description': tenant.description,
                                         'enabled': tenant.enabled})
        except api_exceptions.ApiException, e:
            LOG.exception('Error fetching tenant with id "%s"' % tenant_id)
            messages.error(request,
                           _('Unable to update tenant: %s') % e.message)
            return shortcuts.redirect('horizon:syspanel:tenants:index')

    return shortcuts.render(request,
                            'syspanel/tenants/update.html', {
                                'tenant_id': tenant_id,
                                'form': form})


@login_required
def users(request, tenant_id):
    for f in (AddUser, RemoveUser,):
        form, handled = f.maybe_handle(request)
        if handled:
            return handled

    add_user_form = AddUser()
    remove_user_form = RemoveUser()

    users = api.user_list(request, tenant_id)
    all_users = api.user_list(request)
    user_ids = [u.id for u in users]
    new_users = [u for u in all_users if not u.id in user_ids]
    return shortcuts.render(request,
                            'syspanel/tenants/users.html', {
                                'add_user_form': add_user_form,
                                'remove_user_form': remove_user_form,
                                'tenant_id': tenant_id,
                                'users': users,
                                'new_users': new_users})


@login_required
def quotas(request, tenant_id):
    for f in (UpdateQuotas,):
        form, handled = f.maybe_handle(request)
        if handled:
            return handled

    quotas = api.admin_api(request).quota_sets.get(tenant_id)
    quota_set = {
        'tenant_id': quotas.id,
        'metadata_items': quotas.metadata_items,
        'injected_file_content_bytes': quotas.injected_file_content_bytes,
        'volumes': quotas.volumes,
        'gigabytes': quotas.gigabytes,
        'ram': int(quotas.ram),
        'floating_ips': quotas.floating_ips,
        'instances': quotas.instances,
        'injected_files': quotas.injected_files,
        'cores': quotas.cores,
    }
    form = UpdateQuotas(initial=quota_set)

    return shortcuts.render(request,
                            'syspanel/tenants/quotas.html', {
                                'form': form,
                                'tenant_id': tenant_id,
                                'quotas': quotas})
