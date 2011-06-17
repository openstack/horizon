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
import subprocess
import urlparse

from django.contrib import messages

from django_openstack import api
from django_openstack import forms
from django_openstack.dash.views import instances as dash_instances
from openstackx.api import exceptions as api_exceptions


class ServiceToggleEnabledForm(forms.SelfHandlingForm):
    user = forms.CharField(required=True)

    def handle(self, request, data):
        service = api.admin_api(request).services.get(service_id)
        
        try:
            api.admin_api(request).services.update(service_id, not service.disabled)
            if service.disabled:
                message = 'Service Enabled'
            else:
                message = 'Service Diabled'
            messages.info(request, message)
        except api_exceptions.ApiException, e:
            messages.error(request, 'Unable to update service: %s' % e.message)

        return redirect(request.build_absolute_uri())


@login_required
def index(request):
    for f in (ServiceToggleEnabledForm,):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled

    services = []
    try:  
        services = api.admin_api(request).services.list()
    except api_exceptions.ApiException, e:
        messages.error(request, 'Unable to get service info: %s' % e.message)
        
    other_services = []
      
    for k, v in request.session['serviceCatalog'].iteritems():
        v = v[0]
        try:
            subprocess.check_call(['curl', '-m', '1', v['internalURL']])
            up = True
        except:
            up = False
        hostname = urlparse.urlparse(v['internalURL']).hostname
        row = { 'name': k, 'internalURL': v['internalURL'], 'hostname': hostname,
                'region': v['region'], 'up': up }
        other_services.append(row)
   
    return render_to_response('syspanel_services.html', {
        'services': services,
        'service_toggle_enabled_form': services,
        'other_services': other_services,
    }, context_instance = template.RequestContext(request))
