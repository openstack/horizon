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


class CreateGroupForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Group Name"))
    description = forms.CharField(max_length=255,
                                  widget=forms.Textarea(attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    snapshot_source = forms.ChoiceField(
        label=_("Use snapshot as a source"),
        widget=forms.ThemableSelectWidget(
            attrs={'class': 'snapshot-selector'},
            data_attrs=('name'),
            transform=lambda x: "%s" % (x.name)),
        required=False)

    def prepare_snapshot_source_field(self, request, vg_snapshot_id):
        try:
            vg_snapshot = cinder.group_snapshot_get(request, vg_snapshot_id)
            self.fields['snapshot_source'].choices = ((vg_snapshot_id,
                                                       vg_snapshot),)
        except Exception:
            exceptions.handle(request,
                              _('Unable to load the specified snapshot.'))

    def __init__(self, request, *args, **kwargs):
        super(CreateGroupForm, self).__init__(request, *args, **kwargs)

        vg_snapshot_id = kwargs.get('initial', {}).get('vg_snapshot_id', [])
        self.fields['vg_snapshot_id'] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=vg_snapshot_id)
        self.prepare_snapshot_source_field(request, vg_snapshot_id)

    def handle(self, request, data):
        try:

            message = _('Creating group "%s".') % data['name']
            group = cinder.group_create_from_source(
                request,
                data['name'],
                group_snapshot_id=data['vg_snapshot_id'],
                description=data['description'])

            messages.info(request, message)
            return group
        except Exception:
            redirect = reverse("horizon:project:vg_snapshots:index")
            msg = (_('Unable to create group "%s" from snapshot.')
                   % data['name'])
            exceptions.handle(request,
                              msg,
                              redirect=redirect)
