# Copyright 2015, Alcatel-Lucent USA Inc.
# All Rights Reserved.
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
from django.core import validators
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

LOG = logging.getLogger(__name__)

validate_mac = validators.RegexValidator(r'([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}',
                                         _("Invalid MAC Address format"),
                                         code="invalid_mac")


class AddAllowedAddressPairForm(forms.SelfHandlingForm):
    ip = forms.IPField(label=_("IP Address or CIDR"),
                       help_text=_("A single IP Address or CIDR"),
                       version=forms.IPv4 | forms.IPv6,
                       mask=True)
    mac = forms.CharField(label=_("MAC Address"),
                          help_text=_("A valid MAC Address"),
                          validators=[validate_mac],
                          required=False)
    failure_url = 'horizon:project:networks:ports:detail'

    def clean(self):
        cleaned_data = super(AddAllowedAddressPairForm, self).clean()
        if '/' not in self.data['ip']:
            cleaned_data['ip'] = self.data['ip']
        return cleaned_data

    def handle(self, request, data):
        port_id = self.initial['port_id']
        try:
            port = api.neutron.port_get(request, port_id)

            current = port.get('allowed_address_pairs', [])
            current = [pair.to_dict() for pair in current]
            pair = {'ip_address': data['ip']}
            if data['mac']:
                pair['mac_address'] = data['mac']
            current.append(pair)
            port = api.neutron.port_update(request, port_id,
                                           allowed_address_pairs=current)
            msg = _('Port %s was successfully updated.') % port_id
            messages.success(request, msg)
            return port
        except Exception as e:
            LOG.error('Failed to update port %(port_id)s: %(reason)s',
                      {'port_id': port_id, 'reason': e})
            msg = _('Failed to update port "%s".') % port_id
            args = (self.initial.get('port_id'),)
            redirect = reverse(self.failure_url, args=args)
            exceptions.handle(request, msg, redirect=redirect)
            return False
