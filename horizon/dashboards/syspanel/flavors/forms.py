# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import forms


LOG = logging.getLogger(__name__)


class CreateFlavor(forms.SelfHandlingForm):
    # flavorid is required in novaclient
    flavor_id = forms.IntegerField(label=_("Flavor ID"))
    name = forms.CharField(max_length="25", label=_("Name"))
    vcpus = forms.IntegerField(label=_("VCPUs"))
    memory_mb = forms.IntegerField(label=_("Memory MB"))
    disk_gb = forms.IntegerField(label=_("Root Disk GB"))
    eph_gb = forms.IntegerField(label=_("Ephemeral Disk GB"))

    def handle(self, request, data):
        api.flavor_create(request,
                          data['name'],
                          data['memory_mb'],
                          data['vcpus'],
                          data['disk_gb'],
                          data['flavor_id'],
                          ephemeral=data['eph_gb'])
        msg = _('%s was successfully added to flavors.') % data['name']
        LOG.info(msg)
        messages.success(request, msg)
        return shortcuts.redirect('horizon:syspanel:flavors:index')
