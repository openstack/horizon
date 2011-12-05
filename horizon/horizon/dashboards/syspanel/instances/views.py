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
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.utils.translation import ugettext as _

from horizon import api
from horizon import forms
from horizon.dashboards.nova.instances_and_volumes.instances.forms import \
                                            (TerminateInstance, RebootInstance)
from openstackx.api import exceptions as api_exceptions


LOG = logging.getLogger(__name__)


class GlobalSummary(object):
    node_resources = ['vcpus', 'disk_size', 'ram_size']
    unit_mem_size = {'disk_size': ['GiB', 'TiB'], 'ram_size': ['MiB', 'GiB']}
    node_resource_info = ['', 'active_', 'avail_']

    def __init__(self, request):
        self.summary = {}
        for rsrc in GlobalSummary.node_resources:
            for info in GlobalSummary.node_resource_info:
                self.summary['total_' + info + rsrc] = 0
        self.request = request
        self.service_list = []
        self.usage_list = []

    def service(self):
        try:
            self.service_list = api.service_list(self.request)
        except api_exceptions.ApiException, e:
            self.service_list = []
            LOG.exception('ApiException fetching service list '
                          'in instance usage')
            messages.error(self.request,
                           _('Unable to get service info: %s') % e.message)
            return

        for service in self.service_list:
            if service.type == 'nova-compute':
                self.summary['total_vcpus'] += min(service.stats['max_vcpus'],
                        service.stats.get('vcpus', 0))
                self.summary['total_disk_size'] += min(
                        service.stats['max_gigabytes'],
                        service.stats.get('local_gb', 0))
                self.summary['total_ram_size'] += min(
                        service.stats['max_ram'],
                        service.stats['memory_mb']) if 'max_ram' \
                                in service.stats \
                                else service.stats.get('memory_mb', 0)

    def usage(self, datetime_start, datetime_end):
        try:
            self.usage_list = api.usage_list(self.request, datetime_start,
                    datetime_end)
        except api_exceptions.ApiException, e:
            self.usage_list = []
            LOG.exception('ApiException fetching usage list in instance usage'
                      ' on date range "%s to %s"' % (datetime_start,
                                                     datetime_end))
            messages.error(self.request,
                    _('Unable to get usage info: %s') % e.message)
            return

        for usage in self.usage_list:
            # FIXME: api needs a simpler dict interface (with iteration)
            # - anthony
            # NOTE(mgius): Changed this on the api end.  Not too much
            # neater, but at least its not going into private member
            # data of an external class anymore
            # usage = usage._info
            for k in usage._attrs:
                v = usage.__getattr__(k)
                if type(v) in [float, int]:
                    if not k in self.summary:
                        self.summary[k] = 0
                    self.summary[k] += v

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

    def avail(self):
        for rsrc in GlobalSummary.node_resources:
            self.summary['total_avail_' + rsrc] = \
                    self.summary['total_' + rsrc] - \
                    self.summary['total_active_' + rsrc]


def _next_month(date_start):
    y = date_start.year + (date_start.month + 1) / 13
    m = ((date_start.month + 1) % 13)
    if m == 0:
        m = 1
    return datetime.date(y, m, 1)


def _current_month():
    today = datetime.date.today()
    return datetime.date(today.year, today.month, 1)


def _get_start_and_end_date(request):
    try:
        date_start = datetime.date(
                int(request.GET['date_year']),
                int(request.GET['date_month']),
                1)
    except:
        today = datetime.date.today()
        date_start = datetime.date(today.year, today.month, 1)

    date_end = _next_month(date_start)
    datetime_start = datetime.datetime.combine(date_start, datetime.time())
    datetime_end = datetime.datetime.combine(date_end, datetime.time())

    if date_end > datetime.date.today():
        datetime_end = datetime.datetime.utcnow()
    return (date_start, date_end, datetime_start, datetime_end)


def _csv_usage_link(date_start):
    return "?date_month=%s&date_year=%s&format=csv" % (date_start.month,
            date_start.year)


def usage(request):
    (date_start, date_end, datetime_start, datetime_end) = \
            _get_start_and_end_date(request)

    global_summary = GlobalSummary(request)
    if date_start > _current_month():
        messages.error(request, _('No data for the selected period'))
        date_end = date_start
        datetime_end = datetime_start
    else:
        global_summary.service()
        global_summary.usage(datetime_start, datetime_end)

    dateform = forms.DateForm()
    dateform['date'].field.initial = date_start

    global_summary.avail()
    global_summary.human_readable('disk_size')
    global_summary.human_readable('ram_size')

    if request.GET.get('format', 'html') == 'csv':
        template_name = 'syspanel/instances/usage.csv'
        mimetype = "text/csv"
    else:
        template_name = 'syspanel/instances/usage.html'
        mimetype = "text/html"

    return render_to_response(
    template_name, {
        'dateform': dateform,
        'datetime_start': datetime_start,
        'datetime_end': datetime_end,
        'usage_list': global_summary.usage_list,
        'csv_link': _csv_usage_link(date_start),
        'global_summary': global_summary.summary,
        'external_links': getattr(settings, 'EXTERNAL_MONITORING', []),
    }, context_instance=template.RequestContext(request), mimetype=mimetype)


