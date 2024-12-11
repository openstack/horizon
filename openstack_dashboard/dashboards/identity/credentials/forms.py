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

    def handle(self, request, data):
        try:
            params = {
                'user': data['user_name'],
                'type': data["cred_type"],
                'blob': data["data"],
            }
            if data["project"]:
                params['project'] = data['project']
            new_credential = keystone.credential_create(request, **params)
            messages.success(
                request, _("User credential created successfully."))
            return new_credential
        except Exception:
            exceptions.handle(request, _('Unable to create user credential.'))


class UpdateCredentialForm(forms.SelfHandlingForm):
    id = forms.CharField(label=_("ID"), widget=forms.HiddenInput)
    user_name = forms.ThemableChoiceField(label=_('User'))
    cred_type = forms.ThemableChoiceField(label=_('Type'),
                                          choices=TYPE_CHOICES)
    data = forms.CharField(label=_("Data"))
    project = forms.ThemableChoiceField(label=_('Project'), required=False)
    failure_url = 'horizon:identity:credentials:index'

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        users = keystone.user_list(request)
        user_choices = [(user.id, user.name) for user in users]
        self.fields['user_name'].choices = user_choices

        initial = kwargs.get('initial', {})
        cred_type = initial.get('cred_type')
        self.fields['cred_type'].initial = cred_type

        # Keystone does not change project to None. If this field is left as
        # "Select a project", the project will not be changed. If this field
        # is set to another project, the project will be changed.
        project_choices = [('', _("Select a project"))]
        projects, __ = keystone.tenant_list(request)
        for project in projects:
            if project.enabled:
                project_choices.append((project.id, project.name))
        self.fields['project'].choices = project_choices

        project = initial.get('project_name')
        self.fields['project'].initial = project

    def handle(self, request, data):
        try:
            params = {
                'user': data['user_name'],
                'type': data["cred_type"],
                'blob': data["data"],
            }
            params['project'] = data['project'] if data['project'] else None

            keystone.credential_update(request, data['id'], **params)
            messages.success(
                request, _("User credential updated successfully."))
            return True
        except Exception:
            exceptions.handle(request, _('Unable to update user credential.'))
