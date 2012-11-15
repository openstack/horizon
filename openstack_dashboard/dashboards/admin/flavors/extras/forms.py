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

import logging

from django.utils.translation import ugettext_lazy as _

from openstack_dashboard import api
from horizon import exceptions
from horizon import forms
from horizon import messages

LOG = logging.getLogger(__name__)


class CreateExtraSpec(forms.SelfHandlingForm):
    key = forms.CharField(max_length="25", label=_("Key"))
    value = forms.CharField(max_length="25", label=_("Value"))
    flavor_id = forms.CharField(widget=forms.widgets.HiddenInput)

    def handle(self, request, data):
        try:
            api.nova.flavor_extra_set(request,
                                     data['flavor_id'],
                                     {data['key']: data['value']})
            msg = _('Created extra spec "%s".') % data['key']
            messages.success(request, msg)
            return True
        except:
            exceptions.handle(request,
                              _("Unable to create flavor extra spec."))


class EditExtraSpec(forms.SelfHandlingForm):
    key = forms.CharField(max_length="25", label=_("Key"))
    value = forms.CharField(max_length="25", label=_("Value"))
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
        except:
            exceptions.handle(request, _("Unable to edit extra spec."))
