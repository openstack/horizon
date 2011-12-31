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
import os
import subprocess
import urlparse

from django import shortcuts
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from openstackx.api import exceptions as api_exceptions

from horizon import api
from horizon.dashboards.syspanel.services.forms import ToggleService


LOG = logging.getLogger(__name__)


@login_required
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

    return shortcuts.render(request,
                            'syspanel/services/index.html', {
                                'services': services,
                                'service_toggle_enabled_form': ToggleService,
                                'other_services': other_services})
