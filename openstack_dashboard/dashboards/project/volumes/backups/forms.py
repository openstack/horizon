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


"""
Views for managing backups.
"""

import operator

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.containers \
    import forms as containers_forms


class CreateBackupForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Backup Name"))
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    container_name = forms.CharField(
        max_length=255,
        label=_("Container Name"),
        validators=[containers_forms.no_slash_validator],
        required=False)
    volume_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        # Create a container for the user if no input is given
        if not data['container_name']:
            data['container_name'] = 'volumebackups'

        try:
            backup = api.cinder.volume_backup_create(request,
                                                     data['volume_id'],
                                                     data['container_name'],
                                                     data['name'],
                                                     data['description'])

            message = _('Creating volume backup "%s"') % data['name']
            messages.success(request, message)
            return backup

        except Exception:
            redirect = reverse('horizon:project:volumes:index')
            exceptions.handle(request,
                              _('Unable to create volume backup.'),
                              redirect=redirect)


class RestoreBackupForm(forms.SelfHandlingForm):
    volume_id = forms.ChoiceField(label=_('Select Volume'), required=False)
    backup_id = forms.CharField(widget=forms.HiddenInput())
    backup_name = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        super(RestoreBackupForm, self).__init__(request, *args, **kwargs)

        try:
            volumes = api.cinder.volume_list(request)
        except Exception:
            msg = _('Unable to lookup volume or backup information.')
            redirect = reverse('horizon:project:volumes:index')
            exceptions.handle(request, msg, redirect=redirect)
            raise exceptions.Http302(redirect)

        volumes.sort(key=operator.attrgetter('name', 'created_at'))
        choices = [('', _('Create a New Volume'))]
        choices.extend((volume.id, volume.name) for volume in volumes)
        self.fields['volume_id'].choices = choices

    def handle(self, request, data):
        backup_id = data['backup_id']
        backup_name = data['backup_name'] or None
        volume_id = data['volume_id'] or None

        try:
            restore = api.cinder.volume_backup_restore(request,
                                                       backup_id,
                                                       volume_id)

            # Needed for cases when a new volume is created.
            volume_id = restore.volume_id

            message = _('Successfully restored backup %(backup_name)s '
                        'to volume with id: %(volume_id)s')
            messages.success(request, message % {'backup_name': backup_name,
                                                 'volume_id': volume_id})
            return restore
        except Exception:
            msg = _('Unable to restore backup.')
            redirect = reverse('horizon:project:volumes:index')
            exceptions.handle(request, msg, redirect=redirect)
