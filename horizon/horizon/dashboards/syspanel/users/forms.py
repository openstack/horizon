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
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import forms


LOG = logging.getLogger(__name__)


class BaseUserForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(BaseUserForm, self).__init__(*args, **kwargs)
        # Populate tenant choices
        tenant_choices = [('', "Select a tenant")]
        for tenant in api.tenant_list(request, admin=True):
            if tenant.enabled:
                tenant_choices.append((tenant.id, tenant.name))
        self.fields['tenant_id'].choices = tenant_choices

    @classmethod
    def _instantiate(cls, request, *args, **kwargs):
        return cls(request, *args, **kwargs)


class CreateUserForm(BaseUserForm):
    name = forms.CharField(label=_("Name"))
    email = forms.EmailField(label=_("Email"))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput(render_value=False),
                               required=False)
    tenant_id = forms.ChoiceField(label=_("Primary Project"))

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
                default_role = api.keystone.get_default_role(request)
                if default_role:
                    api.add_tenant_user_role(request,
                                             data['tenant_id'],
                                             new_user.id,
                                             default_role.id)
            except:
                exceptions.handle(request,
                                  _('Unable to add user to primary tenant.'))
            return shortcuts.redirect('horizon:syspanel:users:index')
        except:
            exceptions.handle(request, _('Unable to create user.'))
            return shortcuts.redirect('horizon:syspanel:users:index')


class UpdateUserForm(BaseUserForm):
    id = forms.CharField(label=_("ID"), widget=forms.HiddenInput)
    name = forms.CharField(label=_("User Name"))
    email = forms.EmailField(label=_("Email"))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput(render_value=False),
                               required=False)
    tenant_id = forms.ChoiceField(label=_("Primary Project"))

    def handle(self, request, data):
        failed, succeeded = [], []
        user = data.pop('id')
        password = data.pop('password')
        tenant = data.pop('tenant_id')
        # Discard the "method" param so we can pass kwargs to keystoneclient
        data.pop('method')

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
            messages.success(request,
                             _('Updated %(attributes)s for "%(user)s".')
                               % {"user": data["name"],
                                  "attributes": ", ".join(succeeded)})
        if failed:
            messages.error(request,
                           _('Unable to update %(attributes)s for "%(user)s".')
                             % {"user": data["name"],
                                "attributes": ", ".join(failed)})
        return shortcuts.redirect('horizon:syspanel:users:index')
