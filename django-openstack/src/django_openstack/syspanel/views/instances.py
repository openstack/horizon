# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django import template
from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _

import datetime
import logging

from django.contrib import messages

from django_openstack import api
from django_openstack import forms
from django_openstack.dash.views import instances as dash_instances
from openstackx.api import exceptions as api_exceptions


TerminateInstance = dash_instances.TerminateInstance
RebootInstance = dash_instances.RebootInstance


def _next_month(date_start):
    y = date_start.year + (date_start.month + 1)/13
    m = ((date_start.month + 1)%13)
    if m == 0:
        m = 1
    return datetime.date(y, m, 1)


def _current_month():
    today = datetime.date.today()
    return datetime.date(today.year, today.month,1)


def _get_start_and_end_date(request):
    try:
        date_start = datetime.date(int(request.GET['date_year']), int(request.GET['date_month']), 1)
    except:
        today = datetime.date.today()
        date_start = datetime.date(today.year, today.month,1)

    date_end = _next_month(date_start)
    datetime_start = datetime.datetime.combine(date_start, datetime.time())
    datetime_end = datetime.datetime.combine(date_end, datetime.time())
    return (date_start, date_end, datetime_start, datetime_end)


@login_required
def usage(request):
    (date_start, date_end, datetime_start, datetime_end) = _get_start_and_end_date(request)
    service_list = []
    usage_list = []
    max_vcpus = max_gigabytes = 0

    if date_start > _current_month():
        messages.error(request, 'No data for the selected period')
        date_end = date_start
        datetime_end = datetime_start
    else:
        try:
            service_list = api.admin_api(request).services.list()
        except api_exceptions.ApiException, e:
            messages.error(request, 'Unable to get service info: %s' % e.message)

        for service in service_list:
            if service.type == 'nova-compute':
                max_vcpus += service.stats['max_vcpus']
                max_gigabytes += service.stats['max_gigabytes']

        try:
            usage_list = api.extras_api(request).usage.list(datetime_start, datetime_end)
        except api_exceptions.ApiException, e:
            messages.error(request, 'Unable to get usage info: %s' % e.message)

    dateform = forms.DateForm()
    dateform['date'].field.initial = date_start



    global_summary = {'max_vcpus': max_vcpus, 'max_gigabytes': max_gigabytes,
                      'total_active_disk_size': 0, 'total_active_vcpus': 0,
                      'total_active_ram_size': 0}

    for usage in usage_list:
        # FIXME: api needs a simpler dict interface (with iteration) - anthony
        usage = usage._info
        for k in usage:
            v = usage[k]
            if type(v) in [float, int]:
                if not k in global_summary:
                    global_summary[k] = 0
                global_summary[k] += v

    max_disk_tb = used_disk_tb = available_disk_tb = 0

    max_disk_tb = global_summary['max_gigabytes'] / float(1000)
    used_disk_tb = global_summary['total_active_disk_size'] / float(1000)
    available_disk_tb = (global_summary['max_gigabytes'] / float(1000) - \
                        global_summary['total_active_disk_size'] / float(1000))
    total_ram = settings.TOTAL_CLOUD_RAM_GB
    used_ram = global_summary['total_active_ram_size'] / float(1024)
    avail_ram = total_ram - used_ram

    ram_unit = "GB"
    if total_ram > 999:
        ram_unit = "TB"
        total_ram /= float(1024)
        used_ram /= float(1024)
        avail_ram /= float(1024)

    return render_to_response(
    'syspanel_usage.html',{
        'dateform': dateform,
        'usage_list': usage_list,
        'global_summary': global_summary,
        'available_cores': global_summary['max_vcpus'] - global_summary['total_active_vcpus'],
        'available_disk': global_summary['max_gigabytes'] - global_summary['total_active_disk_size'],
        'max_disk_tb': max_disk_tb,
        'used_disk_tb': used_disk_tb,
        'available_disk_tb': available_disk_tb,
        'total_ram': total_ram,
        'used_ram': used_ram,
        'avail_ram': avail_ram,
        'ram_unit': ram_unit,
        'external_links': settings.EXTERNAL_MONITORING,
    }, context_instance = template.RequestContext(request))


@login_required
def tenant_usage(request, tenant_id):
    (date_start, date_end, datetime_start, datetime_end) = _get_start_and_end_date(request)
    if date_start > _current_month():
        messages.error(request, 'No data for the selected period')
        date_end = date_start
        datetime_end = datetime_start

    dateform = forms.DateForm()
    dateform['date'].field.initial = date_start

    usage = {}
    try:
        usage = extras_api(request).usage.get(tenant_id, datetime_start, datetime_end)
    except api_exceptions.ApiException, e:
        messages.error(request, 'Unable to get usage info: %s' % e.message)

    return render_to_response(
    'syspanel_tenant_usage.html',{
        'dateform': dateform,
        'usage': usage,
    }, context_instance = template.RequestContext(request))


@login_required
def index(request):
    for f in (TerminateInstance, RebootInstance):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled

    instances = []
    try:
        image_dict = api.get_image_cache(request)
        instances = api.extras_api(request).servers.list()
        for instance in instances:
            # FIXME - ported this over, but it is hacky
            instance._info['attrs']['image_name'] =\
               image_dict.get(int(instance.attrs['image_id']),{}).get('name')
    except Exception as e:
        messages.error(request, 'Unable to get instance list: %s' % e.message)

    # We don't have any way of showing errors for these, so don't bother
    # trying to reuse the forms from above
    terminate_form = TerminateInstance()
    reboot_form = RebootInstance()

    return render_to_response('syspanel_instances.html', {
        'instances': instances,
        'terminate_form': terminate_form,
        'reboot_form': reboot_form,
    }, context_instance=template.RequestContext(request))
