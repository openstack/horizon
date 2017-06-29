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

    def __init__(self, *args, **kwargs):
        super(FloatingIpAllocate, self).__init__(*args, **kwargs)
        floating_pool_list = kwargs.get('initial', {}).get('pool_list', [])
        self.fields['pool'].choices = floating_pool_list

    def handle(self, request, data):
        try:
            # Prevent allocating more IP than the quota allows
            usages = quotas.tenant_quota_usages(request,
                                                targets=('floating_ips', ))
            if usages['floating_ips']['available'] <= 0:
                error_message = _('You are already using all of your available'
                                  ' floating IPs.')
                self.api_error(error_message)
                return False

            fip = api.neutron.tenant_floating_ip_allocate(request,
                                                          pool=data['pool'])
            messages.success(request,
                             _('Allocated Floating IP %(ip)s.')
                             % {"ip": fip.ip})
            return fip
        except Exception:
            exceptions.handle(request, _('Unable to allocate Floating IP.'))
