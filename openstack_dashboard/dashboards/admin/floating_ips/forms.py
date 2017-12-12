# Copyright 2016 Letv Cloud Computing
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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


class AdminFloatingIpAllocate(forms.SelfHandlingForm):
    pool = forms.ThemableChoiceField(label=_("Pool"))
    tenant = forms.ThemableChoiceField(label=_("Project"))
    floating_ip_address = forms.IPField(
        label=_("Floating IP Address (optional)"),
        required=False,
        initial="",
        help_text=_("The IP address of the new floating IP (e.g. 202.2.3.4). "
                    "You need to specify an explicit address which is under "
                    "the public network CIDR (e.g. 202.2.3.0/24)."),
        mask=False)
    description = forms.CharField(max_length=255,
                                  label=_("Description"),
                                  required=False)

    def __init__(self, *args, **kwargs):
        super(AdminFloatingIpAllocate, self).__init__(*args, **kwargs)
        floating_pool_list = kwargs.get('initial', {}).get('pool_list', [])
        self.fields['pool'].choices = floating_pool_list
        tenant_list = kwargs.get('initial', {}).get('tenant_list', [])
        self.fields['tenant'].choices = tenant_list

    def handle(self, request, data):
        try:
            # Admin ignore quota
            param = {}
            if data['floating_ip_address']:
                param['floating_ip_address'] = data['floating_ip_address']
            if data['description']:
                param['description'] = data['description']
            subnet = api.neutron.subnet_get(request, data['pool'])
            param['subnet_id'] = subnet.id
            fip = api.neutron.tenant_floating_ip_allocate(
                request,
                pool=subnet.network_id,
                tenant_id=data['tenant'],
                **param)
            messages.success(
                request,
                _('Allocated floating IP %(ip)s.') % {"ip": fip.ip})
            return fip
        except Exception:
            redirect = reverse('horizon:admin:floating_ips:index')
            msg = _('Unable to allocate floating IP.')
            exceptions.handle(request, msg, redirect=redirect)
