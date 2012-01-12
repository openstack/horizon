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

from __future__ import division

import datetime
import logging

from django import http
from django import shortcuts
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext as _

import horizon
from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import test
from horizon import views


LOG = logging.getLogger(__name__)


def usage(request, tenant_id=None):
    tenant_id = tenant_id or request.user.tenant_id
    today = test.today()
    date_start = datetime.date(today.year, today.month, 1)
    datetime_start = datetime.datetime.combine(date_start, test.time())
    datetime_end = test.utcnow()

    show_terminated = request.GET.get('show_terminated', False)

    try:
        usage = api.usage_get(request, tenant_id, datetime_start, datetime_end)
    except:
        usage = api.nova.Usage(None)
        redirect = reverse("horizon:nova:overview:index")
        exceptions.handle(request,
                          _('Unable to retrieve usage information.'))

    ram_unit = "MB"
    total_ram = getattr(usage, 'total_active_ram_size', 0)
    if total_ram >= 1024:
        ram_unit = "GB"
        total_ram /= 1024

    instances = []
    terminated = []

    if hasattr(usage, 'instances'):
        now = datetime.datetime.now()
        for i in usage.instances:
            i['uptime_at'] = now - datetime.timedelta(seconds=i['uptime'])
            if i['ended_at'] and not show_terminated:
                terminated.append(i)
            else:
                instances.append(i)

    if request.GET.get('format', 'html') == 'csv':
        template = 'nova/overview/usage.csv'
        mimetype = "text/csv"
    else:
        template = 'nova/overview/usage.html'
        mimetype = "text/html"

    dash_url = horizon.get_dashboard('nova').get_absolute_url()

    return shortcuts.render(request, template, {
                                'usage': usage,
                                'ram_unit': ram_unit,
                                'total_ram': total_ram,
                                'csv_link': '?format=csv',
                                'show_terminated': show_terminated,
                                'datetime_start': datetime_start,
                                'datetime_end': datetime_end,
                                'instances': instances,
                                'dash_url': dash_url},
                            content_type=mimetype)
