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
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import exceptions
from horizon import forms


LOG = logging.getLogger(__name__)


class FloatingIpAssociate(forms.SelfHandlingForm):
    floating_ip_id = forms.CharField(widget=forms.HiddenInput())
    floating_ip = forms.CharField(label=_("Floating IP"),
                                  widget=forms.TextInput(
                                            attrs={'readonly': 'readonly'}))
    instance_id = forms.ChoiceField(label=_("Instance ID"))

    def __init__(self, *args, **kwargs):
        super(FloatingIpAssociate, self).__init__(*args, **kwargs)
        instancelist = kwargs.get('initial', {}).get('instances', [])
        if instancelist:
            instancelist.insert(0, ("", _("Select an instance")))
        else:
            instancelist = (("", _("No instances available")),)
        self.fields['instance_id'] = forms.ChoiceField(
                choices=instancelist,
                label=_("Instance"))

    def handle(self, request, data):
        ip_id = int(data['floating_ip_id'])
        try:
            api.server_add_floating_ip(request,
                                       data['instance_id'],
                                       ip_id)
            LOG.info('Associating Floating IP "%s" with Instance "%s"'
                                % (data['floating_ip'], data['instance_id']))
            messages.success(request,
                             _('Successfully associated Floating IP %(ip)s '
                               'with Instance: %(inst)s')
                               % {"ip": data['floating_ip'],
                                  "inst": data['instance_id']})
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in FloatingIpAssociate")
            messages.error(request, _('Error associating Floating IP: %s') % e)
        return shortcuts.redirect('horizon:nova:access_and_security:index')


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
