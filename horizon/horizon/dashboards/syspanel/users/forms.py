# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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
from openstackx.api import exceptions as api_exceptions

from horizon import api
from horizon import forms


LOG = logging.getLogger(__name__)


class UserForm(forms.Form):
    def __init__(self, *args, **kwargs):
        tenant_list = kwargs.pop('tenant_list', None)
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['tenant_id'].choices = [[tenant.id, tenant.name]
                for tenant in tenant_list]

    name = forms.CharField(label=_("Name"))
    email = forms.CharField(label=_("Email"))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput(render_value=False),
                               required=False)
    tenant_id = forms.ChoiceField(label=_("Primary Tenant"))


class UserUpdateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        tenant_list = kwargs.pop('tenant_list', None)
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['tenant_id'].choices = [[tenant.id, tenant.name]
                for tenant in tenant_list]

    id = forms.CharField(label=_("ID"),
            widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    # FIXME: keystone doesn't return the username from a get API call.
    #name = forms.CharField(label=_("Name"))
    email = forms.CharField(label=_("Email"))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput(render_value=False),
                               required=False)
    tenant_id = forms.ChoiceField(label=_("Primary Tenant"))


class UserDeleteForm(forms.SelfHandlingForm):
    user = forms.CharField(required=True)

    def handle(self, request, data):
        user_id = data['user']
        LOG.info('Deleting user with id "%s"' % user_id)
        api.user_delete(request, user_id)
        messages.info(request, _('%(user)s was successfully deleted.')
                                % {"user": user_id})
        return shortcuts.redirect(request.build_absolute_uri())


class UserEnableDisableForm(forms.SelfHandlingForm):
    id = forms.CharField(label=_("ID (username)"), widget=forms.HiddenInput())
    enabled = forms.ChoiceField(label=_("enabled"), widget=forms.HiddenInput(),
                                choices=[[c, c]
                                         for c in ("disable", "enable")])

    def handle(self, request, data):
        user_id = data['id']
        enabled = data['enabled'] == "enable"

        try:
            api.user_update_enabled(request, user_id, enabled)
            messages.info(request,
                        _("User %(user)s %(state)s") %
                        {"user": user_id,
                        "state": "enabled" if enabled else "disabled"})
        except api_exceptions.ApiException:
            messages.error(request,
                        _("Unable to %(state)s user %(user)s") %
                        {"state": "enable" if enabled else "disable",
                        "user": user_id})

        return shortcuts.redirect(request.build_absolute_uri())
