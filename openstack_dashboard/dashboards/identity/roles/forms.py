# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


class CreateRoleForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Role Name"))

    def handle(self, request, data):
        try:
            new_user = api.keystone.role_create(request, data["name"])
            messages.success(request, _("Role created successfully."))
            return new_user
        except Exception:
            exceptions.handle(request, _('Unable to create role.'))


class UpdateRoleForm(forms.SelfHandlingForm):
    id = forms.CharField(label=_("ID"), widget=forms.HiddenInput)
    name = forms.CharField(label=_("Role Name"))

    def handle(self, request, data):
        try:
            api.keystone.role_update(request, data['id'], data["name"])
            messages.success(request, _("Role updated successfully."))
            return True
        except Exception:
            exceptions.handle(request, _('Unable to update role.'))
