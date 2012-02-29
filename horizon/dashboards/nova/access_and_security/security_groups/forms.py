# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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
from django.forms import ValidationError
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon.utils.validators import validate_ipv4_cidr


LOG = logging.getLogger(__name__)


class CreateGroup(forms.SelfHandlingForm):
    name = forms.CharField(validators=[validators.validate_slug])
    description = forms.CharField()
    tenant_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            api.security_group_create(request,
                                      data['name'],
                                      data['description'])
            messages.success(request,
                             _('Successfully created security_group: %s')
                                    % data['name'])
        except:
            exceptions.handle(request, _('Unable to create security group.'))
        return shortcuts.redirect('horizon:nova:access_and_security:index')


class AddRule(forms.SelfHandlingForm):
    ip_protocol = forms.ChoiceField(label=_('IP protocol'),
                                    choices=[('tcp', 'tcp'),
                                             ('udp', 'udp'),
                                             ('icmp', 'icmp')],
                                    widget=forms.Select(attrs={'class':
                                                               'switchable'}))
    from_port = forms.IntegerField(label=_("From port"),
                                   help_text=_("TCP/UDP: Enter integer value "
                                               "between 1 and 65535. ICMP: "
                                               "enter a value for ICMP type "
                                               "in the range (-1: 255)"),
                                   widget=forms.TextInput(
                                          attrs={'data': _('From port'),
                                                 'data-icmp': _('Type')}))
    to_port = forms.IntegerField(label=_("To port"),
                                 help_text=_("TCP/UDP: Enter integer value "
                                             "between 1 and 65535. ICMP: "
                                             "enter a value for ICMP code "
                                             "in the range (-1: 255)"),
                                 widget=forms.TextInput(
                                        attrs={'data': _('To port'),
                                               'data-icmp': _('Code')}))
    cidr = forms.CharField(label=_("CIDR"),
                           help_text=_("Classless Inter-Domain Routing "
                                       "(i.e. 192.168.0.0/24"),
                           validators=[validate_ipv4_cidr])
    # TODO (anthony) source group support
    # group_id = forms.CharField()

    security_group_id = forms.IntegerField(widget=forms.HiddenInput())
    tenant_id = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super(AddRule, self).clean()
        if cleaned_data["to_port"] < cleaned_data["from_port"]:
            msg = _('The "to" port number must be greater than or equal to '
                    'the "from" port number.')
            raise ValidationError(msg)
        return cleaned_data

    def handle(self, request, data):
        try:
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
