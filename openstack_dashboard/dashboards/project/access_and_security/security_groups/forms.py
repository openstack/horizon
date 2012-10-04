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

from django.core import validators
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils.validators import validate_port_range
from horizon.utils import fields

from openstack_dashboard import api


class CreateGroup(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"),
                           validators=[validators.validate_slug])
    description = forms.CharField(label=_("Description"))

    def handle(self, request, data):
        try:
            sg = api.security_group_create(request,
                                           data['name'],
                                           data['description'])
            messages.success(request,
                             _('Successfully created security group: %s')
                               % data['name'])
            return sg
        except:
            redirect = reverse("horizon:project:access_and_security:index")
            exceptions.handle(request,
                              _('Unable to create security group.'),
                              redirect=redirect)


class AddRule(forms.SelfHandlingForm):
    ip_protocol = forms.ChoiceField(label=_('IP Protocol'),
                                    choices=[('tcp', 'TCP'),
                                             ('udp', 'UDP'),
                                             ('icmp', 'ICMP')],
                                    help_text=_("The protocol which this "
                                                "rule should be applied to."),
                                    widget=forms.Select(attrs={'class':
                                                               'switchable'}))
    from_port = forms.IntegerField(label=_("From Port"),
                                   help_text=_("TCP/UDP: Enter integer value "
                                               "between 1 and 65535. ICMP: "
                                               "enter a value for ICMP type "
                                               "in the range (-1: 255)"),
                                   widget=forms.TextInput(
                                          attrs={'data': _('From Port'),
                                                 'data-icmp': _('Type')}),
                                   validators=[validate_port_range])
    to_port = forms.IntegerField(label=_("To Port"),
                                 help_text=_("TCP/UDP: Enter integer value "
                                             "between 1 and 65535. ICMP: "
                                             "enter a value for ICMP code "
                                             "in the range (-1: 255)"),
                                 widget=forms.TextInput(
                                        attrs={'data': _('To Port'),
                                               'data-icmp': _('Code')}),
                                 validators=[validate_port_range])

    source_group = forms.ChoiceField(label=_('Source Group'),
                                     required=False,
                                     help_text=_("To specify an allowed IP "
                                                 "range, select CIDR. To "
                                                 "allow access from all "
                                                 "members of another security "
                                                 "group select Source Group."))
    cidr = fields.IPField(label=_("CIDR"),
                           required=False,
                           initial="0.0.0.0/0",
                           help_text=_("Classless Inter-Domain Routing "
                                       "(e.g. 192.168.0.0/24)"),
                           version=fields.IPv4 | fields.IPv6,
                           mask=True)

    security_group_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        sg_list = kwargs.pop('sg_list', [])
        super(AddRule, self).__init__(*args, **kwargs)
        # Determine if there are security groups available for the
        # source group option; add the choices and enable the option if so.
        security_groups_choices = [("", "CIDR")]
        if sg_list:
            security_groups_choices.append(('Security Group', sg_list))
        self.fields['source_group'].choices = security_groups_choices

    def clean(self):
        cleaned_data = super(AddRule, self).clean()
        from_port = cleaned_data.get("from_port", None)
        to_port = cleaned_data.get("to_port", None)
        cidr = cleaned_data.get("cidr", None)
        ip_proto = cleaned_data.get('ip_protocol', None)
        source_group = cleaned_data.get("source_group", None)

        if ip_proto == 'icmp':
            if from_port is None:
                msg = _('The ICMP type is invalid.')
                raise ValidationError(msg)
            if to_port is None:
                msg = _('The ICMP code is invalid.')
                raise ValidationError(msg)
            if from_port not in xrange(-1, 256):
                msg = _('The ICMP type not in range (-1, 255)')
                raise ValidationError(msg)
            if to_port not in xrange(-1, 256):
                msg = _('The ICMP code not in range (-1, 255)')
                raise ValidationError(msg)
        else:
            if from_port is None:
                msg = _('The "from" port number is invalid.')
                raise ValidationError(msg)
            if to_port is None:
                msg = _('The "to" port number is invalid.')
                raise ValidationError(msg)
            if to_port < from_port:
                msg = _('The "to" port number must be greater than '
                        'or equal to the "from" port number.')
                raise ValidationError(msg)

        if source_group and cidr != self.fields['cidr'].initial:
            # Specifying a source group *and* a custom CIDR is invalid.
            msg = _('Either CIDR or Source Group may be specified, '
                    'but not both.')
            raise ValidationError(msg)
        elif source_group:
            # If a source group is specified, clear the CIDR from its default
            cleaned_data['cidr'] = None
        else:
            # If only cidr is specified, clear the source_group entirely
            cleaned_data['source_group'] = None

        return cleaned_data

    def handle(self, request, data):
        try:
            rule = api.security_group_rule_create(request,
                                                  data['security_group_id'],
                                                  data['ip_protocol'],
                                                  data['from_port'],
                                                  data['to_port'],
                                                  data['cidr'],
                                                  data['source_group'])
            messages.success(request,
                             _('Successfully added rule: %s') % unicode(rule))
            return rule
        except:
            redirect = reverse("horizon:project:access_and_security:index")
            exceptions.handle(request,
                              _('Unable to add rule to security group.'),
                              redirect=redirect)
