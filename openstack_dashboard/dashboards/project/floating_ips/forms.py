# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright (c) 2012 X.commerce, a business unit of eBay Inc.
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.usage import quotas


class FloatingIpAllocate(forms.SelfHandlingForm):
    pool = forms.ThemableChoiceField(label=_("Pool"))
    description = forms.CharField(max_length=255,
                                  label=_("Description"),
                                  required=False)
    dns_domain = forms.CharField(max_length=255,
                                 label=_("DNS Domain"),
                                 required=False)
    dns_name = forms.CharField(max_length=255,
                               label=_("DNS Name"),
                               required=False)

    def __init__(self, request, *args, **kwargs):
        super(FloatingIpAllocate, self).__init__(request, *args, **kwargs)
        floating_pool_list = kwargs.get('initial', {}).get('pool_list', [])
        self.fields['pool'].choices = floating_pool_list

        dns_supported = api.neutron.is_extension_supported(
            request,
            "dns-integration")
        if not dns_supported:
            del self.fields["dns_name"]
            del self.fields["dns_domain"]

    def handle(self, request, data):
        try:
            # Prevent allocating more IP than the quota allows
            usages = quotas.tenant_quota_usages(request,
                                                targets=('floatingip', ))
            if ('floatingip' in usages and
                    usages['floatingip']['available'] <= 0):
                error_message = _('You are already using all of your available'
                                  ' floating IPs.')
                self.api_error(error_message)
                return False

            param = {}
            if data['description']:
                param['description'] = data['description']
            if 'dns_domain' in data and data['dns_domain']:
                param['dns_domain'] = data['dns_domain']
            if 'dns_name' in data and data['dns_name']:
                param['dns_name'] = data['dns_name']
            fip = api.neutron.tenant_floating_ip_allocate(
                request,
                pool=data['pool'],
                **param)
            messages.success(request,
                             _('Allocated Floating IP %(ip)s.')
                             % {"ip": fip.ip})
            return fip
        except Exception:
            exceptions.handle(request, _('Unable to allocate Floating IP.'))
