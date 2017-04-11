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

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class AddProtocolForm(forms.SelfHandlingForm):
    idp_id = forms.CharField(label=_("Identity Provider ID"),
                             widget=forms.TextInput(
                                 attrs={'readonly': 'readonly'}))
    id = forms.CharField(label=_("Protocol ID"))
    mapping_id = forms.ThemableChoiceField(label=_("Mapping ID"))

    def __init__(self, request, *args, **kwargs):
        super(AddProtocolForm, self).__init__(request, *args, **kwargs)
        self.populate_mapping_id_choices(request)

    def populate_mapping_id_choices(self, request):
        try:
            mappings = api.keystone.mapping_list(request)
        except Exception as e:
            LOG.info('Failed to get mapping list %s', e)
            msg = _('Failed to get mapping list %s') % e
            messages.error(request, msg)

        choices = [(m.id, m.id) for m in mappings]
        choices.sort()

        if choices:
            choices.insert(0, ("", _("Select Mapping")))
        else:
            choices.insert(0, ("", _("No mappings available")))

        self.fields['mapping_id'].choices = choices

    def handle(self, request, data):
        try:
            new_mapping = api.keystone.protocol_create(
                request,
                data["id"],
                data["idp_id"],
                data["mapping_id"])
            messages.success(
                request,
                _("Identity provider protocol created successfully."))
            return new_mapping
        except exceptions.Conflict:
            msg = _('Protocol ID "%s" is already used.') % data["id"]
            messages.error(request, msg)
        except Exception:
            exceptions.handle(
                request,
                _("Unable to create identity provider protocol."))
