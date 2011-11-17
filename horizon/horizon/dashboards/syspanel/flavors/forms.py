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


class CreateFlavor(forms.SelfHandlingForm):
    flavorid = forms.IntegerField(label=_("Flavor ID"))
    name = forms.CharField(max_length="25", label=_("Name"))
    vcpus = forms.CharField(max_length="5", label=_("VCPUs"))
    memory_mb = forms.CharField(max_length="5", label=_("Memory MB"))
    disk_gb = forms.CharField(max_length="5", label=_("Disk GB"))

    def handle(self, request, data):
        api.flavor_create(request,
                          data['name'],
                          int(data['memory_mb']),
                          int(data['vcpus']),
                          int(data['disk_gb']),
                          int(data['flavorid']))
        msg = _('%s was successfully added to flavors.') % data['name']
        LOG.info(msg)
        messages.success(request, msg)
        return shortcuts.redirect('horizon:syspanel:flavors:index')


class DeleteFlavor(forms.SelfHandlingForm):
    flavorid = forms.CharField(required=True)

    def handle(self, request, data):
        try:
            flavor_id = data['flavorid']
            flavor = api.flavor_get(request, flavor_id)
            LOG.info('Deleting flavor with id "%s"' % flavor_id)
            api.flavor_delete(request, flavor_id, False)
            messages.info(request, _('Successfully deleted flavor: %s') %
                          flavor.name)
        except api_exceptions.ApiException, e:
            messages.error(request, _('Unable to delete flavor: %s') %
                                     e.message)
        return shortcuts.redirect(request.build_absolute_uri())
