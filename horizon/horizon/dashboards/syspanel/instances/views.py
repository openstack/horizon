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

import datetime
import logging

from django import template
from django import http
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.dashboards.nova.instances_and_volumes \
     .instances.tables import InstancesTable
from horizon.dashboards.nova.instances_and_volumes \
     .instances.views import console, DetailView, vnc


LOG = logging.getLogger(__name__)


class AdminIndexView(tables.DataTableView):
    table_class = InstancesTable
    template_name = 'syspanel/instances/index.html'

    def get_data(self):
        instances = []
        try:
            instances = api.admin_server_list(self.request)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve instance list.'))
        return instances
