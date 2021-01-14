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


from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import cinder


class UpdateForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Snapshot Name"),
                           required=False)
    description = forms.CharField(max_length=255,
                                  widget=forms.Textarea(attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)

    def handle(self, request, data):
        snapshot_id = self.initial['snapshot_id']
        try:
            snapshot = cinder.volume_snapshot_update(request,
                                                     snapshot_id,
                                                     data['name'],
                                                     data['description'])

            name_or_id = (snapshot["snapshot"]["name"] or
                          snapshot["snapshot"]["id"])
            message = _('Updating volume snapshot "%s"') % name_or_id
            messages.info(request, message)
            return True
        except Exception:
            redirect = reverse("horizon:project:snapshots:index")
            exceptions.handle(request,
                              _('Unable to update volume snapshot.'),
                              redirect=redirect)
