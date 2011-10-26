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
import os
import subprocess
import sys
import urlparse

from django.contrib import messages

from django_openstack import api
from django_openstack import forms
from django_openstack.dash.views import instances as dash_instances
from django_openstack.decorators import enforce_admin_access
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
                messages.info(request, _("Service '%s' has been enabled")
                                        % data['name'])
            else:
                messages.info(request, _("Service '%s' has been disabled")
                                        % data['name'])
        except api_exceptions.ApiException, e:
            LOG.exception('ApiException while toggling service %s' %
                      data['service'])
            messages.error(request,
                           _("Unable to update service '%(name)s': %(msg)s")
                           % {"name": data['name'], "msg": e.message})

        return redirect(request.build_absolute_uri())


@login_required
@enforce_admin_access
def index(request):
    for f in (ToggleService,):
        form, handled = f.maybe_handle(request)
        if handled:
            return handled

    services = []
    try:
        services = api.service_list(request)
    except api_exceptions.ApiException, e:
        LOG.exception('ApiException fetching service list')
        messages.error(request,
                       _('Unable to get service info: %s') % e.message)

    other_services = []

    for service in request.session['serviceCatalog']:
        url = service['endpoints'][0]['internalURL']
        try:
            # TODO(mgius): This silences curl, but there's probably
            # a better solution than using curl to begin with
            subprocess.check_call(['curl', '-m', '1', url],
                                  stdout=open(os.devnull, 'w'),
                                  stderr=open(os.devnull, 'w'))
            up = True
        except:
            up = False
        hostname = urlparse.urlparse(url).hostname
        row = {'type': service['type'], 'internalURL': url, 'host': hostname,
               'region': service['endpoints'][0]['region'], 'up': up}
        other_services.append(row)

    services = sorted(services, key=lambda svc: (svc.type +
                                                 svc.host))
    other_services = sorted(other_services, key=lambda svc: (svc['type'] +
                                                             svc['host']))

    return render_to_response(
    'django_openstack/syspanel/services/index.html', {
        'services': services,
        'service_toggle_enabled_form': ToggleService,
        'other_services': other_services,
    }, context_instance=template.RequestContext(request))
