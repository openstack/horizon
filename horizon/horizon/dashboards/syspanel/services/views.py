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
        for i, service in enumerate(self.request.session['serviceCatalog']):
            url = service['endpoints'][0]['internalURL']
            hostname = urlparse.urlparse(url).hostname
            row = {'id': i,  # id is required for table to render properly
                   'type': service['type'],
                   'internalURL': url,
                   'host': hostname,
                   'region': service['endpoints'][0]['region'],
                   'disabled': None}
            services.append(api.base.APIDictWrapper(row))

        return services
