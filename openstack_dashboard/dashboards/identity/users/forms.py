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

import collections
import logging

import django
from django.conf import settings
from django.forms import ValidationError  # noqa
from django import http
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils
from horizon.utils import validators

from openstack_dashboard import api


LOG = logging.getLogger(__name__)
PROJECT_REQUIRED = api.keystone.VERSIONS.active < 3


class PasswordMixin(forms.SelfHandlingForm):
    password = forms.RegexField(
        label=_("Password"),
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    confirm_password = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(render_value=False))
    no_autocomplete = True

    def clean(self):
        '''Check to make sure password fields match.'''
        data = super(forms.Form, self).clean()
        if 'password' in data:
            if data['password'] != data.get('confirm_password', None):
                raise ValidationError(_('Passwords do not match.'))
        return data


class BaseUserForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(BaseUserForm, self).__init__(request, *args, **kwargs)

        # Populate project choices
        project_choices = []

        # If the user is already set (update action), list only projects which
        # the user has access to.
        user_id = kwargs['initial'].get('id', None)
        domain_id = kwargs['initial'].get('domain_id', None)
        projects, has_more = api.keystone.tenant_list(request,
                                                      domain=domain_id,
                                                      user=user_id)
        for project in projects:
            if project.enabled:
                project_choices.append((project.id, project.name))
        if not project_choices:
            project_choices.insert(0, ('', _("No available projects")))
        elif len(project_choices) > 1:
            project_choices.insert(0, ('', _("Select a project")))
        self.fields['project'].choices = project_choices


ADD_PROJECT_URL = "horizon:identity:projects:create"


class CreateUserForm(PasswordMixin, BaseUserForm):
    # Hide the domain_id and domain_name by default
    domain_id = forms.CharField(label=_("Domain ID"),
                                required=False,
                                widget=forms.HiddenInput())
    domain_name = forms.CharField(label=_("Domain Name"),
                                  required=False,
                                  widget=forms.HiddenInput())
    name = forms.CharField(max_length=255, label=_("User Name"))
    email = forms.EmailField(
        label=_("Email"),
        required=False)
    project = forms.DynamicChoiceField(label=_("Primary Project"),
                                       required=PROJECT_REQUIRED,
                                       add_item_link=ADD_PROJECT_URL)
    role_id = forms.ChoiceField(label=_("Role"),
                                required=PROJECT_REQUIRED)

    def __init__(self, *args, **kwargs):
        roles = kwargs.pop('roles')
        super(CreateUserForm, self).__init__(*args, **kwargs)
        # Reorder form fields from multiple inheritance
        ordering = ["domain_id", "domain_name", "name", "email", "password",
                    "confirm_password", "project", "role_id"]
        # Starting from 1.7 Django uses OrderedDict for fields and keyOrder
        # no longer works for it
        if django.VERSION >= (1, 7):
            self.fields = collections.OrderedDict(
                (key, self.fields[key]) for key in ordering)
        else:
            self.fields.keyOrder = ordering
        role_choices = [(role.id, role.name) for role in roles]
        self.fields['role_id'].choices = role_choices

        # For keystone V3, display the two fields in read-only
        if api.keystone.VERSIONS.active >= 3:
            readonlyInput = forms.TextInput(attrs={'readonly': 'readonly'})
            self.fields["domain_id"].widget = readonlyInput
            self.fields["domain_name"].widget = readonlyInput

    # We have to protect the entire "data" dict because it contains the
    # password and confirm_password strings.
    @sensitive_variables('data')
    def handle(self, request, data):
        domain = api.keystone.get_default_domain(self.request)
        try:
            LOG.info('Creating user with name "%s"' % data['name'])
            if "email" in data:
                data['email'] = data['email'] or None
            new_user = api.keystone.user_create(request,
                                                name=data['name'],
                                                email=data['email'],
                                                password=data['password'],
                                                project=data['project'],
                                                enabled=True,
                                                domain=domain.id)
            messages.success(request,
                             _('User "%s" was successfully created.')
                             % data['name'])
            if data['project'] and data['role_id']:
                roles = api.keystone.roles_for_user(request,
                                                    new_user.id,
                                                    data['project']) or []
                assigned = [role for role in roles if role.id == str(
                    data['role_id'])]
                if not assigned:
                    try:
                        api.keystone.add_tenant_user_role(request,
                                                          data['project'],
                                                          new_user.id,
                                                          data['role_id'])
                    except Exception:
                        exceptions.handle(request,
                                          _('Unable to add user '
                                            'to primary project.'))
            return new_user
        except exceptions.Conflict:
            msg = _('User name "%s" is already used.') % data['name']
            messages.error(request, msg)
        except Exception:
            exceptions.handle(request, _('Unable to create user.'))


