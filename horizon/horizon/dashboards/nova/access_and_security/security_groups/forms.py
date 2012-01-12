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

from django import shortcuts
from django.contrib import messages
from django.core import validators
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import forms


LOG = logging.getLogger(__name__)


class CreateGroup(forms.SelfHandlingForm):
    name = forms.CharField(validators=[validators.validate_slug])
    description = forms.CharField()
    tenant_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            LOG.info('Add security_group: "%s"' % data)

            security_group = api.security_group_create(request,
                                                       data['name'],
                                                       data['description'])
            messages.success(request,
                             _('Successfully created security_group: %s')
                                    % data['name'])
            return shortcuts.redirect(
                    'horizon:nova:access_and_security:index')
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in CreateGroup")
            messages.error(request, _('Error creating security group: %s') %
                                     e.message)


class AddRule(forms.SelfHandlingForm):
    ip_protocol = forms.ChoiceField(choices=[('tcp', 'tcp'),
                                             ('udp', 'udp'),
                                             ('icmp', 'icmp')])
    from_port = forms.CharField()
    to_port = forms.CharField()
    cidr = forms.CharField()
    # TODO (anthony) source group support
    # group_id = forms.CharField()

    security_group_id = forms.CharField(widget=forms.HiddenInput())
    tenant_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        tenant_id = data['tenant_id']
        try:
            LOG.info('Add security_group_rule: "%s"' % data)

            rule = api.security_group_rule_create(request,
                                                  data['security_group_id'],
                                                  data['ip_protocol'],
                                                  data['from_port'],
                                                  data['to_port'],
                                                  data['cidr'])
            messages.success(request, _('Successfully added rule: %s') \
                                    % unicode(rule))
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in AddRule")
            messages.error(request, _('Error adding rule security group: %s')
                                     % e.message)
        return shortcuts.redirect("horizon:nova:access_and_security:index")
