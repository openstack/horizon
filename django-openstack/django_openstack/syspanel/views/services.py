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
import sys
import urlparse

from django.contrib import messages

from django_openstack import api
from django_openstack import forms
from django_openstack.dash.views import instances as dash_instances
from openstackx.api import exceptions as api_exceptions

LOG = logging.getLogger('django_openstack.syspanel.views.services')


class ToggleService(forms.SelfHandlingForm):
    service = forms.CharField(required=False)
    name = forms.CharField(required=False)

    def handle(self, request, data):
        try:
            service = api.service_get(request, data['service'])
            api.service_update(request,
                               data['service'],
                               not service.disabled)
            if service.disabled:
                messages.info(request, "Service '%s' has been enabled"
                                        % data['name'])
            else:
                messages.info(request, "Service '%s' has been disabled"
                                        % data['name'])
        except api_exceptions.ApiException, e:
            LOG.error('ApiException while toggling service %s' %
                      data['service'], exc_info=True)
            messages.error(request, "Unable to update service '%s': %s"
                                     % data['name'], e.message)

        return redirect(request.build_absolute_uri())


@login_required
def index(request):
    for f in (ToggleService,):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled

    services = []
    try:
        services = api.service_list(request)
    except api_exceptions.ApiException, e:
        LOG.error('ApiException fetching service list', exc_info=True)
        messages.error(request, 'Unable to get service info: %s' % e.message)

    other_services = []

    for k, v in request.session['serviceCatalog'].iteritems():
        v = v[0]
        try:
            # TODO(mgius): This silences curl, but there's probably
            # a better solution than using curl to begin with
            subprocess.check_call(['curl', '-m', '1', v['internalURL']],
                                  stdout=open(sys.devnull, 'w'),
                                  stderr=open(sys.devnull, 'w'))
            up = True
        except:
            up = False
        hostname = urlparse.urlparse(v['internalURL']).hostname
        row = {'type': k, 'internalURL': v['internalURL'], 'host': hostname,
               'region': v['region'], 'up': up }
        other_services.append(row)

    return render_to_response('syspanel_services.html', {
        'services': services,
        'service_toggle_enabled_form': ToggleService,
        'other_services': other_services,
    }, context_instance = template.RequestContext(request))
