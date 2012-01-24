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

from dateutil.relativedelta import relativedelta
from django import shortcuts
from django.conf import settings
from django.contrib import messages
from django.utils.translation import ugettext as _

from horizon import api
from horizon import forms
from horizon import exceptions


LOG = logging.getLogger(__name__)


class GlobalSummary(object):
    node_resources = ['vcpus', 'disk_size', 'ram_size']
    unit_mem_size = {'disk_size': ['GB', 'TB'], 'ram_size': ['MB', 'GB']}
    node_resource_info = ['', 'active_', 'avail_']

    def __init__(self, request):
        self.summary = {}
        for rsrc in GlobalSummary.node_resources:
            for info in GlobalSummary.node_resource_info:
                self.summary['total_' + info + rsrc] = 0
        self.request = request
        self.usage_list = []

    def usage(self, start, end):
        try:
            self.usage_list = api.usage_list(self.request, start, end)
        except:
            self.usage_list = []
            exceptions.handle(self.request,
                              _('Unable to retrieve usage information on date'
                                'range %(start)s to %(end)s' % {"start": start,
                                                                "end": end}))
        for usage in self.usage_list:
            for key in usage._attrs:
                val = getattr(usage, key)
                if isinstance(val, (float, int)):
                    self.summary.setdefault(key, 0)
                    self.summary[key] += val

    def human_readable(self, rsrc):
        if self.summary['total_' + rsrc] > 1023:
            self.summary['unit_' + rsrc] = GlobalSummary.unit_mem_size[rsrc][1]
            mult = 1024.0
        else:
            self.summary['unit_' + rsrc] = GlobalSummary.unit_mem_size[rsrc][0]
            mult = 1.0

        for kind in GlobalSummary.node_resource_info:
            self.summary['total_' + kind + rsrc + '_hr'] = \
                    self.summary['total_' + kind + rsrc] / mult

    @staticmethod
    def next_month(date_start):
        return date_start + relativedelta(months=1)

    @staticmethod
    def current_month():
        today = datetime.date.today()
        return datetime.date(today.year, today.month, 1)

    @staticmethod
    def get_start_and_end_date(year, month, day=1):
        date_start = datetime.date(year, month, day)
        date_end = GlobalSummary.next_month(date_start)
        datetime_start = datetime.datetime.combine(date_start, datetime.time())
        datetime_end = datetime.datetime.combine(date_end, datetime.time())

        if date_end > datetime.date.today():
            datetime_end = datetime.datetime.utcnow()
        return date_start, date_end, datetime_start, datetime_end

    @staticmethod
    def csv_link(date_start):
        return "?date_month=%s&date_year=%s&format=csv" % (date_start.month,
                date_start.year)


def usage(request):
    today = datetime.date.today()
    dateform = forms.DateForm(request.GET, initial={'year': today.year,
                                                    "month": today.month})
    if dateform.is_valid():
        req_year = int(dateform.cleaned_data['year'])
        req_month = int(dateform.cleaned_data['month'])
    else:
        req_year = today.year
        req_month = today.month
    date_start, date_end, datetime_start, datetime_end = \
            GlobalSummary.get_start_and_end_date(req_year, req_month)

    global_summary = GlobalSummary(request)
    if date_start > GlobalSummary.current_month():
        messages.error(request, _('No data for the selected period'))
        datetime_end = datetime_start
    else:
        global_summary.usage(datetime_start, datetime_end)

    if request.GET.get('format', 'html') == 'csv':
        template = 'syspanel/tenants/usage.csv'
        mimetype = "text/csv"
    else:
        template = 'syspanel/tenants/usage.html'
        mimetype = "text/html"

    context = {'dateform': dateform,
               'datetime_start': datetime_start,
               'datetime_end': datetime_end,
               'usage_list': global_summary.usage_list,
               'csv_link': GlobalSummary.csv_link(date_start),
               'global_summary': global_summary.summary,
               'external_links': getattr(settings, 'EXTERNAL_MONITORING', [])}

    return shortcuts.render(request, template, context, content_type=mimetype)
