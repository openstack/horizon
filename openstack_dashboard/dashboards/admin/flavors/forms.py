# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import json

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


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
            api.nova.flavor_extra_set(request, id, metadata)

            remove_keys = [key for key in old_metadata if key not in metadata]

            api.nova.flavor_extra_delete(request, id, remove_keys)

            message = _('Metadata successfully updated.')
            messages.success(request, message)
        except Exception:
            exceptions.handle(request,
                              _('Unable to update the flavor metadata.'))
            return False
        return True
