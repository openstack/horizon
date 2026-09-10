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

import base64
import secrets

from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import keystone

# Available credential type choices
TYPE_CHOICES = (
    ('totp', _('TOTP')),
    ('ec2', _('EC2')),
    ('cert', _('cert')),
)


class CreateCredentialForm(forms.SelfHandlingForm):
    user_name = forms.ThemableChoiceField(label=_('User'))
    cred_type = forms.ThemableChoiceField(label=_('Type'),
                                          choices=TYPE_CHOICES)
    data = forms.CharField(label=_('Data'))
    project = forms.ThemableChoiceField(label=_('Project'), required=False)
    failure_url = 'horizon:identity:credentials:index'

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        users = keystone.user_list(request)
        user_choices = [(user.id, user.name) for user in users]
        self.fields['user_name'].choices = user_choices

        project_choices = [('', _("Select a project"))]
        projects, __ = keystone.tenant_list(request)
        for project in projects:
            if project.enabled:
                project_choices.append((project.id, project.name))
        self.fields['project'].choices = project_choices

        self.fields['data'].initial = 'auto'

    def handle(self, request, data):
        try:
            params = {
                'user': data['user_name'],
                'type': data['cred_type'],
                'blob': data['data'],
            }
            if data["project"]:
                params['project'] = data['project']

            if data['data'] == 'auto':
                if params['type'] == 'totp':
                    # Generate a TOTP: a base32 encoded string for the secret
                    # that must be at least 16 bytes
                    # We use 20 bytes of data from secrets.token_bytes.
                    params['blob'] = base64.b32encode(
                        secrets.token_bytes(20)).decode('utf-8')
                else:
                    params['blob'] = None
                    messages.warning(
                        request, _("Autogeneration is available only for TOTP"))

            new_credential = keystone.credential_create(request, **params)
            messages.success(
                request, _("User credential created successfully."))
            return new_credential
        except Exception:
            exceptions.handle(request, _('Unable to create user credential.'))


class UpdateCredentialForm(forms.SelfHandlingForm):
    # Keystone made type, user_id and project_id immutable, so they are
    # shown for context but cannot be edited. Django's disabled fields
    # ignore submitted data and keep their initial value, which is what we
    # want: a tampered POST cannot change them either.
    id = forms.CharField(label=_("ID"), widget=forms.HiddenInput)
    user_name = forms.ThemableChoiceField(label=_('User'), disabled=True)
    cred_type = forms.ThemableChoiceField(label=_('Type'),
                                          choices=TYPE_CHOICES,
                                          disabled=True)
    data = forms.CharField(label=_("Data"))
    project = forms.ThemableChoiceField(label=_('Project'), required=False,
                                        disabled=True)
    failure_url = 'horizon:identity:credentials:index'

    @staticmethod
    def _with_current(choices, current):
        """Guarantee the stored value is selectable.

        A disabled field still validates its initial value against the
        choices, and the owning user or the project can be absent from the
        listing, for instance a disabled project or one this operator cannot
        list. Falling back to the raw id keeps the form usable instead of
        rejecting it with "Select a valid choice".
        """
        if current and current not in [value for value, __ in choices]:
            return list(choices) + [(current, current)]
        return choices

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        initial = kwargs.get('initial', {})

        users = keystone.user_list(request)
        user_choices = [(user.id, user.name) for user in users]
        self.fields['user_name'].choices = self._with_current(
            user_choices, initial.get('user_name'))

        cred_type = initial.get('cred_type')
        self.fields['cred_type'].choices = self._with_current(
            TYPE_CHOICES, cred_type)
        self.fields['cred_type'].initial = cred_type

        # The project is immutable, so this list exists only to render the
        # current one by name.
        project_choices = [('', _("Select a project"))]
        projects, __ = keystone.tenant_list(request)
        for project in projects:
            if project.enabled:
                project_choices.append((project.id, project.name))

        project = initial.get('project_name')
        self.fields['project'].choices = self._with_current(
            project_choices, project)
        self.fields['project'].initial = project

    def handle(self, request, data):
        try:
            keystone.credential_update(request, data['id'], data['data'])
            messages.success(
                request, _("User credential updated successfully."))
            return True
        except Exception:
            exceptions.handle(request, _('Unable to update user credential.'))
