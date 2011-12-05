# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
# Copyright 2011 OpenStack LLC
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
Views for Instances and Volumes.
"""
import datetime
import logging

from django import http
from django import shortcuts
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions
import openstackx.api.exceptions as api_exceptions

from horizon import api
from horizon import forms
from horizon import test
from horizon.dashboards.nova.instances_and_volumes.instances.forms import \
                            (TerminateInstance, RebootInstance, UpdateInstance)
from horizon.dashboards.nova.instances_and_volumes.volumes.forms import \
                               (CreateForm, DeleteForm, AttachForm, DetachForm)


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    tenant_id = request.user.tenant_id
    for f in (TerminateInstance, RebootInstance, DeleteForm, DetachForm):
        form, handled = f.maybe_handle(request)
        if handled:
            return handled
    try:
        instances = api.server_list(request)
    except api_exceptions.ApiException as e:
        instances = []
        LOG.exception(_('Exception in instance index'))
        messages.error(request, _('Unable to fetch instances: %s') % e.message)
    try:
        volumes = api.volume_list(request)
    except novaclient_exceptions.ClientException, e:
        volumes = []
        LOG.exception("ClientException in volume index")
        messages.error(request, _('Unable to fetch volumes: %s') % e.message)

    terminate_form = TerminateInstance()
    reboot_form = RebootInstance()
    delete_form = DeleteForm()
    detach_form = DetachForm()
    create_form = CreateForm()

    return shortcuts.render(request, 'nova/instances_and_volumes/index.html', {
                                     'instances': instances,
                                     'terminate_form': terminate_form,
                                     'reboot_form': reboot_form,
                                     'volumes': volumes,
                                     'delete_form': delete_form,
                                     'create_form': create_form,
                                     'detach_form': detach_form})
