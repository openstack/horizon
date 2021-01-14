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

import re

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


KEY_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_.:-]+$", re.UNICODE)
KEY_ERROR_MESSAGES = {
    'invalid': _('Key names can only contain alphanumeric characters, '
                 'underscores, periods, colons and hyphens')}


class CreateSpec(forms.SelfHandlingForm):
    key = forms.RegexField(max_length=255, label=_("Key"),
                           regex=KEY_NAME_REGEX,
                           error_messages=KEY_ERROR_MESSAGES)
    value = forms.CharField(max_length=255, label=_("Value"))

    def handle(self, request, data):
        group_type_id = self.initial['group_type_id']
        error_msg = _('key with name "%s" already exists.Use Edit to '
                      'update the value, else create key with different '
                      'name.') % data['key']
        try:
            specs_list = api.cinder.group_type_spec_list(self.request,
                                                         group_type_id)
            for spec in specs_list:
                if spec.key.lower() == data['key'].lower():
                    raise forms.ValidationError(error_msg)
            api.cinder.group_type_spec_set(request,
                                           group_type_id,
                                           {data['key']: data['value']})

            msg = _('Created group type spec "%s".') % data['key']
            messages.success(request, msg)
            return True
        except forms.ValidationError:
            messages.error(request, error_msg)
        except Exception:
            redirect = reverse("horizon:admin:group_types:index")
            exceptions.handle(request,
                              _("Unable to create group type spec."),
                              redirect=redirect)


class EditSpec(forms.SelfHandlingForm):
    value = forms.CharField(max_length=255, label=_("Value"))

    def handle(self, request, data):
        key = self.initial['key']
        group_type_id = self.initial['group_type_id']
        try:
            api.cinder.group_type_spec_set(request,
                                           group_type_id,
                                           {key: data['value']})
            msg = _('Saved group type spec "%s".') % key
            messages.success(request, msg)
            return True
        except Exception:
            redirect = reverse("horizon:admin:group_types:index")
            exceptions.handle(request,
                              _("Unable to edit group type spec."),
                              redirect=redirect)
