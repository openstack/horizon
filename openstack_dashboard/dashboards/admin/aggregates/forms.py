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

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.aggregates import constants

INDEX_URL = constants.AGGREGATES_INDEX_URL


class UpdateAggregateForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"),
                           max_length=255)
    availability_zone = forms.CharField(label=_("Availability Zone"),
                                        required=False,
                                        max_length=255)

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
