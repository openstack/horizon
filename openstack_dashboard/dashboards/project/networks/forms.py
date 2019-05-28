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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard import policy


LOG = logging.getLogger(__name__)


class UpdateNetwork(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), required=False)
    admin_state = forms.BooleanField(
        label=_("Enable Admin State"),
        required=False,
        help_text=_("If checked, the network will be enabled."))
    shared = forms.BooleanField(label=_("Shared"), required=False)
    failure_url = 'horizon:project:networks:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdateNetwork, self).__init__(request, *args, **kwargs)

        if not policy.check((("network", "update_network:shared"),), request):
            self.fields['shared'].widget = forms.HiddenInput()

    def handle(self, request, data):
        try:
            params = {'admin_state_up': data['admin_state'],
                      'name': data['name']}
            # Make sure we are not sending shared data when the user
            # doesn't have admin rights because even if the user doesn't
            # change it neutron sends back a 403 error
            if policy.check((("network", "update_network:shared"),), request):
                params['shared'] = data['shared']
            network = api.neutron.network_update(request,
                                                 self.initial['network_id'],
                                                 **params)
            msg = (_('Network %s was successfully updated.') %
                   network.name_or_id)
            messages.success(request, msg)
            return network
        except Exception as e:
            LOG.info('Failed to update network %(id)s: %(exc)s',
                     {'id': self.initial['network_id'], 'exc': e})
            name_or_id = data['name'] or self.initial['network_id']
            msg = _('Failed to update network %s') % name_or_id
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
