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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import cinder


class CreateVolumeType(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Name"))

    def handle(self, request, data):
        try:
            # Remove any new lines in the public key
            volume_type = cinder.volume_type_create(request,
                                                    data['name'])
            messages.success(request, _('Successfully created volume type: %s')
                                      % data['name'])
            return volume_type
        except Exception:
            exceptions.handle(request,
                              _('Unable to create volume type.'))
            return False
