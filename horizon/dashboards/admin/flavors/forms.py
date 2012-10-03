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

from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import messages


LOG = logging.getLogger(__name__)


class CreateFlavor(forms.SelfHandlingForm):
    name = forms.CharField(max_length="25", label=_("Name"))
    vcpus = forms.IntegerField(label=_("VCPUs"))
    memory_mb = forms.IntegerField(label=_("RAM MB"))
    disk_gb = forms.IntegerField(label=_("Root Disk GB"))
    eph_gb = forms.IntegerField(label=_("Ephemeral Disk GB"))

    def _get_new_flavor_id(self):
        # TODO(gabriel): Get rid of this hack after flavor
        # id handling is improved in Nova's API.
        flavors = []
        try:
            flavors = api.nova.flavor_list(self.request)
        except:
            exceptions.handle(self.request,
                              _("Unable to get unique ID for new flavor."))
        if flavors:
            largest_id = max(flavors, key=lambda f: f.id).id
            flavor_id = int(largest_id) + 1
        else:
            flavor_id = 1
        return flavor_id

    def handle(self, request, data):
        try:
            flavor = api.nova.flavor_create(request,
                                            data['name'],
                                            data['memory_mb'],
                                            data['vcpus'],
                                            data['disk_gb'],
                                            self._get_new_flavor_id(),
                                            ephemeral=data['eph_gb'])
            msg = _('Created flavor "%s".') % data['name']
            messages.success(request, msg)
            return flavor
        except:
            exceptions.handle(request, _("Unable to create flavor."))


class EditFlavor(CreateFlavor):
    flavor_id = forms.IntegerField(widget=forms.widgets.HiddenInput)

    def handle(self, request, data):
        try:
            # First mark the existing flavor as deleted.
            api.nova.flavor_delete(request, data['flavor_id'])
            # Then create a new flavor with the same name but a new ID.
            # This is in the same try/except block as the delete call
            # because if the delete fails the API will error out because
            # active flavors can't have the same name.
            flavor = api.nova.flavor_create(request,
                                            data['name'],
                                            data['memory_mb'],
                                            data['vcpus'],
                                            data['disk_gb'],
                                            self._get_new_flavor_id(),
                                            ephemeral=data['eph_gb'])
            msg = _('Updated flavor "%s".') % data['name']
            messages.success(request, msg)
            return flavor
        except:
            exceptions.handle(request, _("Unable to update flavor."))
