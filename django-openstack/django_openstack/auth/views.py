# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django import http
from django import template
from django import shortcuts
from django.contrib import messages

from django_openstack import api
from django_openstack import forms
from openstackx.api import exceptions as api_exceptions


class Login(forms.SelfHandlingForm):
    username = forms.CharField(max_length="20", label="User Name")
    password = forms.CharField(max_length="20", label="Password")

    def handle(self, request, data):
        try:
            token = api.token_create(request,
                                     "",
                                     data['username'],
                                     data['password'])
            info = api.token_info(request, token)
            request.session['token'] = token.id
            request.session['user'] = info['user']
            request.session['tenant'] = info['tenant']
            request.session['admin'] = info['admin']
            request.session['serviceCatalog'] = token.serviceCatalog
            logging.info(token.serviceCatalog)

            if request.session['admin']:
                return shortcuts.redirect('syspanel_overview')
            else:
                return shortcuts.redirect('dash_overview')

        except api_exceptions.Unauthorized as e:
            messages.error(request, 'Error authenticating: %s' % e.message)


def login(request):
    if request.user and request.user.is_authenticated():
        if request.user.is_admin():
            return shortcuts.redirect('syspanel_overview')
        else:
            return shortcuts.redirect('dash_overview')

    form, handled = Login.maybe_handle(request)
    if handled:
        return handled

    return shortcuts.render_to_response('login_required.html', {
        'form': form,
    }, context_instance=template.RequestContext(request))


def switch_tenants(request, tenant_id):
    form, handled = Login.maybe_handle(
            request, initial={'tenant': tenant_id})
    if handled:
        return handled

    return shortcuts.render_to_response('switch_tenants.html', {
        'to_tenant': tenant_id,
        'form': form,
    }, context_instance=template.RequestContext(request))


def logout(request):
    request.session.clear()
    return shortcuts.redirect('splash')
