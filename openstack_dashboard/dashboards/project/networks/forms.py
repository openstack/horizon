# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 NEC Corporation
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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard import policy


LOG = logging.getLogger(__name__)


class UpdateNetwork(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), required=False)
    tenant_id = forms.CharField(widget=forms.HiddenInput)
    network_id = forms.CharField(label=_("ID"),
                                 widget=forms.TextInput(
                                     attrs={'readonly': 'readonly'}))
    admin_state = forms.ChoiceField(choices=[(True, _('UP')),
                                             (False, _('DOWN'))],
                                    required=False,
                                    label=_("Admin State"))
    shared = forms.BooleanField(label=_("Shared"), required=False)
    failure_url = 'horizon:project:networks:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdateNetwork, self).__init__(request, *args, **kwargs)

        if not policy.check((("network", "create_network:shared"),), request):
            self.fields['shared'].widget = forms.CheckboxInput(
                attrs={'disabled': True})
            self.fields['shared'].help_text = _(
                'Non admin users are not allowed to set shared option.')

    def handle(self, request, data):
        try:
            params = {'admin_state_up': (data['admin_state'] == 'True'),
                      'name': data['name'],
                      'shared': data['shared']}
            network = api.neutron.network_update(request,
                                                 data['network_id'],
                                                 **params)
            msg = _('Network %s was successfully updated.') % data['name']
            LOG.debug(msg)
            messages.success(request, msg)
            return network
        except Exception:
            msg = _('Failed to update network %s') % data['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
