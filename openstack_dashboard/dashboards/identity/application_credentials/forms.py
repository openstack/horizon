# Copyright 2018 SUSE Linux GmbH
#
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

import datetime
import logging

from django.conf import settings
from django.forms import widgets
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables
import yaml

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class CreateApplicationCredentialForm(forms.SelfHandlingForm):
    # Hide the domain_id and domain_name by default
    name = forms.CharField(max_length=255, label=_("Name"))
    description = forms.CharField(
        widget=forms.widgets.Textarea(attrs={'rows': 4}),
        label=_("Description"),
        required=False)
    secret = forms.CharField(max_length=255, label=_("Secret"), required=False)
    expiration_date = forms.DateField(
        widget=forms.widgets.DateInput(attrs={'type': 'date'}),
        label=_("Expiration Date"),
        required=False)
    expiration_time = forms.TimeField(
        widget=forms.widgets.TimeInput(attrs={'type': 'time'}),
        label=_("Expiration Time"),
        required=False)
    roles = forms.MultipleChoiceField(
        widget=forms.widgets.SelectMultiple(),
        label=_("Roles"),
        required=False)
    access_rules = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        label=_("Access Rules"),
        required=False)
    unrestricted = forms.BooleanField(label=_("Unrestricted (dangerous)"),
                                      required=False)
    kubernetes_namespace = forms.CharField(max_length=255,
                                           label=_("Kubernetes Namespace"),
                                           initial="default",
                                           required=False)

    def __init__(self, request, *args, **kwargs):
        self.next_view = kwargs.pop('next_view', None)
        super().__init__(request, *args, **kwargs)
        role_list = self.request.user.roles
        role_names = [role['name'] for role in role_list]
        role_choices = ((name, name) for name in role_names)
        self.fields['roles'].choices = role_choices
        keystone_version = api.keystone.get_identity_api_version(request)
        if keystone_version < (3, 13):
            del self.fields['access_rules']
        if not settings.KUBECONFIG_ENABLED:
            self.fields['kubernetes_namespace'].widget = widgets.HiddenInput()

    # We have to protect the entire "data" dict because it contains the
    # secret string.
    @sensitive_variables('data')
    def handle(self, request, data):
        try:
            LOG.info('Creating application credential with name "%s"',
                     data['name'])

            expiration = None
            if data['expiration_date']:
                if data['expiration_time']:
                    expiration_time = data['expiration_time']
                else:
                    expiration_time = datetime.datetime.min.time()
                expiration = datetime.datetime.combine(
                    data['expiration_date'], expiration_time)
            else:
                if data['expiration_time']:
                    expiration_time = data['expiration_time']
                    expiration_date = datetime.date.today()
                    expiration = datetime.datetime.combine(expiration_date,
                                                           expiration_time)
            if data['roles']:
                # the role list received from the form is a list of dicts
                # encoded as strings
                roles = [{'name': role_name} for role_name in data['roles']]
            else:
                roles = None
            if data.get('access_rules'):
                access_rules = data['access_rules']
            else:
                access_rules = None
            new_app_cred = api.keystone.application_credential_create(
                request,
                name=data['name'],
                description=data['description'] or None,
                secret=data['secret'] or None,
                expires_at=expiration or None,
                roles=roles,
                access_rules=access_rules,
                unrestricted=data['unrestricted']
            )
            self.request.session['application_credential'] = \
                new_app_cred.to_dict()
            (self.request.session['application_credential']
                ['kubernetes_namespace']) = data['kubernetes_namespace']
            request.method = 'GET'
            return self.next_view.as_view()(request)
        except exceptions.Conflict:
            msg = (_('Application credential name "%s" is already used.')
                   % data['name'])
            messages.error(request, msg)
        except Exception:
            exceptions.handle(
                request, _('Unable to create application credential.'))

    def clean(self):
        cleaned_data = super().clean()
        try:
            cleaned_data['access_rules'] = yaml.safe_load(
                cleaned_data['access_rules'])
        except yaml.YAMLError:
            msg = (_('Access rules must be a valid JSON or YAML list.'))
            raise forms.ValidationError(msg)
        return cleaned_data


class CreateSuccessfulForm(forms.SelfHandlingForm):
    app_cred_id = forms.CharField(
        label=_("ID"),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    app_cred_name = forms.CharField(
        label=_("Name"),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    app_cred_secret = forms.CharField(
        label=_("Secret"),
        widget=forms.widgets.Textarea(
            attrs={'rows': 3, 'readonly': 'readonly'}))

    def handle(self, request, data):
        pass
