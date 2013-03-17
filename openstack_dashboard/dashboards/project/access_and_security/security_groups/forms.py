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
from ..floating_ips.utils import get_int_or_uuid


class CreateGroup(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"),
                           error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " ASCII characters and numbers.")},
                           validators=[validators.validate_slug])
    description = forms.CharField(label=_("Description"))

    def handle(self, request, data):
        try:
            sg = api.nova.security_group_create(request,
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
    id = forms.CharField(widget=forms.HiddenInput())
    ip_protocol = forms.ChoiceField(label=_('IP Protocol'),
                                    choices=[('tcp', _('TCP')),
                                             ('udp', _('UDP')),
                                             ('icmp', _('ICMP'))],
                                    help_text=_("The protocol which this "
                                                "rule should be applied to."),
                                    widget=forms.Select(attrs={
                                            'class': 'switchable',
                                            'data-slug': 'protocol'}))

    port_or_range = forms.ChoiceField(label=_('Open'),
                                      choices=[('port', _('Port')),
                                               ('range', _('Port Range'))],
                                      widget=forms.Select(attrs={
                                            'class': 'switchable switched',
                                            'data-slug': 'range',
                                            'data-switch-on': 'protocol',
                                            'data-protocol-tcp': _('Open'),
                                            'data-protocol-udp': _('Open')}))

    port = forms.IntegerField(label=_("Port"),
                              required=False,
                              help_text=_("Enter an integer value "
                                          "between 1 and 65535."),
                              widget=forms.TextInput(attrs={
                                   'class': 'switched',
                                   'data-switch-on': 'range',
                                   'data-range-port': _('Port')}),
                              validators=[validate_port_range])

    from_port = forms.IntegerField(label=_("From Port"),
                                   required=False,
                                   help_text=_("Enter an integer value "
                                               "between 1 and 65535."),
                                   widget=forms.TextInput(attrs={
                                        'class': 'switched',
                                        'data-switch-on': 'range',
                                        'data-range-range': _('From Port')}),
                                   validators=[validate_port_range])

    to_port = forms.IntegerField(label=_("To Port"),
                                 required=False,
                                 help_text=_("Enter an integer value "
                                             "between 1 and 65535."),
                                 widget=forms.TextInput(attrs={
                                        'class': 'switched',
                                        'data-switch-on': 'range',
                                        'data-range-range': _('To Port')}),
                                 validators=[validate_port_range])

    icmp_type = forms.IntegerField(label=_("Type"),
                                   required=False,
                                   help_text=_("Enter a value for ICMP type "
                                               "in the range (-1: 255)"),
                                   widget=forms.TextInput(attrs={
                                        'class': 'switched',
                                        'data-switch-on': 'protocol',
                                        'data-protocol-icmp': _('Type')}),
                                   validators=[validate_port_range])

    icmp_code = forms.IntegerField(label=_("Code"),
                                   required=False,
                                   help_text=_("Enter a value for ICMP code "
                                               "in the range (-1: 255)"),
                                   widget=forms.TextInput(attrs={
                                          'class': 'switched',
                                          'data-switch-on': 'protocol',
                                          'data-protocol-icmp': _('Code')}),
                                   validators=[validate_port_range])

    source = forms.ChoiceField(label=_('Source'),
                               choices=[('cidr', _('CIDR')),
                                        ('sg', _('Security Group'))],
                               help_text=_('To specify an allowed IP '
                                           'range, select "CIDR". To '
                                           'allow access from all '
                                           'members of another security '
                                           'group select "Security '
                                           'Group".'),
                               widget=forms.Select(attrs={
                                      'class': 'switchable',
                                      'data-slug': 'source'}))

    cidr = fields.IPField(label=_("CIDR"),
                          required=False,
                          initial="0.0.0.0/0",
                          help_text=_("Classless Inter-Domain Routing "
                                      "(e.g. 192.168.0.0/24)"),
                          version=fields.IPv4 | fields.IPv6,
                          mask=True,
                          widget=forms.TextInput(
                                attrs={'class': 'switched',
                                       'data-switch-on': 'source',
                                       'data-source-cidr': _('CIDR')}))

    security_group = forms.ChoiceField(label=_('Security Group'),
                                       required=False,
                                       widget=forms.Select(attrs={
                                          'class': 'switched',
                                          'data-switch-on': 'source',
                                          'data-source-sg': _('Security '
                                                              'Group')}))

    def __init__(self, *args, **kwargs):
        sg_list = kwargs.pop('sg_list', [])
        super(AddRule, self).__init__(*args, **kwargs)
        # Determine if there are security groups available for the
        # source group option; add the choices and enable the option if so.
        if sg_list:
            security_groups_choices = sg_list
        else:
            security_groups_choices = [("", _("No security groups available"))]
        self.fields['security_group'].choices = security_groups_choices

    def clean(self):
        cleaned_data = super(AddRule, self).clean()

        ip_proto = cleaned_data.get('ip_protocol')
        port_or_range = cleaned_data.get("port_or_range")
        source = cleaned_data.get("source")

        icmp_type = cleaned_data.get("icmp_type", None)
        icmp_code = cleaned_data.get("icmp_code", None)

        from_port = cleaned_data.get("from_port", None)
        to_port = cleaned_data.get("to_port", None)
        port = cleaned_data.get("port", None)

        if ip_proto == 'icmp':
            if icmp_type is None:
                msg = _('The ICMP type is invalid.')
                raise ValidationError(msg)
            if icmp_code is None:
                msg = _('The ICMP code is invalid.')
                raise ValidationError(msg)
            if icmp_type not in xrange(-1, 256):
                msg = _('The ICMP type not in range (-1, 255)')
                raise ValidationError(msg)
            if icmp_code not in xrange(-1, 256):
                msg = _('The ICMP code not in range (-1, 255)')
                raise ValidationError(msg)
            cleaned_data['from_port'] = icmp_type
            cleaned_data['to_port'] = icmp_code
        else:
            if port_or_range == "port":
                cleaned_data["from_port"] = port
                cleaned_data["to_port"] = port
                if port is None:
                    msg = _('The specified port is invalid.')
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

        if source == "cidr":
            cleaned_data['security_group'] = None
        else:
            cleaned_data['cidr'] = None

        return cleaned_data

    def handle(self, request, data):
        try:
            rule = api.nova.security_group_rule_create(
                        request,
                        get_int_or_uuid(data['id']),
                        data['ip_protocol'],
                        data['from_port'],
                        data['to_port'],
                        data['cidr'],
                        data['security_group'])
            messages.success(request,
                             _('Successfully added rule: %s') % unicode(rule))
            return rule
        except:
            redirect = reverse("horizon:project:access_and_security:"
                               "security_groups:detail", args=[data['id']])
            exceptions.handle(request,
                              _('Unable to add rule to security group.'),
                              redirect=redirect)