def tenant_usage(request):
    tenant_id = request.user.tenant
    (date_start, date_end, datetime_start, datetime_end) = \
            _get_start_and_end_date(request)
    if date_start > _current_month():
        messages.error(request, _('No data for the selected period'))
        date_end = date_start
        datetime_end = datetime_start

    dateform = forms.DateForm()
    dateform['date'].field.initial = date_start

    usage = {}
    try:
        usage = api.usage_get(request, tenant_id, datetime_start, datetime_end)
    except api_exceptions.ApiException, e:
        LOG.exception('ApiException getting usage info for tenant "%s"'
                  ' on date range "%s to %s"' % (tenant_id,
                                                 datetime_start,
                                                 datetime_end))
        messages.error(request, _('Unable to get usage info: %s') % e.message)

    running_instances = []
    terminated_instances = []
    if hasattr(usage, 'instances'):
        now = datetime.datetime.now()
        for i in usage.instances:
            # this is just a way to phrase uptime in a way that is compatible
            # with the 'timesince' filter.  Use of local time intentional
            i['uptime_at'] = now - datetime.timedelta(seconds=i['uptime'])
            if i['ended_at']:
                terminated_instances.append(i)
            else:
                running_instances.append(i)

    if request.GET.get('format', 'html') == 'csv':
        template_name = 'syspanel/instances/tenant_usage.csv'
        mimetype = "text/csv"
    else:
        template_name = 'syspanel/instances/tenant_usage.html'
        mimetype = "text/html"

    return render_to_response(template_name, {
        'dateform': dateform,
        'datetime_start': datetime_start,
        'datetime_end': datetime_end,
        'usage': usage,
        'csv_link': _csv_usage_link(date_start),
        'instances': running_instances + terminated_instances,
        'tenant_id': tenant_id,
    }, context_instance=template.RequestContext(request), mimetype=mimetype)


def index(request):
    for f in (TerminateInstance, RebootInstance):
        form, handled = f.maybe_handle(request)
        if handled:
            return handled

    instances = []
    try:
        instances = api.admin_server_list(request)
    except Exception as e:
        LOG.exception('Unspecified error in instance index')
        messages.error(request,
                       _('Unable to get instance list: %s') % e.message)

    # We don't have any way of showing errors for these, so don't bother
    # trying to reuse the forms from above
    terminate_form = TerminateInstance()
    reboot_form = RebootInstance()

    return render_to_response(
    'syspanel/instances/index.html', {
        'instances': instances,
        'terminate_form': terminate_form,
        'reboot_form': reboot_form,
    }, context_instance=template.RequestContext(request))


def refresh(request):
    for f in (TerminateInstance, RebootInstance):
        form, handled = f.maybe_handle(request)
        if handled:
            return handled

    instances = []
    try:
        instances = api.admin_server_list(request)
    except Exception as e:
        messages.error(request,
                       _('Unable to get instance list: %s') % e.message)

    # We don't have any way of showing errors for these, so don't bother
    # trying to reuse the forms from above
    terminate_form = TerminateInstance()
    reboot_form = RebootInstance()

    return render_to_response(
    'syspanel/instances/_list.html', {
        'instances': instances,
        'terminate_form': terminate_form,
        'reboot_form': reboot_form,
    }, context_instance=template.RequestContext(request))


def detail(request, instance_id):
    try:
        instance = api.server_get(request, instance_id)
        try:
            console = api.console_create(request, instance_id, 'vnc')
            vnc_url = "%s&title=%s(%s)" % (console.output,
                                           instance.name,
                                           instance_id)
        except api_exceptions.ApiException, e:
            LOG.exception('ApiException while fetching instance vnc \
                           connection')
            messages.error(request,
            _('Unable to get vnc console for instance %(inst)s: %(message)s') %
            {"inst": instance_id, "message": e.message})
            return redirect('horizon:syspanel:instances:index', tenant_id)
    except api_exceptions.ApiException, e:
        LOG.exception('ApiException while fetching instance info')
        messages.error(request,
            _('Unable to get information for instance %(inst)s: %(message)s') %
            {"inst": instance_id, "message": e.message})
        return redirect('horizon:syspanel:instances:index', tenant_id)

    return render_to_response(
    'syspanel/instances/detail.html', {
        'instance': instance,
        'vnc_url': vnc_url,
    }, context_instance=template.RequestContext(request))
