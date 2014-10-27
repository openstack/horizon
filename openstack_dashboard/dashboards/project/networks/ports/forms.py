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


LOG = logging.getLogger(__name__)


class UpdatePort(forms.SelfHandlingForm):
    network_id = forms.CharField(widget=forms.HiddenInput())
    port_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False)
    # TODO(amotoki): make UP/DOWN translatable
    admin_state = forms.ChoiceField(choices=[(True, 'UP'), (False, 'DOWN')],
                                    label=_("Admin State"))
    failure_url = 'horizon:project:networks:detail'

    def __init__(self, request, *args, **kwargs):
        super(UpdatePort, self).__init__(request, *args, **kwargs)
        if api.neutron.is_extension_supported(request, 'mac-learning'):
            self.fields['mac_state'] = forms.BooleanField(
                label=_("Mac Learning State"), required=False)

    def handle(self, request, data):
        data['admin_state'] = (data['admin_state'] == 'True')
        try:
            LOG.debug('params = %s' % data)
            extension_kwargs = {}
            if 'mac_state' in data:
                extension_kwargs['mac_learning_enabled'] = data['mac_state']
            port = api.neutron.port_update(request, data['port_id'],
                                           name=data['name'],
                                           admin_state_up=data['admin_state'],
                                           **extension_kwargs)
            msg = _('Port %s was successfully updated.') % data['port_id']
            LOG.debug(msg)
            messages.success(request, msg)
            return port
        except Exception:
            msg = _('Failed to update port %s') % data['port_id']
            LOG.info(msg)
            redirect = reverse(self.failure_url,
                               args=[data['network_id']])
            exceptions.handle(request, msg, redirect=redirect)
