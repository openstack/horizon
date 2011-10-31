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


class ToggleService(forms.SelfHandlingForm):
    service = forms.CharField(required=False)
    name = forms.CharField(required=False)

    def handle(self, request, data):
        try:
            service = api.service_get(request, data['service'])
            api.service_update(request,
                               data['service'],
                               not service.disabled)
            if service.disabled:
                messages.info(request, _("Service '%s' has been enabled")
                                        % data['name'])
            else:
                messages.info(request, _("Service '%s' has been disabled")
                                        % data['name'])
        except api_exceptions.ApiException, e:
            LOG.exception('ApiException while toggling service %s' %
                      data['service'])
            messages.error(request,
                           _("Unable to update service '%(name)s': %(msg)s")
                           % {"name": data['name'], "msg": e.message})

        return shortcuts.redirect(request.build_absolute_uri())
