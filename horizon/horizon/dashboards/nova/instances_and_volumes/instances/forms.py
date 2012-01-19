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

from horizon import api
from horizon import exceptions
from horizon import forms


LOG = logging.getLogger(__name__)


class UpdateInstance(forms.SelfHandlingForm):
    tenant_id = forms.CharField(widget=forms.HiddenInput())
    instance = forms.CharField(widget=forms.TextInput(
                               attrs={'readonly': 'readonly'}))
    name = forms.CharField(required=True)

    def handle(self, request, data):
        try:
            api.server_update(request, data['instance'], data['name'])
            messages.success(request,
                             _('Instance "%s" updated.') % data['name'])
        except:
            exceptions.handle(request, _('Unable to update instance.'))

        return shortcuts.redirect(
                        'horizon:nova:instances_and_volumes:index')
