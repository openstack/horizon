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
from openstack_dashboard.dashboards.project.volumes.tables \
    import VolumesTableBase as volumes_table

# This set of states was pulled from cinder's snapshot_actions.py
SETTABLE_STATUSES = (
    'available', 'creating', 'deleting', 'error', 'error_deleting'
)
STATUS_CHOICES = tuple(
    status for status in volumes_table.STATUS_DISPLAY_CHOICES
    if status[0] in SETTABLE_STATUSES
)


def populate_status_choices(current_status, status_choices):
    choices = []
    for status in status_choices:
        if status[0] == current_status:
            choices.append((status[0], _("%s (current)") % status[1]))
        else:
            choices.append(status)

    choices.insert(0, ("", _("Select a new status")))
    return choices


class UpdateStatus(forms.SelfHandlingForm):
    status = forms.ThemableChoiceField(label=_("Status"))

    def __init__(self, request, *args, **kwargs):
        # Initial values have to be operated before super() otherwise the
        # initial values will get overwritten back to the raw value
        current_status = kwargs['initial']['status']
        kwargs['initial'].pop('status')

        super(UpdateStatus, self).__init__(request, *args, **kwargs)

        self.fields['status'].choices = populate_status_choices(
            current_status, STATUS_CHOICES)

    def handle(self, request, data):
        try:
            cinder.volume_snapshot_reset_state(request,
                                               self.initial['snapshot_id'],
                                               data['status'])

            choices = dict(STATUS_CHOICES)
            choice = choices[data['status']]
            messages.success(request, _('Successfully updated volume snapshot'
                                        ' status: "%s".') % choice)
            return True
        except Exception:
            redirect = reverse("horizon:admin:snapshots:index")
            exceptions.handle(request,
                              _('Unable to update volume snapshot status.'),
                              redirect=redirect)
