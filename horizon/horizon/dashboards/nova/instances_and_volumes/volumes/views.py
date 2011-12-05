# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
Views for managing Nova volumes.
"""

import logging

from django import shortcuts
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon.dashboards.nova.instances_and_volumes.volumes.forms \
                        import (CreateForm, DeleteForm, AttachForm, DetachForm)


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    delete_form, handled = DeleteForm.maybe_handle(request)
    detach_form, handled = DetachForm.maybe_handle(request)

    if handled:
        return handled

    create_form = CreateForm()

    try:
        volumes = api.volume_list(request)
    except novaclient_exceptions.ClientException, e:
        volumes = []
        LOG.exception("ClientException in volume index")
        messages.error(request, _('Error fetching volumes: %s') % e.message)

    return shortcuts.render(request,
                            'nova/instances_and_volumes/volumes/index.html', {
                                'volumes': volumes,
                                'delete_form': delete_form,
                                'create_form': create_form,
                                'detach_form': detach_form})


@login_required
def detail(request, volume_id):
    try:
        volume = api.volume_get(request, volume_id)
        attachment = volume.attachments[0]
        if attachment:
            instance = api.server_get(
                    request, volume.attachments[0]['serverId'])
        else:
            instance = None
    except novaclient_exceptions.ClientException, e:
        LOG.exception("ClientException in volume get")
        messages.error(request, _('Error fetching volume: %s') % e.message)
        return shortcuts.redirect(
                            'horizon:nova:instances_and_volumes:volumes:index')

    return shortcuts.render(request,
                            'nova/instances_and_volumes/volumes/detail.html', {
                                'volume': volume,
                                'attachment': attachment,
                                'instance': instance})


@login_required
def create(request):
    create_form, handled = CreateForm.maybe_handle(request)

    if handled:
        return handled

    return shortcuts.render(request,
                            'nova/instances_and_volumes/volumes/create.html', {
                                'create_form': create_form})


@login_required
def attach(request, volume_id):
    instances = api.server_list(request)
    attach_form, handled = AttachForm.maybe_handle(request,
                                      initial={'volume_id': volume_id,
                                               'instances': instances})

    if handled:
        return handled

    return shortcuts.render(request,
                            'nova/instances_and_volumes/volumes/attach.html', {
                                'attach_form': attach_form,
                                'volume_id': volume_id})
