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

"""
Views for managing Nova instances.
"""
import datetime
import logging

from django import http
from django import shortcuts
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from django_openstack import api
from django_openstack import forms
from django_openstack import utils
import openstack.compute.servers
import openstackx.api.exceptions as api_exceptions
import StringIO

LOG = logging.getLogger('django_openstack.dash')


class TerminateInstance(forms.SelfHandlingForm):
    instance = forms.CharField(required=True)

    def handle(self, request, data):
        instance_id = data['instance']
        instance = api.server_get(request, instance_id)

        try:
            api.server_delete(request, instance)
        except api_exceptions.ApiException, e:
            LOG.exception(_('ApiException while terminating instance "%s"') %
                      instance_id)
            messages.error(request,
                           _('Unable to terminate %(inst)s: %(message)s') %
                           {"inst": instance_id, "message": e.message})
        else:
            msg = _('Instance %s has been terminated.') % instance_id
            LOG.info(msg)
            messages.success(request, msg)

        return shortcuts.redirect(request.build_absolute_uri())


class RebootInstance(forms.SelfHandlingForm):
    instance = forms.CharField(required=True)

    def handle(self, request, data):
        instance_id = data['instance']
        try:
            server = api.server_reboot(request, instance_id)
            messages.success(request, _("Instance rebooting"))
        except api_exceptions.ApiException, e:
            LOG.exception(_('ApiException while rebooting instance "%s"') %
                      instance_id)
            messages.error(request,
                       _('Unable to reboot instance: %s') % e.message)

        else:
            msg = _('Instance %s has been rebooted.') % instance_id
            LOG.info(msg)
            messages.success(request, msg)

        return shortcuts.redirect(request.build_absolute_uri())


class UpdateInstance(forms.SelfHandlingForm):
    tenant_id = forms.CharField(widget=forms.HiddenInput())
    instance = forms.CharField(widget=forms.TextInput(
                               attrs={'readonly': 'readonly'}))
    name = forms.CharField(required=True)
    description = forms.CharField(required=False)

    def handle(self, request, data):
        tenant_id = data['tenant_id']
        description = data.get('description', '')
        try:
            api.server_update(request,
                              data['instance'],
                              data['name'],
                              description)
            messages.success(request, _("Instance '%s' updated") %
                                      data['name'])
        except api_exceptions.ApiException, e:
            messages.error(request,
                       _('Unable to update instance: %s') % e.message)

        return shortcuts.redirect('dash_instances', tenant_id)


@login_required
def index(request, tenant_id):
    for f in (TerminateInstance, RebootInstance):
        form, handled = f.maybe_handle(request)
        if handled:
            return handled
    instances = []
    try:
        instances = api.server_list(request)
    except api_exceptions.ApiException as e:
        LOG.exception(_('Exception in instance index'))
        messages.error(request, _('Unable to get instance list: %s')
                       % e.message)

    # We don't have any way of showing errors for these, so don't bother
    # trying to reuse the forms from above
    terminate_form = TerminateInstance()
    reboot_form = RebootInstance()

    return shortcuts.render_to_response(
    'django_openstack/dash/instances/index.html', {
        'instances': instances,
        'terminate_form': terminate_form,
        'reboot_form': reboot_form,
    }, context_instance=template.RequestContext(request))


@login_required
def refresh(request, tenant_id):
    instances = []
    try:
        instances = api.server_list(request)
    except Exception as e:
        messages.error(request,
                       _('Unable to get instance list: %s') % e.message)

    # We don't have any way of showing errors for these, so don't bother
    # trying to reuse the forms from above
    terminate_form = TerminateInstance()
    reboot_form = RebootInstance()

    return shortcuts.render_to_response(
    'django_openstack/dash/instances/_instance_list.html', {
        'instances': instances,
        'terminate_form': terminate_form,
        'reboot_form': reboot_form,
    }, context_instance=template.RequestContext(request))


