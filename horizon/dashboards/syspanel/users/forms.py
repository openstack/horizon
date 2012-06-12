# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

import logging

from django import shortcuts
from django.contrib import messages
from django.forms import ValidationError
from django.utils.translation import force_unicode, ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon.utils import validators


LOG = logging.getLogger(__name__)


class BaseUserForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(BaseUserForm, self).__init__(*args, **kwargs)
        # Populate tenant choices
        tenant_choices = [('', _("Select a project"))]

        for tenant in api.tenant_list(request, admin=True):
            if tenant.enabled:
                tenant_choices.append((tenant.id, tenant.name))
        self.fields['tenant_id'].choices = tenant_choices

    @classmethod
    def _instantiate(cls, request, *args, **kwargs):
        return cls(request, *args, **kwargs)

    def clean(self):
        '''Check to make sure password fields match.'''
        data = super(forms.Form, self).clean()
        if 'password' in data:
            if data['password'] != data.get('confirm_password', None):
                raise ValidationError(_('Passwords do not match.'))
        return data


class CreateUserForm(BaseUserForm):
    name = forms.CharField(label=_("User Name"))
    email = forms.EmailField(label=_("Email"))
    password = forms.RegexField(
            label=_("Password"),
            widget=forms.PasswordInput(render_value=False),
            regex=validators.password_validator(),
            error_messages={'invalid': validators.password_validator_msg()})
    confirm_password = forms.CharField(
            label=_("Confirm Password"),
            required=False,
            widget=forms.PasswordInput(render_value=False))
    tenant_id = forms.ChoiceField(label=_("Primary Project"))
    role_id = forms.ChoiceField(label=_("Role"))

    def __init__(self, *args, **kwargs):
        roles = kwargs.pop('roles')
        super(CreateUserForm, self).__init__(*args, **kwargs)
        role_choices = [(role.id, role.name) for role in roles]
        self.fields['role_id'].choices = role_choices

    # We have to protect the entire "data" dict because it contains the
    # password and confirm_password strings.
    @sensitive_variables('data')
    def handle(self, request, data):
        try:
            LOG.info('Creating user with name "%s"' % data['name'])
            new_user = api.user_create(request,
                            data['name'],
                            data['email'],
                            data['password'],
                            data['tenant_id'],
                            True)
            messages.success(request,
                             _('User "%s" was successfully created.')
                             % data['name'])
            try:
                api.add_tenant_user_role(request,
                                         data['tenant_id'],
                                         new_user.id,
                                         data['role_id'])
            except:
                exceptions.handle(request,
                                  _('Unable to add user to primary project.'))
            return shortcuts.redirect('horizon:syspanel:users:index')
        except:
            exceptions.handle(request, _('Unable to create user.'))
            return shortcuts.redirect('horizon:syspanel:users:index')


class UpdateUserForm(BaseUserForm):
    id = forms.CharField(label=_("ID"), widget=forms.HiddenInput)
    name = forms.CharField(label=_("User Name"))
    email = forms.EmailField(label=_("Email"))
    password = forms.RegexField(label=_("Password"),
            widget=forms.PasswordInput(render_value=False),
            regex=validators.password_validator(),
            required=False,
            error_messages={'invalid':
                    validators.password_validator_msg()})
    confirm_password = forms.CharField(
            label=_("Confirm Password"),
            widget=forms.PasswordInput(render_value=False),
            required=False)
    tenant_id = forms.ChoiceField(label=_("Primary Project"))

    def __init__(self, request, *args, **kwargs):
        super(UpdateUserForm, self).__init__(request, *args, **kwargs)

        if api.keystone_can_edit_user() == False:
            for field in ('name', 'email', 'password', 'confirm_password'):
                self.fields.pop(field)

    # We have to protect the entire "data" dict because it contains the
    # password and confirm_password strings.
    @sensitive_variables('data', 'password')
    def handle(self, request, data):
        failed, succeeded = [], []
        user_is_editable = api.keystone_can_edit_user()
        user = data.pop('id')
        tenant = data.pop('tenant_id')
        data.pop('method')

        if user_is_editable:
            password = data.pop('password')
            data.pop('confirm_password', None)

        if user_is_editable:
            # Update user details
            msg_bits = (_('name'), _('email'))
            try:
                api.keystone.user_update(request, user, **data)
                succeeded.extend(msg_bits)
            except:
                failed.extend(msg_bits)
                exceptions.handle(request, ignore=True)

        # Update default tenant
        msg_bits = (_('primary project'),)
        try:
            api.user_update_tenant(request, user, tenant)
            succeeded.extend(msg_bits)
        except:
            failed.append(msg_bits)
            exceptions.handle(request, ignore=True)

        if user_is_editable:
            # If present, update password
            # FIXME(gabriel): password change should be its own form and view
            if password:
                msg_bits = (_('password'),)
                try:
                    api.user_update_password(request, user, password)
                    succeeded.extend(msg_bits)
                except:
                    failed.extend(msg_bits)
                    exceptions.handle(request, ignore=True)

        if succeeded:
            messages.success(request, _('User has been updated successfully.'))
        if failed:
            failed = map(force_unicode, failed)
            messages.error(request,
                           _('Unable to update %(attributes)s for the user.')
                             % {"attributes": ", ".join(failed)})
        return shortcuts.redirect('horizon:syspanel:users:index')
