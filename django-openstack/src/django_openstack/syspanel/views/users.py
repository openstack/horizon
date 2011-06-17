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
    password = forms.CharField(label="Password", widget=forms.PasswordInput(render_value=False))
    tenant_id = forms.ChoiceField(label="Primary Tenant")
    enabled = forms.BooleanField(label="Enabled", initial=True)


class UserDeleteForm(forms.SelfHandlingForm):
    user = forms.CharField(required=True)

    def handle(self, request, data):
        user_id = data['user']
        api.account_api(request).users.delete(user_id)
        messages.success(request,
                         '%s was successfully deleted.'
                         % user_id)
        return redirect(request.build_absolute_uri())


class UserToggleEnabledForm(forms.SelfHandlingForm):
    user = forms.CharField(required=True)

    def handle(self, request, data):
        user_id = data['user']
        messages.info(request, 'toggle not implemented %s .' % user_id)
        return redirect(request.build_absolute_uri())


@login_required
def index(request):
    for f in (UserDeleteForm, UserToggleEnabledForm):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled

    users = api.account_api(request).users.list()

    user_delete_form = UserDeleteForm()
    user_toggle_enabled_form = UserToggleEnabledForm()
    return render_to_response('syspanel_users.html',{
        'users': users,
        'user_delete_form': user_delete_form,
        'user_toggle_enabled_form': user_toggle_enabled_form,
    }, context_instance = template.RequestContext(request))


@login_required
def update(request, user_id):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            tenant = form.clean()
            # TODO Make this a real request
            # account_api(request).users.update(user['id'],
            #         user['username'], user['tenants'])
            messages.success(request,
                             '%s was successfully updated.'
                             % user['username'])
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
        tenants = api.account_api(request).tenants.list()
        form = UserForm(initial={'id': user['id']}, tenant_list=tenants)
        return render_to_response(
        'syspanel_user_update.html',{
            'form': form,
            'user_id': user_id,
        }, context_instance = template.RequestContext(request))


@login_required
def create(request):
    tenants = api.account_api(request).tenants.list()

    if request.method == "POST":
        form = UserForm(request.POST, tenant_list=tenants)
        if form.is_valid():
            user = form.clean()
            # TODO Make this a real request
            try:
                api.account_api(request).users.create(user['id'],
                                                      user['email'],
                                                      user['password'],
                                                      user['tenant_id'],
                                                      user['enabled'])

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
