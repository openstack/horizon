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
from openstack_dashboard.dashboards.admin.aggregates import constants

INDEX_URL = constants.AGGREGATES_INDEX_URL


class UpdateAggregateForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"),
                           max_length=255)
    availability_zone = forms.CharField(label=_("Availability Zone"),
                                        max_length=255)

    def __init__(self, request, *args, **kwargs):
        super(UpdateAggregateForm, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        id = self.initial['id']
        name = data['name']
        availability_zone = data['availability_zone']
        aggregate = {'name': name}
        if availability_zone:
            aggregate['availability_zone'] = availability_zone
        try:
            api.nova.aggregate_update(request, id, aggregate)
            message = (_('Successfully updated aggregate: "%s."')
                       % data['name'])
            messages.success(request, message)
        except Exception:
            exceptions.handle(request,
                              _('Unable to update the aggregate.'))
        return True


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

            for key in old_metadata:
                if key not in metadata:
                    metadata[key] = None

            api.nova.aggregate_set_metadata(request, id, metadata)
            message = _('Metadata successfully updated.')
            messages.success(request, message)
        except Exception:
            msg = _('Unable to update the aggregate metadata.')
            exceptions.handle(request, msg)

            return False
        return True
