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

import logging

from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext as _
from openstackx.api import exceptions as api_exceptions

from horizon import api
from horizon import forms


LOG = logging.getLogger(__name__)


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
            return shortcuts.redirect('horizon:nova:images_and_snapshots:snapshots:index')
        except api_exceptions.ApiException, e:
            msg = _('Error Creating Snapshot: %s') % e.message
            LOG.exception(msg)
            messages.error(request, msg)
            return shortcuts.redirect(request.build_absolute_uri())
