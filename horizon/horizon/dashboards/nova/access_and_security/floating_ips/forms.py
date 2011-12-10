# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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
from django.contrib.auth.decorators import login_required
from django import shortcuts
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import forms


LOG = logging.getLogger(__name__)


class ReleaseFloatingIp(forms.SelfHandlingForm):
    floating_ip_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            LOG.info('Releasing Floating IP "%s"' % data['floating_ip_id'])
            api.tenant_floating_ip_release(request, data['floating_ip_id'])
            messages.info(request, _('Successfully released Floating IP: %s')
                                    % data['floating_ip_id'])
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in ReleaseFloatingIp")
            messages.error(request, _('Error releasing Floating IP '
                                      'from tenant: %s') % e.message)
        return shortcuts.redirect(request.build_absolute_uri())


class FloatingIpAssociate(forms.SelfHandlingForm):
    floating_ip_id = forms.CharField(widget=forms.HiddenInput())
    floating_ip = forms.CharField(widget=forms.TextInput(
                                            attrs={'readonly': 'readonly'}))
    instance_id = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(FloatingIpAssociate, self).__init__(*args, **kwargs)
        instancelist = kwargs.get('initial', {}).get('instances', [])
        self.fields['instance_id'] = forms.ChoiceField(
                choices=instancelist,
                label=_("Instance"))

    def handle(self, request, data):
        try:
            api.server_add_floating_ip(request,
                                       data['instance_id'],
                                       data['floating_ip_id'])
            LOG.info('Associating Floating IP "%s" with Instance "%s"'
                                % (data['floating_ip'], data['instance_id']))
            messages.info(request, _('Successfully associated Floating IP: \
                                    %(ip)s with Instance: %(inst)s'
                                    % {"ip": data['floating_ip'],
                                       "inst": data['instance_id']}))
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in FloatingIpAssociate")
            messages.error(request, _('Error associating Floating IP: %s')
                                     % e.message)
        return shortcuts.redirect(
                        'horizon:nova:access_and_security:index')


class FloatingIpDisassociate(forms.SelfHandlingForm):
    floating_ip_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            fip = api.tenant_floating_ip_get(request, data['floating_ip_id'])
            api.server_remove_floating_ip(request, fip.instance_id, fip.id)

            LOG.info('Disassociating Floating IP "%s"'
                      % data['floating_ip_id'])

            messages.info(request,
                          _('Successfully disassociated Floating IP: %s')
                          % data['floating_ip_id'])
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in FloatingIpAssociate")
            messages.error(request, _('Error disassociating Floating IP: %s')
                                     % e.message)
        return shortcuts.redirect(
                        'horizon:nova:access_and_security:index')


class FloatingIpAllocate(forms.SelfHandlingForm):
    tenant_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            fip = api.tenant_floating_ip_allocate(request)
            LOG.info('Allocating Floating IP "%s" to tenant "%s"'
                     % (fip.ip, data['tenant_id']))

            messages.success(request,
                             _('Successfully allocated Floating IP "%(ip)s"\
                                to tenant "%(tenant)s"')
                             % {"ip": fip.ip, "tenant": data['tenant_id']})

        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in FloatingIpAllocate")
            messages.error(request, _('Error allocating Floating IP "%(ip)s"\
                to tenant "%(tenant)s": %(msg)s') %
                {"ip": fip.ip, "tenant": data['tenant_id'], "msg": e.message})
        return shortcuts.redirect(
                        'horizon:nova:access_and_security:index')