@login_required
def usage(request, tenant_id=None):
    today = utils.today()
    date_start = datetime.date(today.year, today.month, 1)
    datetime_start = datetime.datetime.combine(date_start, utils.time())
    datetime_end = utils.utcnow()

    show_terminated = request.GET.get('show_terminated', False)

    usage = {}
    if not tenant_id:
        tenant_id = request.user.tenant_id

    try:
        usage = api.usage_get(request, tenant_id, datetime_start, datetime_end)
    except api_exceptions.ApiException, e:
        LOG.exception(_('ApiException in instance usage'))

        messages.error(request, _('Unable to get usage info: %s') % e.message)

    ram_unit = "MB"
    total_ram = 0
    if hasattr(usage, 'total_active_ram_size'):
        total_ram = usage.total_active_ram_size
        if total_ram > 999:
            ram_unit = "GB"
            total_ram /= float(1024)

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

    instances = running_instances
    if show_terminated:
        instances += terminated_instances

    if request.GET.get('format', 'html') == 'csv':
        template_name = 'django_openstack/dash/instances/usage.csv'
        mimetype = "text/csv"
    else:
        template_name = 'django_openstack/dash/instances/usage.html'
        mimetype = "text/html"

    return shortcuts.render_to_response(template_name, {
        'usage': usage,
        'ram_unit': ram_unit,
        'total_ram': total_ram,
        # there are no date selection caps yet so keeping csv_link simple
        'csv_link': '?format=csv',
        'show_terminated': show_terminated,
        'datetime_start': datetime_start,
        'datetime_end': datetime_end,
        'instances': instances
    }, context_instance=template.RequestContext(request), mimetype=mimetype)


@login_required
def console(request, tenant_id, instance_id):
    try:
        # TODO(jakedahn): clean this up once the api supports tailing.
        length = request.GET.get('length', '')
        console = api.console_create(request, instance_id, 'text')
        response = http.HttpResponse(mimetype='text/plain')
        if length:
            response.write('\n'.join(console.output.split('\n')
                           [-int(length):]))
        else:
            response.write(console.output)
        response.flush()
        return response
    except api_exceptions.ApiException, e:
        LOG.exception(_('ApiException while fetching instance console'))
        messages.error(request,
                   _('Unable to get log for instance %(inst)s: %(msg)s') %
                    {"inst": instance_id, "msg": e.message})
        return shortcuts.redirect('dash_instances', tenant_id)


@login_required
def vnc(request, tenant_id, instance_id):
    try:
        console = api.console_create(request, instance_id, 'vnc')
        instance = api.server_get(request, instance_id)
        return shortcuts.redirect(console.output +
                ("&title=%s(%s)" % (instance.name, instance_id)))
    except api_exceptions.ApiException, e:
        LOG.exception(_('ApiException while fetching instance vnc connection'))
        messages.error(request,
            _('Unable to get vnc console for instance %(inst)s: %(message)s') %
            {"inst": instance_id, "message": e.message})
        return shortcuts.redirect('dash_instances', tenant_id)


@login_required
def update(request, tenant_id, instance_id):
    try:
        instance = api.server_get(request, instance_id)
    except api_exceptions.ApiException, e:
        LOG.exception(_('ApiException while fetching instance info'))
        messages.error(request,
            _('Unable to get information for instance %(inst)s: %(message)s') %
            {"inst": instance_id, "message": e.message})
        return shortcuts.redirect('dash_instances', tenant_id)

    form, handled = UpdateInstance.maybe_handle(request, initial={
                                'instance': instance_id,
                                'tenant_id': tenant_id,
                                'name': instance.name,
                                'description': instance.attrs['description']})

    if handled:
        return handled

    return shortcuts.render_to_response(
    'django_openstack/dash/instances/update.html', {
        'instance': instance,
        'form': form,
    }, context_instance=template.RequestContext(request))


@login_required
def detail(request, tenant_id, instance_id):
    try:
        instance = api.server_get(request, instance_id)
        volumes = api.volume_instance_list(request, instance_id)
        try:
            console = api.console_create(request, instance_id, 'vnc')
            vnc_url = "%s&title=%s(%s)" % (console.output,
                                           instance.name,
                                           instance_id)
        except api_exceptions.ApiException, e:
            LOG.exception(_('ApiException while fetching instance vnc \
                           connection'))
            messages.error(request,
                _('Unable to get vnc console for instance %(inst)s: %(msg)s') %
                {"inst": instance_id, "msg": e.message})
            return shortcuts.redirect('dash_instances', tenant_id)
    except api_exceptions.ApiException, e:
        LOG.exception(_('ApiException while fetching instance info'))
        messages.error(request,
            _('Unable to get information for instance %(inst)s: %(msg)s') %
            {"inst": instance_id, "msg": e.message})
        return shortcuts.redirect('dash_instances', tenant_id)

    return shortcuts.render_to_response(
    'django_openstack/dash/instances/detail.html', {
        'instance': instance,
        'vnc_url': vnc_url,
        'volumes': volumes
    }, context_instance=template.RequestContext(request))
