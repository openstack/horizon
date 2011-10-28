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

from django import template
from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

import datetime
import json
import logging

from django.contrib import messages

from django_openstack import api
from django_openstack import forms
from django_openstack.dash.views import instances as dash_instances
from django_openstack.decorators import enforce_admin_access
from openstackx.api import exceptions as api_exceptions


LOG = logging.getLogger('django_openstack.syspanel.views.tenants')


class AddUser(forms.SelfHandlingForm):
    user = forms.CharField()
    tenant = forms.CharField()

    def handle(self, request, data):
        try:
            api.role_add_for_tenant_user(
                    request,
                    data['tenant'],
                    data['user'],
                    settings.OPENSTACK_KEYSTONE_DEFAULT_ROLE)
            messages.success(request,
                            _('%(user)s was successfully added to %(tenant)s.')
                            % {"user": data['user'], "tenant": data['tenant']})
        except api_exceptions.ApiException, e:
            messages.error(request, _('Unable to create user association: %s')
                           % (e.message))
        return redirect('syspanel_tenant_users', tenant_id=data['tenant'])


class RemoveUser(forms.SelfHandlingForm):
    user = forms.CharField()
    tenant = forms.CharField()

    def handle(self, request, data):
        try:
            api.role_delete_for_tenant_user(
                    request,
                    data['tenant'],
                    data['user'],
                    settings.OPENSTACK_KEYSTONE_DEFAULT_ROLE)
            messages.success(request,
                        _('%(user)s was successfully removed from %(tenant)s.')
                        % {"user": data['user'], "tenant": data['tenant']})
        except api_exceptions.ApiException, e:
            messages.error(request, _('Unable to create tenant: %s') %
                           (e.message))
        return redirect('syspanel_tenant_users', tenant_id=data['tenant'])


class CreateTenant(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"))
    description = forms.CharField(widget=forms.widgets.Textarea(),
            label=_("Description"))
    enabled = forms.BooleanField(label=_("Enabled"), required=False,
            initial=True)

    def handle(self, request, data):
        try:
            LOG.info('Creating tenant with name "%s"' % data['name'])
            api.tenant_create(request,
                              data['name'],
                              data['description'],
                              data['enabled'])
            messages.success(request,
                             _('%s was successfully created.')
                             % data['name'])
        except api_exceptions.ApiException, e:
            LOG.exception('ApiException while creating tenant\n'
                      'Id: "%s", Description: "%s", Enabled "%s"' %
                      (data['name'], data['description'], data['enabled']))
            messages.error(request, _('Unable to create tenant: %s') %
                           (e.message))
        return redirect('syspanel_tenants')


class UpdateTenant(forms.SelfHandlingForm):
    id = forms.CharField(label=_("ID"),
            widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    name = forms.CharField(label=_("Name"),
            widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    description = forms.CharField(widget=forms.widgets.Textarea(),
            label=_("Description"))
    enabled = forms.BooleanField(required=False, label=_("Enabled"))

    def handle(self, request, data):
        try:
            LOG.info('Updating tenant with id "%s"' % data['id'])
            api.tenant_update(request,
                              data['id'],
                              data['name'],
                              data['description'],
                              data['enabled'])
            messages.success(request,
                             _('%s was successfully updated.')
                             % data['name'])
        except api_exceptions.ApiException, e:
            LOG.exception('ApiException while updating tenant\n'
                      'Id: "%s", Name: "%s", Description: "%s", Enabled "%s"' %
                      (data['id'], data['name'],
                       data['description'], data['enabled']))
            messages.error(request,
                           _('Unable to update tenant: %s') % e.message)
        return redirect('syspanel_tenants')


class UpdateQuotas(forms.SelfHandlingForm):
    tenant_id = forms.CharField(label=_("ID (name)"),
            widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    metadata_items = forms.CharField(label=_("Metadata Items"))
    injected_files = forms.CharField(label=_("Injected Files"))
    injected_file_content_bytes = forms.CharField(label=_("Injected File "
                                                          "Content Bytes"))
    cores = forms.CharField(label=_("VCPUs"))
    instances = forms.CharField(label=_("Instances"))
    volumes = forms.CharField(label=_("Volumes"))
    gigabytes = forms.CharField(label=_("Gigabytes"))
    ram = forms.CharField(label=_("RAM (in MB)"))
    floating_ips = forms.CharField(label=_("Floating IPs"))

    def handle(self, request, data):
        try:
            api.admin_api(request).quota_sets.update(data['tenant_id'],
               metadata_items=data['metadata_items'],
               injected_file_content_bytes=data['injected_file_content_bytes'],
               volumes=data['volumes'],
               gigabytes=data['gigabytes'],
               ram=int(data['ram']),
               floating_ips=data['floating_ips'],
               instances=data['instances'],
               injected_files=data['injected_files'],
               cores=data['cores'],
            )
            messages.success(request,
                             _('Quotas for %s were successfully updated.')
                             % data['tenant_id'])
        except api_exceptions.ApiException, e:
            messages.error(request,
                           _('Unable to update quotas: %s') % e.message)
        return redirect('syspanel_tenants')


class DeleteTenant(forms.SelfHandlingForm):
    tenant_id = forms.CharField(required=True)

    def handle(self, request, data):
        tenant_id = data['tenant_id']
        try:
            api.tenant_delete(request, tenant_id)
            messages.info(request, _('Successfully deleted tenant %(tenant)s.')
                                     % {"tenant": tenant_id})
        except Exception, e:
            LOG.exception("Error deleting tenant")
            messages.error(request,
                           _("Error deleting tenant: %s") % e.message)
        return redirect(request.build_absolute_uri())


@login_required
@enforce_admin_access
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
    return render_to_response(
    'django_openstack/syspanel/tenants/index.html', {
        'tenants': tenants,
        'tenant_delete_form': tenant_delete_form,
    }, context_instance=template.RequestContext(request))


@login_required
@enforce_admin_access
def create(request):
    form, handled = CreateTenant.maybe_handle(request)
    if handled:
        return handled

    return render_to_response(
    'django_openstack/syspanel/tenants/create.html', {
        'form': form,
    }, context_instance=template.RequestContext(request))


@login_required
@enforce_admin_access
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
            return redirect('syspanel_tenants')

    return render_to_response(
    'django_openstack/syspanel/tenants/update.html', {
        'form': form,
    }, context_instance=template.RequestContext(request))


@login_required
@enforce_admin_access
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
    return render_to_response(
    'django_openstack/syspanel/tenants/users.html', {
        'add_user_form': add_user_form,
        'remove_user_form': remove_user_form,
        'tenant_id': tenant_id,
        'users': users,
        'new_users': new_users,
    }, context_instance=template.RequestContext(request))


@login_required
@enforce_admin_access
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

    return render_to_response(
    'django_openstack/syspanel/tenants/quotas.html', {
        'form': form,
        'tenant_id': tenant_id,
        'quotas': quotas,
    }, context_instance=template.RequestContext(request))
