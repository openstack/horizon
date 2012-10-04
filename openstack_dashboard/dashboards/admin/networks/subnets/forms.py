# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from horizon import forms
from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.subnets import \
        forms as user_forms


LOG = logging.getLogger(__name__)


class CreateSubnet(user_forms.CreateSubnet):
    failure_url = 'horizon:admin:networks:detail'

    def handle(self, request, data):
        try:
            # We must specify tenant_id of the network which a subnet is
            # created for if admin user does not belong to the tenant.
            network = api.quantum.network_get(request, data['network_id'])
            data['tenant_id'] = network.tenant_id
        except:
            msg = _('Failed to retrieve network %s for a subnet') \
                % data['network_id']
            LOG.info(msg)
            redirect = reverse(self.failure_url, args=[data['network_id']])
            exceptions.handle(request, msg, redirect=redirect)
        return super(CreateSubnet, self).handle(request, data)


class UpdateSubnet(user_forms.UpdateSubnet):
    tenant_id = forms.CharField(widget=forms.HiddenInput())
    failure_url = 'horizon:admin:networks:detail'
