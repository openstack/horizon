# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging

from django.contrib import messages
from django import shortcuts
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import forms


LOG = logging.getLogger(__name__)


class FloatingIpAllocate(forms.SelfHandlingForm):
    tenant_name = forms.CharField(widget=forms.HiddenInput())
    pool = forms.ChoiceField(label=_("Pool"))

    def __init__(self, *args, **kwargs):
        super(FloatingIpAllocate, self).__init__(*args, **kwargs)
        floating_pool_list = kwargs.get('initial', {}).get('pool_list', [])
        self.fields['pool'].choices = floating_pool_list

    def handle(self, request, data):
        try:
            fip = api.tenant_floating_ip_allocate(request,
                                                  pool=data.get('pool', None))
            LOG.info('Allocating Floating IP "%s" to project "%s"'
                     % (fip.ip, data['tenant_name']))

            messages.success(request,
                             _('Successfully allocated Floating IP "%(ip)s" '
                               'to project "%(project)s"')
                             % {"ip": fip.ip, "project": data['tenant_name']})
        except:
            exceptions.handle(request, _('Unable to allocate Floating IP.'))
        return shortcuts.redirect(
                        'horizon:nova:access_and_security:index')