class UpdateUserForm(BaseUserForm):
    # Hide the domain_id and domain_name by default
    domain_id = forms.CharField(label=_("Domain ID"),
                                required=False,
                                widget=forms.HiddenInput())
    domain_name = forms.CharField(label=_("Domain Name"),
                                  required=False,
                                  widget=forms.HiddenInput())
    id = forms.CharField(label=_("ID"), widget=forms.HiddenInput)
    name = forms.CharField(max_length=255, label=_("User Name"))
    email = forms.EmailField(
        label=_("Email"),
        required=False)
    project = forms.ChoiceField(label=_("Primary Project"),
                                required=PROJECT_REQUIRED)

    def __init__(self, request, *args, **kwargs):
        super(UpdateUserForm, self).__init__(request, *args, **kwargs)

        if api.keystone.keystone_can_edit_user() is False:
            for field in ('name', 'email'):
                self.fields.pop(field)
        # For keystone V3, display the two fields in read-only
        if api.keystone.VERSIONS.active >= 3:
            readonlyInput = forms.TextInput(attrs={'readonly': 'readonly'})
            self.fields["domain_id"].widget = readonlyInput
            self.fields["domain_name"].widget = readonlyInput

    def handle(self, request, data):
        user = data.pop('id')

        data.pop('domain_id')
        data.pop('domain_name')
        try:
            if "email" in data:
                data['email'] = data['email'] or None
            response = api.keystone.user_update(request, user, **data)
            messages.success(request,
                             _('User has been updated successfully.'))
        except exceptions.Conflict:
            msg = _('User name "%s" is already used.') % data['name']
            messages.error(request, msg)
            return False
        except Exception:
            response = exceptions.handle(request, ignore=True)
            messages.error(request, _('Unable to update the user.'))

        if isinstance(response, http.HttpResponse):
            return response
        else:
            return True


class ChangePasswordForm(PasswordMixin, forms.SelfHandlingForm):
    id = forms.CharField(widget=forms.HiddenInput)
    name = forms.CharField(
        label=_("User Name"),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
        required=False)

    def __init__(self, request, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(request, *args, **kwargs)

        if getattr(settings, 'ENFORCE_PASSWORD_CHECK', False):
            self.fields["admin_password"] = forms.CharField(
                label=_("Admin Password"),
                widget=forms.PasswordInput(render_value=False))
            # Reorder form fields from multiple inheritance
            self.fields.keyOrder = ["id", "name", "admin_password",
                                    "password", "confirm_password"]

    @sensitive_variables('data', 'password', 'admin_password')
    def handle(self, request, data):
        user_id = data.pop('id')
        password = data.pop('password')
        admin_password = None

        # Throw away the password confirmation, we're done with it.
        data.pop('confirm_password', None)

        # Verify admin password before changing user password
        if getattr(settings, 'ENFORCE_PASSWORD_CHECK', False):
            admin_password = data.pop('admin_password')
            if not api.keystone.user_verify_admin_password(request,
                                                           admin_password):
                self.api_error(_('The admin password is incorrect.'))
                return False

        try:
            response = api.keystone.user_update_password(
                request, user_id, password)
            if user_id == request.user.id:
                return utils.logout_with_message(
                    request,
                    _('Password changed. Please log in to continue.'),
                    redirect=False)
            messages.success(request,
                             _('User password has been updated successfully.'))
        except Exception:
            response = exceptions.handle(request, ignore=True)
            messages.error(request, _('Unable to update the user password.'))

        if isinstance(response, http.HttpResponse):
            return response
        else:
            return True
