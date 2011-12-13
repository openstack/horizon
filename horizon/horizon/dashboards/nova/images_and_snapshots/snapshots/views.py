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
Views for managing Nova instance snapshots.
"""

import logging
import re

from django import http
from django import shortcuts
from django import template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from glance.common import exception as glance_exception
from openstackx.api import exceptions as api_exceptions

from horizon import api
from horizon import forms
from horizon.dashboards.nova.images_and_snapshots.snapshots.forms import \
                                                                CreateSnapshot


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    images = []

    try:
        images = api.snapshot_list_detailed(request)
    except glance_exception.ClientConnectionError, e:
        msg = _('Error connecting to glance: %s') % str(e)
        LOG.exception(msg)
        messages.error(request, msg)
    except glance_exception.GlanceException, e:
        msg = _('Error retrieving image list: %s') % str(e)
        LOG.exception(msg)
        messages.error(request, msg)

    return shortcuts.render(request,
                            'nova/images_and_snapshots/snapshots/index.html',
                            {'images': images})


@login_required
def create(request, instance_id):
    tenant_id = request.user.tenant_id
    form, handled = CreateSnapshot.maybe_handle(request,
                        initial={'tenant_id': tenant_id,
                                 'instance_id': instance_id})
    if handled:
        return handled

    try:
        instance = api.server_get(request, instance_id)
    except api_exceptions.ApiException, e:
        msg = _("Unable to retrieve instance: %s") % e
        LOG.exception(msg)
        messages.error(request, msg)
        return shortcuts.redirect(
                        'horizon:nova:instances_and_volumes:instances:index')

    valid_states = ['ACTIVE']
    if instance.status not in valid_states:
        messages.error(request, _("To snapshot, instance state must be\
                                  one of the following: %s") %
                                  ', '.join(valid_states))
        return shortcuts.redirect(
                        'horizon:nova:instances_and_volumes:instances:index')

    return shortcuts.render(request,
                            'nova/images_and_snapshots/snapshots/create.html',
                            {'instance': instance,
                             'create_form': form})
