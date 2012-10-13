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
import uuid

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class CreateFlavor(forms.SelfHandlingForm):
    name = forms.CharField(max_length="25", label=_("Name"))
    vcpus = forms.IntegerField(label=_("VCPUs"))
    memory_mb = forms.IntegerField(label=_("RAM MB"))
    disk_gb = forms.IntegerField(label=_("Root Disk GB"))
    eph_gb = forms.IntegerField(label=_("Ephemeral Disk GB"))

    def handle(self, request, data):
        try:
            flavor = api.nova.flavor_create(request,
                                            data['name'],
                                            data['memory_mb'],
                                            data['vcpus'],
                                            data['disk_gb'],
                                            uuid.uuid4(),
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
            flavor_id = data['flavor_id']
            # grab any existing extra specs, because flavor edit currently
            # implemented as a delete followed by a create
            extras_dict = api.nova.flavor_get_extras(self.request, flavor_id)
            # First mark the existing flavor as deleted.
            api.nova.flavor_delete(request, data['flavor_id'])
            # Then create a new flavor with the same name but a new ID.
            # This is in the same try/except block as the delete call
            # because if the delete fails the API will error out because
            # active flavors can't have the same name.
            new_flavor_id = uuid.uuid4()
            flavor = api.nova.flavor_create(request,
                                            data['name'],
                                            data['memory_mb'],
                                            data['vcpus'],
                                            data['disk_gb'],
                                            new_flavor_id,
                                            ephemeral=data['eph_gb'])
            if (len(extras_dict) > 0):
                api.nova.flavor_extra_set(request, new_flavor_id, extras_dict)
            msg = _('Updated flavor "%s".') % data['name']
            messages.success(request, msg)
            return flavor
        except:
            exceptions.handle(request, _("Unable to update flavor."))
