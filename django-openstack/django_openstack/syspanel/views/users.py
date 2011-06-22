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



class UserForm(forms.Form):
    def __init__(self, *args, **kwargs):
        tenant_list = kwargs.pop('tenant_list', None)
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['tenant_id'].choices = [[tenant.id,tenant.id] for tenant in tenant_list]

    id = forms.CharField(label="ID")
    email = forms.CharField(label="Email")
    password = forms.CharField(label="Password", widget=forms.PasswordInput(render_value=False), required=False)
    tenant_id = forms.ChoiceField(label="Primary Tenant")


class UserDeleteForm(forms.SelfHandlingForm):
    user = forms.CharField(required=True)

    def handle(self, request, data):
        user_id = data['user']
        api.user_delete(request, user_id)
        messages.success(request,
                         '%s was successfully deleted.'
                         % user_id)
        return redirect(request.build_absolute_uri())


@login_required
def index(request):
    for f in (UserDeleteForm,):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled

    users = api.user_list(request)

    user_delete_form = UserDeleteForm()
    return render_to_response('syspanel_users.html',{
        'users': users,
        'user_delete_form': user_delete_form,
    }, context_instance = template.RequestContext(request))


@login_required
def update(request, user_id):
    if request.method == "POST":
        tenants = api.tenant_list(request)
        form = UserForm(request.POST, tenant_list=tenants)
        if form.is_valid():
            user = form.clean()
            updated = []
            if user['email']:
                updated.append('email')
                api.user_update_email(request, user['id'], user['email'])
            if user['password']:
                updated.append('password')
                api.user_update_password(request, user['id'], user['password'])
            if user['tenant_id']:
                updated.append('tenant')
                api.user_update_tenant(request, user['id'], user['tenant_id'])
            messages.success(request,
                             'Updated %s for %s.'
                             % (', '.join(updated), user_id))
            return redirect('syspanel_users')
        else:
            # TODO add better error management
            messages.error(request, 'Unable to update user,\
                                    please try again.')

            return render_to_response(
            'syspanel_user_update.html',{
                'form': form,
                'user_id': user_id,
            }, context_instance = template.RequestContext(request))

    else:
        u = api.user_get(request, user_id)
        tenants = api.tenant_list(request)
        try:
            # FIXME
            email = u.email
        except:
            email = ''

        try:
            tenant_id = u.tenantId
        except:
            tenant_id = None
        form = UserForm(initial={'id': user_id,
                                 'tenant_id': tenant_id,
                                 'email': email},
                                 tenant_list=tenants)
        return render_to_response(
        'syspanel_user_update.html',{
            'form': form,
            'user_id': user_id,
        }, context_instance = template.RequestContext(request))


@login_required
def create(request):
    tenants = api.tenant_list(request)

    if request.method == "POST":
        form = UserForm(request.POST, tenant_list=tenants)
        if form.is_valid():
            user = form.clean()
            # TODO Make this a real request
            try:
                api.user_create(request,
                                user['id'],
                                user['email'],
                                user['password'],
                                user['tenant_id'],
                                True)

                messages.success(request,
                                 '%s was successfully created.'
                                 % user['id'])
                return redirect('syspanel_users')

            except api_exceptions.ApiException, e:
                messages.error(request,
                                 'Error creating user: %s'
                                 % e.message)
                return redirect('syspanel_users')
        else:
            return render_to_response(
            'syspanel_user_create.html',{
                'form': form,
            }, context_instance = template.RequestContext(request))

    else:
        form = UserForm(tenant_list=tenants)
        return render_to_response(
        'syspanel_user_create.html',{
            'form': form,
        }, context_instance = template.RequestContext(request))
