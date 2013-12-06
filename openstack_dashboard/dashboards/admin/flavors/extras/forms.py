# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright (c) 2012 Intel, Inc.
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

from django.conf import settings
from django.forms import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard import api

from horizon import exceptions
from horizon import forms
from horizon import messages

import re


class CreateExtraSpec(forms.SelfHandlingForm):
    _extraspec_name_regex = re.compile(r"^[\w\.\-: ]+$", re.UNICODE)
    keys = forms.ChoiceField(label=_("Keys"),
                             widget=forms.Select(attrs={
                                 'class': 'switchable',
                                 'data-slug': 'keys'}))
    key = forms.RegexField(
        max_length="255",
        label=_("Key"),
        required=False,
        regex=_extraspec_name_regex,
        error_messages={'invalid': _('Key Name may only contain letters, '
                            'numbers, underscores, periods, colons, '
                            'spaces and hyphens.')},
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'keys',
            'data-keys-custom': _('Key')}))
    value = forms.CharField(max_length="255", label=_("Value"))
    flavor_id = forms.CharField(widget=forms.widgets.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(CreateExtraSpec, self).__init__(*args, **kwargs)
        key_settings = getattr(settings, 'FLAVOR_EXTRA_KEYS', {})
        key_list = key_settings.get('flavor_keys', [])
        self.fields['keys'].choices = key_list + [('custom', _('Other Key'))]

    def clean(self):
        cleaned_data = super(CreateExtraSpec, self).clean()
        keys = cleaned_data.get('keys', None)
        key = cleaned_data.get('key', None)
        if keys == 'custom' and key == "":
            msg = _('This field is required.')
            self._errors["key"] = self.error_class([msg])
        return cleaned_data

    def handle(self, request, data):
        if data["keys"] != 'custom':
            data['key'] = data['keys']
        try:
            api.nova.flavor_extra_set(request,
                                     data['flavor_id'],
                                     {data['key']: data['value']})
            msg = _('Created extra spec "%s".') % data['key']
            messages.success(request, msg)
            return True
        except Exception:
            exceptions.handle(request,
                              _("Unable to create flavor extra spec."))


class EditExtraSpec(forms.SelfHandlingForm):
    key = forms.CharField(widget=forms.widgets.HiddenInput)
    value = forms.CharField(max_length="255", label=_("Value"))
    flavor_id = forms.CharField(widget=forms.widgets.HiddenInput)

    def handle(self, request, data):
        flavor_id = data['flavor_id']
        try:
            api.nova.flavor_extra_set(request,
                                     flavor_id,
                                     {data['key']: data['value']})
            msg = _('Saved extra spec "%s".') % data['key']
            messages.success(request, msg)
            return True
        except Exception:
            exceptions.handle(request, _("Unable to edit extra spec."))
