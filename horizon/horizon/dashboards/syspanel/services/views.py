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
from django.utils.translation import ugettext as _
from openstackx.api import exceptions as api_exceptions

from horizon import api
from horizon import tables
from .tables import ServicesTable


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = ServicesTable
    template_name = 'syspanel/services/index.html'

    def get_data(self):
        services = []
        try:
            services = api.service_list(self.request)
        except api_exceptions.ApiException, e:
            LOG.exception('ApiException fetching service list')
            messages.error(self.request,
                           _('Unable to get service info: %s') % e.message)

        other_services = []
        for service in self.request.session['serviceCatalog']:
            url = service['endpoints'][0]['internalURL']
            hostname = urlparse.urlparse(url).hostname
            row = {'id': None,
                   'type': service['type'],
                   'internalURL': url,
                   'host': hostname,
                   'region': service['endpoints'][0]['region'],
                   'disabled': None}
            other_services.append(api.base.APIDictWrapper(row))

        services = sorted(services, key=lambda svc: (svc.type +
                                                     svc.host))
        other_services = sorted(other_services, key=lambda svc: (svc['type'] +
                                                                 svc['host']))
        all_services = services + other_services
        return all_services
