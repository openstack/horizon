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
import re

from django.conf import settings
from django.forms import ValidationError
from django import http
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils
from horizon.utils import validators

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class PasswordMixin(forms.SelfHandlingForm):
    password = forms.RegexField(
        label=_("Password"),
        widget=forms.PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    confirm_password = forms.CharField(
        label=_("Confirm Password"),
        strip=False,
        widget=forms.PasswordInput(render_value=False))
    no_autocomplete = True

    def clean(self):
        '''Check to make sure password fields match.'''
        data = super().clean()
        if 'password' in data and 'confirm_password' in data:
            if data['password'] != data['confirm_password']:
                raise ValidationError(_('Passwords do not match.'))
        return data


class BaseUserForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        # Populate project choices
        project_choices = []

        # If the user is already set (update action), list only projects which
        # the user has access to.
        user_id = kwargs['initial'].get('id', None)
        domain_id = kwargs['initial'].get('domain_id', None)
        default_project_id = kwargs['initial'].get('project', None)

        try:
            projects, has_more = api.keystone.tenant_list(
                request, domain=domain_id)

            for project in sorted(projects, key=lambda p: p.name.lower()):
                if project.enabled:
                    project_choices.append((project.id, project.name))
            if not project_choices:
                project_choices.insert(0, ('', _("No available projects")))
            # TODO(david-lyle): if keystoneclient is fixed to allow unsetting
            # the default project, then this condition should be removed.
            elif default_project_id is None:
                project_choices.insert(0, ('', _("Select a project")))
            self.fields['project'].choices = project_choices

        except Exception:
            LOG.debug("User: %s has no projects", user_id)


class AddExtraColumnMixIn(object):
    def add_extra_fields(self, ordering=None):
        # add extra column defined by setting
        EXTRA_INFO = settings.USER_TABLE_EXTRA_INFO
        for key, value in EXTRA_INFO.items():
            self.fields[key] = forms.CharField(label=value,
                                               required=False)
            if ordering:
                ordering.append(key)


ADD_PROJECT_URL = "horizon:identity:projects:create"


class CreateUserForm(PasswordMixin, BaseUserForm, AddExtraColumnMixIn):
    # Hide the domain_id and domain_name by default
    domain_id = forms.CharField(label=_("Domain ID"),
                                required=False,
                                widget=forms.HiddenInput())
    domain_name = forms.CharField(label=_("Domain Name"),
                                  required=False,
                                  widget=forms.HiddenInput())
    name = forms.CharField(max_length=255, label=_("User Name"))
    description = forms.CharField(widget=forms.widgets.Textarea(
                                  attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    email = forms.EmailField(
        label=_("Email"),
        required=False)
    project = forms.ThemableDynamicChoiceField(label=_("Primary Project"),
                                               required=False,
                                               add_item_link=ADD_PROJECT_URL)
    role_id = forms.ThemableChoiceField(label=_("Role"),
                                        required=False)
    enabled = forms.BooleanField(label=_("Enabled"),
                                 required=False,
                                 initial=True)
    lock_password = forms.BooleanField(label=_("Lock password"),
                                       required=False,
                                       initial=False)

    def __init__(self, *args, **kwargs):
        roles = kwargs.pop('roles')
        super().__init__(*args, **kwargs)
        # Reorder form fields from multiple inheritance
        ordering = ["domain_id", "domain_name", "name",
                    "description", "email", "password",
                    "confirm_password", "project", "role_id",
                    "enabled", "lock_password"]
        self.add_extra_fields(ordering)
        self.fields = collections.OrderedDict(
            (key, self.fields[key]) for key in ordering)
        role_choices = [
            (role.id, role.name) for role in
            sorted(roles, key=lambda r: r.name.lower())
        ]
        self.fields['role_id'].choices = role_choices

        # For keystone V3, display the two fields in read-only
        readonlyInput = forms.TextInput(attrs={'readonly': 'readonly'})
        self.fields["domain_id"].widget = readonlyInput
        self.fields["domain_name"].widget = readonlyInput

    # We have to protect the entire "data" dict because it contains the
    # password and confirm_password strings.
    @sensitive_variables('data')
    def handle(self, request, data):
        domain = api.keystone.get_default_domain(self.request, False)
        try:
            LOG.info('Creating user with name "%s"', data['name'])
            desc = data["description"]
            if "email" in data:
                data['email'] = data['email'] or None

            # add extra information
            EXTRA_INFO = settings.USER_TABLE_EXTRA_INFO
            kwargs = dict((key, data.get(key)) for key in EXTRA_INFO)

            if "lock_password" in data:
                kwargs.update({'options':
                              {'lock_password': data['lock_password']}})

            new_user = \
                api.keystone.user_create(request,
                                         name=data['name'],
                                         email=data['email'],
                                         description=desc or None,
                                         password=data['password'],
                                         project=data['project'] or None,
                                         enabled=data['enabled'],
                                         domain=domain.id,
                                         **kwargs)
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


class UpdateUserForm(BaseUserForm, AddExtraColumnMixIn):
    # Hide the domain_id and domain_name by default
    domain_id = forms.CharField(label=_("Domain ID"),
                                required=False,
                                widget=forms.HiddenInput())
    domain_name = forms.CharField(label=_("Domain Name"),
                                  required=False,
                                  widget=forms.HiddenInput())
    id = forms.CharField(label=_("ID"), widget=forms.HiddenInput)
    name = forms.CharField(max_length=255, label=_("User Name"))
    description = forms.CharField(widget=forms.widgets.Textarea(
                                  attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    email = forms.EmailField(
        label=_("Email"),
        required=False)
    project = forms.ThemableChoiceField(label=_("Primary Project"),
                                        required=False)

    lock_password = forms.BooleanField(label=_("Lock password"),
                                       required=False,
                                       initial=False)

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.add_extra_fields()
        if api.keystone.keystone_can_edit_user() is False:
            for field in ('name', 'email'):
                self.fields.pop(field)
        readonlyInput = forms.TextInput(attrs={'readonly': 'readonly'})
        self.fields["domain_id"].widget = readonlyInput
        self.fields["domain_name"].widget = readonlyInput

    def handle(self, request, data):
        user = data.pop('id')

        data.pop('domain_id')
        data.pop('domain_name')

        if 'project' not in self.changed_data:
            data.pop('project')

        if 'description' not in self.changed_data:
            data.pop('description')
        if 'lock_password' in data:
            data.update({'options': {'lock_password': data['lock_password']}})
            data.pop('lock_password')

        try:
            if "email" in data:
                data['email'] = data['email']
            response = api.keystone.user_update(request, user, **data)
            messages.success(request,
                             _('User "%s" has been updated '
                               'successfully.') % data['name'])
        except exceptions.Conflict:
            msg = _('User name "%s" is already used.') % data['name']
            messages.error(request, msg)
            return False
        except Exception:
            response = exceptions.handle(request, ignore=True)
            messages.error(request, _('Unable to update the user.'))

        if isinstance(response, http.HttpResponse):
            return response

        return True


class ChangePasswordForm(PasswordMixin, forms.SelfHandlingForm):
    id = forms.CharField(widget=forms.HiddenInput)
    name = forms.CharField(
        label=_("User Name"),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
        required=False)

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        if settings.ENFORCE_PASSWORD_CHECK:
            self.fields["admin_password"] = forms.CharField(
                label=_("Admin Password"),
                strip=False,
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
        if settings.ENFORCE_PASSWORD_CHECK:
            admin_password = data.pop('admin_password')
            if not api.keystone.user_verify_admin_password(request,
                                                           admin_password):
                self.api_error(_('The admin password is incorrect.'))
                return False

        try:
            response = api.keystone.user_update_password(
                request, user_id, password, admin=False)
            if user_id == request.user.id:
                return utils.logout_with_message(
                    request,
                    _('Password changed. Please log in to continue.'),
                    redirect=False)
            messages.success(request,
                             _('User password has been updated successfully.'))
        except Exception as exc:
            response = exceptions.handle(request, ignore=True)
            match = re.match((r'The password does not match the '
                              r'requirements:(.*?) [(]HTTP 400[)]'), str(exc),
                             re.UNICODE | re.MULTILINE)
            if match:
                info = match.group(1)
                messages.error(request, _('The password does not match the '
                                          'requirements: %s') % info)
            else:
                messages.error(request,
                               _('Unable to update the user password.'))

        if isinstance(response, http.HttpResponse):
            return response

        return True
