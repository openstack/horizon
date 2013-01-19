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

from django.forms import ValidationError
from django.utils.translation import force_unicode, ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import validators

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class BaseUserForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(BaseUserForm, self).__init__(request, *args, **kwargs)
        # Populate tenant choices
        tenant_choices = [('', _("Select a project"))]

        for tenant in api.keystone.tenant_list(request, admin=True):
            if tenant.enabled:
                tenant_choices.append((tenant.id, tenant.name))
        self.fields['tenant_id'].choices = tenant_choices

    def clean(self):
        '''Check to make sure password fields match.'''
        data = super(forms.Form, self).clean()
        if 'password' in data:
            if data['password'] != data.get('confirm_password', None):
                raise ValidationError(_('Passwords do not match.'))
        return data


ADD_PROJECT_URL = "horizon:admin:projects:create"


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
    tenant_id = forms.DynamicChoiceField(label=_("Primary Project"),
                                         add_item_link=ADD_PROJECT_URL)
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
            new_user = api.keystone.user_create(request,
                                                data['name'],
                                                data['email'],
                                                data['password'],
                                                data['tenant_id'],
                                                True)
            messages.success(request,
                             _('User "%s" was successfully created.')
                             % data['name'])
            if data['role_id']:
                try:
                    api.keystone.add_tenant_user_role(request,
                                             data['tenant_id'],
                                             new_user.id,
                                             data['role_id'])
                except:
                    exceptions.handle(request,
                                      _('Unable to add user'
                                        'to primary project.'))
            return new_user
        except:
            exceptions.handle(request, _('Unable to create user.'))


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

        if api.keystone.keystone_can_edit_user() is False:
            for field in ('name', 'email', 'password', 'confirm_password'):
                self.fields.pop(field)

    # We have to protect the entire "data" dict because it contains the
    # password and confirm_password strings.
    @sensitive_variables('data', 'password')
    def handle(self, request, data):
        failed, succeeded = [], []
        user_is_editable = api.keystone.keystone_can_edit_user()
        user = data.pop('id')
        tenant = data.pop('tenant_id')

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
            api.keystone.user_update_tenant(request, user, tenant)
            succeeded.extend(msg_bits)
        except:
            failed.append(msg_bits)
            exceptions.handle(request, ignore=True)

        # Check for existing roles
        # Show a warning if no role exists for the tenant
        user_roles = api.keystone.roles_for_user(request, user, tenant)
        if not user_roles:
            messages.warning(request,
                             _('The user %s has no role defined for' +
                             ' that project.')
                             % data.get('name', None))

        if user_is_editable:
            # If present, update password
            # FIXME(gabriel): password change should be its own form and view
            if password:
                msg_bits = (_('password'),)
                try:
                    api.keystone.user_update_password(request, user, password)
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
        return True
