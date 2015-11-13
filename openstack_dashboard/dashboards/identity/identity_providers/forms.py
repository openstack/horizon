# Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
#
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


class RegisterIdPForm(forms.SelfHandlingForm):
    id = forms.CharField(
        label=_("Identity Provider ID"),
        max_length=64,
        help_text=_("User-defined unique id to identify the identity "
                    "provider."))
    remote_ids = forms.CharField(
        label=_("Remote IDs"),
        required=False,
        help_text=_("Comma-delimited list of valid remote IDs from the "
                    "identity provider."))
    description = forms.CharField(
        label=_("Description"),
        widget=forms.widgets.Textarea(attrs={'rows': 4}),
        required=False)
    enabled = forms.BooleanField(
        label=_("Enabled"),
        required=False,
        help_text=_("Indicates whether this identity provider should accept "
                    "federated authentication requests."),
        initial=True)

    def handle(self, request, data):
        try:
            remote_ids = data["remote_ids"] or []
            if remote_ids:
                remote_ids = [rid.strip() for rid in remote_ids.split(',')]
            new_idp = api.keystone.identity_provider_create(
                request,
                data["id"],
                description=data["description"],
                enabled=data["enabled"],
                remote_ids=remote_ids)
            messages.success(request,
                             _("Identity provider registered successfully."))
            return new_idp
        except exceptions.Conflict:
            msg = _("Unable to register identity provider. Please check that "
                    "the Identity Provider ID and Remote IDs provided are "
                    "not already in use.")
            messages.error(request, msg)
        except Exception:
            exceptions.handle(request,
                              _("Unable to register identity provider."))
        return False


class UpdateIdPForm(forms.SelfHandlingForm):
    id = forms.CharField(
        label=_("Identity Provider ID"),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
        help_text=_("User-defined unique id to identify the identity "
                    "provider."))
    remote_ids = forms.CharField(
        label=_("Remote IDs"),
        required=False,
        help_text=_("Comma-delimited list of valid remote IDs from the "
                    "identity provider."))
    description = forms.CharField(
        label=_("Description"),
        widget=forms.widgets.Textarea(attrs={'rows': 4}),
        required=False)
    enabled = forms.BooleanField(
        label=_("Enabled"),
        required=False,
        help_text=_("Indicates whether this identity provider should accept "
                    "federated authentication requests."),
        initial=True)

    def handle(self, request, data):
        try:
            remote_ids = data["remote_ids"] or []
            if remote_ids:
                remote_ids = [rid.strip() for rid in remote_ids.split(',')]
            api.keystone.identity_provider_update(
                request,
                data['id'],
                description=data["description"],
                enabled=data["enabled"],
                remote_ids=remote_ids)
            messages.success(request,
                             _("Identity provider updated successfully."))
            return True
        except exceptions.Conflict:
            msg = _("Unable to update identity provider. Please check that "
                    "the Remote IDs provided are not already in use.")
            messages.error(request, msg)
        except Exception:
            exceptions.handle(request,
                              _('Unable to update identity provider.'))
        return False
