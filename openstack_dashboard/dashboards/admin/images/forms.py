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


import json

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.images.images \
    import forms as images_forms


class AdminCreateImageForm(images_forms.CreateImageForm):
    pass


class AdminUpdateImageForm(images_forms.UpdateImageForm):
    pass


class UpdateMetadataForm(forms.SelfHandlingForm):

    def handle(self, request, data):
        id = self.initial['id']
        old_metadata = self.initial['metadata']

        try:
            new_metadata = json.loads(self.data['metadata'])

            metadata = dict(
                (item['key'], str(item['value']))
                for item in new_metadata
            )

            remove_props = [key for key in old_metadata if key not in metadata]

            api.glance.image_update_properties(request,
                                               id,
                                               remove_props,
                                               **metadata)
            message = _('Metadata successfully updated.')
            messages.success(request, message)
        except Exception:
            exceptions.handle(request,
                              _('Unable to update the image metadata.'))
            return False
        return True
