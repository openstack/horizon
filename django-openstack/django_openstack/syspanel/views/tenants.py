# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from openstackx.api import exceptions as api_exceptions


class AddUser(forms.SelfHandlingForm):
    user = forms.CharField()
    tenant = forms.CharField()
    
    def handle(self, request, data):
        try:  
            api.account_api(request).role_refs.add_for_tenant_user(data['tenant'],
                    data['user'], settings.OPENSTACK_KEYSTONE_DEFAULT_ROLE)
            messages.success(request,
                             '%s was successfully added to %s.'
                             % (data['user'], data['tenant']))
        except api_exceptions.ApiException, e:
            messages.error(request, 'Unable to create user association: %s' %
                           (e.message))
        return redirect('syspanel_tenants')


class RemoveUser(forms.SelfHandlingForm):
    user = forms.CharField()
    tenant = forms.CharField()
    
    def handle(self, request, data):
        try:  
            api.account_api(request).role_refs.delete_for_tenant_user(data['tenant'],
                    data['user'], 'Member')
            messages.success(request,
                             '%s was successfully removed from %s.'
                             % (data['user'], data['tenant']))
        except api_exceptions.ApiException, e:
            messages.error(request, 'Unable to create tenant: %s' %
                           (e.message))
        return redirect('syspanel_tenants')


class CreateTenant(forms.SelfHandlingForm):
    id = forms.CharField(label="ID (name)")
    description = forms.CharField(widget=forms.widgets.Textarea(), label="Description")
    enabled = forms.BooleanField(label="Enabled", required=False, initial=True)

    def handle(self, request, data):
        try:
            api.tenant_create(request,
                              data['id'],
                              data['description'],
                              data['enabled'])
            messages.success(request,
                             '%s was successfully created.'
                             % data['id'])
        except api_exceptions.ApiException, e:
            messages.error(request, 'Unable to create tenant: %s' %
                           (e.message))
        return redirect('syspanel_tenants')


class UpdateTenant(forms.SelfHandlingForm):
    id = forms.CharField(label="ID (name)", widget=forms.TextInput(attrs={'readonly':'readonly'}))
    description = forms.CharField(widget=forms.widgets.Textarea(), label="Description")
    enabled = forms.BooleanField(label="Enabled", required=False)

    def handle(self, request, data):
        try:
            api.tenant_update(request,
                              data['id'],
                              data['description'],
                              data['enabled'])
            messages.success(request,
                             '%s was successfully updated.'
                             % data['id'])
        except api_exceptions.ApiException, e:
            messages.error(request, 'Unable to update tenant: %s' % e.message)
        return redirect('syspanel_tenants')


@login_required
def index(request):
    tenants = []
    try:
        tenants = api.tenant_list(request)
    except api_exceptions.ApiException, e:
        messages.error(request, 'Unable to get tenant info: %s' % e.message)
    tenants.sort(key=lambda x: x.id, reverse=True)
    return render_to_response('syspanel_tenants.html',{
        'tenants': tenants,
    }, context_instance = template.RequestContext(request))


@login_required
def create(request):
    form, handled = CreateTenant.maybe_handle(request)
    if handled:
        return handled

    return render_to_response(
    'syspanel_tenant_create.html',{
        'form': form,
    }, context_instance = template.RequestContext(request))


@login_required
def update(request, tenant_id):
    form, handled = UpdateTenant.maybe_handle(request)
    if handled:
        return handled

    if request.method == 'GET':
        try:
            tenant = api.tenant_get(request, tenant_id)
            form = UpdateTenant(initial={'id': tenant.id,
                                         'description': tenant.description,
                                         'enabled': tenant.enabled})
        except api_exceptions.ApiException, e:
            messages.error(request, 'Unable to update tenant: %s' % e.message)
            return redirect('syspanel_tenants')

    return render_to_response(
    'syspanel_tenant_update.html',{
        'form': form,
    }, context_instance = template.RequestContext(request))


@login_required
def users(request, tenant_id):
    for f in (AddUser, RemoveUser,):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled
#    form, handled = UpdateTenant.maybe_handle(request)
#    if handled:
#        return handled
    add_user_form = AddUser()
    remove_user_form = RemoveUser()

    users = api.account_api(request).users.get_for_tenant(tenant_id).values
    all_users = api.account_api(request).users.list()
    new_user_ids = []
    user_ids = [u['id'] for u in users]
    all_user_ids = [u.id for u in all_users]
    for uid in all_user_ids:
        if not uid in user_ids:
            new_user_ids.append(uid)
    for i in user_ids:
        if i in new_user_ids:
            new_user_ids.remove(i)
    return render_to_response(
    'syspanel_tenant_users.html',{
        'add_user_form': add_user_form,
        'remove_user_form': remove_user_form,
        'tenant_id': tenant_id,
        'users': users,
        'new_users': new_user_ids,
    }, context_instance = template.RequestContext(request))
