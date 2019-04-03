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

from openstack_dashboard import api

from horizon import exceptions
from horizon import forms
from horizon import messages


KEY_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_.:-]+$", re.UNICODE)
KEY_ERROR_MESSAGES = {
    'invalid': _('Key names can only contain alphanumeric characters, '
                 'underscores, periods, colons and hyphens')}


class CreateExtraSpec(forms.SelfHandlingForm):
    key = forms.RegexField(max_length=255, label=_("Key"),
                           regex=KEY_NAME_REGEX,
                           error_messages=KEY_ERROR_MESSAGES)
    value = forms.CharField(max_length=255, label=_("Value"))

    def clean(self):
        data = super(CreateExtraSpec, self).clean()
        type_id = self.initial['type_id']
        extra_list = api.cinder.volume_type_extra_get(self.request,
                                                      type_id)
        if "key" in data:
            for extra in extra_list:
                if extra.key.lower() == data['key'].lower():
                    error_msg = _('Key with name "%s" already exists. Use '
                                  'Edit to update the value, else create key '
                                  'with different name.') % data['key']
                    raise forms.ValidationError(error_msg)

        return data

    def handle(self, request, data):
        type_id = self.initial['type_id']
        try:
            api.cinder.volume_type_extra_set(request,
                                             type_id,
                                             {data['key']: data['value']})
            msg = _('Created extra spec "%s".') % data['key']
            messages.success(request, msg)
            return True
        except Exception:
            redirect = reverse("horizon:admin:volume_types:index")
            exceptions.handle(request,
                              _("Unable to create volume type extra spec."),
                              redirect=redirect)


class EditExtraSpec(forms.SelfHandlingForm):
    value = forms.CharField(max_length=255, label=_("Value"))

    def handle(self, request, data):
        key = self.initial['key']
        type_id = self.initial['type_id']
        try:
            api.cinder.volume_type_extra_set(request,
                                             type_id,
                                             {key: data['value']})
            msg = _('Saved extra spec "%s".') % key
            messages.success(request, msg)
            return True
        except Exception:
            redirect = reverse("horizon:admin:volume_types:index")
            exceptions.handle(request,
                              _("Unable to edit volume type extra spec."),
                              redirect=redirect)
