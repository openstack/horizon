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

import datetime
import logging
import re

from django import http
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.utils.translation import ugettext as _
from django import shortcuts

from django_openstack import api
from django_openstack import forms
from openstackx.api import exceptions as api_exceptions
from glance.common import exception as glance_exception


LOG = logging.getLogger('django_openstack.dash.views.snapshots')


class CreateSnapshot(forms.SelfHandlingForm):
    tenant_id = forms.CharField(widget=forms.HiddenInput())
    instance_id = forms.CharField(widget=forms.TextInput(
        attrs={'readonly': 'readonly'}))
    name = forms.CharField(max_length="20", label=_("Snapshot Name"))

    def handle(self, request, data):
        try:
            LOG.info('Creating snapshot "%s"' % data['name'])
            snapshot = api.snapshot_create(request,
                    data['instance_id'],
                    data['name'])
            instance = api.server_get(request, data['instance_id'])

            messages.info(request,
                     _('Snapshot "%(name)s" created for instance "%(inst)s"') %
                    {"name": data['name'], "inst": instance.name})
            return shortcuts.redirect('dash_snapshots', data['tenant_id'])
        except api_exceptions.ApiException, e:
            msg = _('Error Creating Snapshot: %s') % e.message
            LOG.exception(msg)
            messages.error(request, msg)
            return shortcuts.redirect(request.build_absolute_uri())


@login_required
def index(request, tenant_id):
    images = []

    try:
        images = api.snapshot_list_detailed(request)
    except glance_exception.ClientConnectionError, e:
        msg = _('Error connecting to glance: %s') % str(e)
        LOG.exception(msg)
        messages.error(request, msg)
    except glance_exception.Error, e:
        msg = _('Error retrieving image list: %s') % str(e)
        LOG.exception(msg)
        messages.error(request, msg)

    return render_to_response(
    'django_openstack/dash/snapshots/index.html', {
        'images': images,
    }, context_instance=template.RequestContext(request))


@login_required
def create(request, tenant_id, instance_id):
    form, handled = CreateSnapshot.maybe_handle(request,
                        initial={'tenant_id': tenant_id,
                                 'instance_id': instance_id})
    if handled:
        return handled

    try:
        instance = api.server_get(request, instance_id)
    except api_exceptions.ApiException, e:
        msg = _("Unable to retreive instance: %s") % e
        LOG.exception(msg)
        messages.error(request, msg)
        return shortcuts.redirect('dash_instances', tenant_id)

    valid_states = ['ACTIVE']
    if instance.status not in valid_states:
        messages.error(request, _("To snapshot, instance state must be\
                                  one of the following: %s") %
                                  ', '.join(valid_states))
        return shortcuts.redirect('dash_instances', tenant_id)

    return shortcuts.render_to_response(
    'django_openstack/dash/snapshots/create.html', {
        'instance': instance,
        'create_form': form,
    }, context_instance=template.RequestContext(request))
