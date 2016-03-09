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


from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import cinder

# This set of states was pulled from cinder's snapshot_actions.py
STATUS_CHOICES = (
    ('available', _('Available')),
    ('creating', _('Creating')),
    ('deleting', _('Deleting')),
    ('error', _('Error')),
    ('error_deleting', _('Error Deleting')),
)


def populate_status_choices(initial, status_choices):
    current_status = initial.get('status')
    status_choices = [status for status in status_choices
                      if status[0] != current_status]
    status_choices.insert(0, ("", _("Select a new status")))

    return status_choices


class UpdateStatus(forms.SelfHandlingForm):
    status = forms.ThemableChoiceField(label=_("Status"))

    def __init__(self, request, *args, **kwargs):
        super(UpdateStatus, self).__init__(request, *args, **kwargs)

        initial = kwargs.get('initial', {})
        self.fields['status'].choices = populate_status_choices(
            initial, STATUS_CHOICES)

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
            redirect = reverse("horizon:admin:volumes:index")
            exceptions.handle(request,
                              _('Unable to update volume snapshot status.'),
                              redirect=redirect)
