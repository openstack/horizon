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
import openstackx.api.exceptions as api_exceptions

from horizon import api
from horizon import forms


LOG = logging.getLogger(__name__)


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

    def handle(self, request, data):
        tenant_id = data['tenant_id']
        try:
            api.server_update(request,
                              data['instance'],
                              data['name'])
            messages.success(request, _("Instance '%s' updated") %
                                      data['name'])
        except api_exceptions.ApiException, e:
            messages.error(request,
                       _('Unable to update instance: %s') % e.message)

        return shortcuts.redirect('horizon:nova:instances:index')
