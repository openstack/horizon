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
from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import cinder
from openstack_dashboard.dashboards.admin.snapshots.forms \
    import populate_status_choices
from openstack_dashboard.dashboards.project.backups \
    import forms as project_forms
from openstack_dashboard.dashboards.project.backups.tables \
    import BackupsTable as backups_table


SETTABLE_STATUSES = ('available', 'error')
STATUS_CHOICES = tuple(
    status for status in backups_table.STATUS_DISPLAY_CHOICES
    if status[0] in SETTABLE_STATUSES
)


class UpdateStatus(forms.SelfHandlingForm):
    status = forms.ThemableChoiceField(label=_("Status"))

    def __init__(self, request, *args, **kwargs):
        current_status = kwargs['initial']['status']
        kwargs['initial'].pop('status')

        super().__init__(request, *args, **kwargs)

        self.fields['status'].choices = populate_status_choices(
            current_status, STATUS_CHOICES)

    def handle(self, request, data):
        for choice in self.fields['status'].choices:
            if choice[0] == data['status']:
                new_status = choice[1]
                break
        else:
            new_status = data['status']

        try:
            cinder.volume_backup_reset_state(request,
                                             self.initial['backup_id'],
                                             data['status'])
            messages.success(request,
                             _('Successfully updated volume backup'
                               ' status to "%s".') % new_status)
            return True
        except Exception:
            redirect = reverse("horizon:admin:backups:index")
            exceptions.handle(request,
                              _('Unable to update volume backup status to '
                                '"%s".') % new_status, redirect=redirect)


class AdminRestoreBackupForm(project_forms.RestoreBackupForm):
    redirect_url = 'horizon:admin:backups:index'
