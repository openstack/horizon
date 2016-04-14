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

import netaddr

from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _

import six

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import validators as utils_validators

from openstack_dashboard import api
from openstack_dashboard.utils import filters


class GroupBase(forms.SelfHandlingForm):
    """Base class to handle creation and update of security groups.

    Children classes must define two attributes:

    .. attribute:: success_message

        A success message containing the placeholder %s,
        which will be replaced by the group name.

    .. attribute:: error_message

        An error message containing the placeholder %s,
        which will be replaced by the error message.
    """
    name = forms.CharField(label=_("Name"),
                           max_length=255,
                           validators=[
                               utils_validators.validate_printable_ascii])
    description = forms.CharField(label=_("Description"),
                                  required=False,
                                  widget=forms.Textarea(attrs={'rows': 4}))

    def __init__(self, request, *args, **kwargs):
        super(GroupBase, self).__init__(request, *args, **kwargs)
        if not api.base.is_service_enabled(request, 'network'):
            self.fields['description'].required = True

    def _call_network_api(self, request, data):
        """Call the underlying network API: Nova-network or Neutron.

        Used in children classes to create or update a group.
        """
        raise NotImplementedError()

    def handle(self, request, data):
        try:
            sg = self._call_network_api(request, data)
            messages.success(request, self.success_message % sg.name)
            return sg
        except Exception as e:
            redirect = reverse("horizon:project:access_and_security:index")
            error_msg = self.error_message % e
            exceptions.handle(request, error_msg, redirect=redirect)


class CreateGroup(GroupBase):
    success_message = _('Successfully created security group: %s')
    error_message = _('Unable to create security group: %s')

    def _call_network_api(self, request, data):
        return api.network.security_group_create(request,
                                                 data['name'],
                                                 data['description'])


class UpdateGroup(GroupBase):
    success_message = _('Successfully updated security group: %s')
    error_message = _('Unable to update security group: %s')

    id = forms.CharField(widget=forms.HiddenInput())

    def _call_network_api(self, request, data):
        return api.network.security_group_update(request,
                                                 data['id'],
                                                 data['name'],
                                                 data['description'])


class AddRule(forms.SelfHandlingForm):
    id = forms.CharField(widget=forms.HiddenInput())
    rule_menu = forms.ChoiceField(label=_('Rule'),
                                  widget=forms.Select(attrs={
                                      'class': 'switchable',
                                      'data-slug': 'rule_menu'}))

    # "direction" field is enabled only when custom mode.
    # It is because most common rules in local_settings.py is meaningful
    # when its direction is 'ingress'.
    direction = forms.ChoiceField(
        label=_('Direction'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'rule_menu',
            'data-rule_menu-tcp': _('Direction'),
            'data-rule_menu-udp': _('Direction'),
            'data-rule_menu-icmp': _('Direction'),
            'data-rule_menu-custom': _('Direction'),
            'data-rule_menu-all_tcp': _('Direction'),
            'data-rule_menu-all_udp': _('Direction'),
            'data-rule_menu-all_icmp': _('Direction'),
        }))

    ip_protocol = forms.IntegerField(
        label=_('IP Protocol'), required=False,
        help_text=_("Enter an integer value between 0 and 255 "
                    "(or -1 which means wildcard)."),
        validators=[utils_validators.validate_ip_protocol],
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'rule_menu',
            'data-rule_menu-custom': _('IP Protocol')}))

    port_or_range = forms.ChoiceField(
        label=_('Open Port'),
        choices=[('port', _('Port')),
                 ('range', _('Port Range'))],
        widget=forms.Select(attrs={
            'class': 'switchable switched',
            'data-slug': 'range',
            'data-switch-on': 'rule_menu',
            'data-rule_menu-tcp': _('Open Port'),
            'data-rule_menu-udp': _('Open Port')}))

    port = forms.IntegerField(label=_("Port"),
                              required=False,
                              help_text=_("Enter an integer value "
                                          "between 1 and 65535."),
                              widget=forms.TextInput(attrs={
                                  'class': 'switched',
                                  'data-switch-on': 'range',
                                  'data-range-port': _('Port')}),
                              validators=[
                                  utils_validators.validate_port_range])

    from_port = forms.IntegerField(label=_("From Port"),
                                   required=False,
                                   help_text=_("Enter an integer value "
                                               "between 1 and 65535."),
                                   widget=forms.TextInput(attrs={
                                       'class': 'switched',
                                       'data-switch-on': 'range',
                                       'data-range-range': _('From Port')}),
                                   validators=[
                                       utils_validators.validate_port_range])

    to_port = forms.IntegerField(label=_("To Port"),
                                 required=False,
                                 help_text=_("Enter an integer value "
                                             "between 1 and 65535."),
                                 widget=forms.TextInput(attrs={
                                     'class': 'switched',
                                     'data-switch-on': 'range',
                                     'data-range-range': _('To Port')}),
                                 validators=[
                                     utils_validators.validate_port_range])

    icmp_type = forms.IntegerField(label=_("Type"),
                                   required=True,
                                   help_text=_("Enter a value for ICMP type "
                                               "in the range (-1: 255)"),
                                   widget=forms.TextInput(attrs={
                                       'class': 'switched',
                                       'data-switch-on': 'rule_menu',
                                       'data-rule_menu-icmp': _('Type')}),
                                   validators=[
                                       utils_validators.validate_port_range])

    icmp_code = forms.IntegerField(label=_("Code"),
                                   required=True,
                                   help_text=_("Enter a value for ICMP code "
                                               "in the range (-1: 255)"),
                                   widget=forms.TextInput(attrs={
                                       'class': 'switched',
                                       'data-switch-on': 'rule_menu',
                                       'data-rule_menu-icmp': _('Code')}),
                                   validators=[
                                       utils_validators.validate_port_range])

    remote = forms.ChoiceField(label=_('Remote'),
                               choices=[('cidr', _('CIDR')),
                                        ('sg', _('Security Group'))],
                               help_text=_('To specify an allowed IP '
                                           'range, select &quot;CIDR&quot;. '
                                           'To allow access from all '
                                           'members of another security '
                                           'group select &quot;Security '
                                           'Group&quot;.'),
                               widget=forms.Select(attrs={
                                   'class': 'switchable',
                                   'data-slug': 'remote'}))

    cidr = forms.IPField(label=_("CIDR"),
                         required=False,
                         initial="0.0.0.0/0",
                         help_text=_("Classless Inter-Domain Routing "
                                     "(e.g. 192.168.0.0/24, or "
                                     "2001:db8::/128)"),
                         version=forms.IPv4 | forms.IPv6,
                         mask=True,
                         widget=forms.TextInput(
                             attrs={'class': 'switched',
                                    'data-switch-on': 'remote',
                                    'data-remote-cidr': _('CIDR')}))

    security_group = forms.ChoiceField(label=_('Security Group'),
                                       required=False,
                                       widget=forms.Select(attrs={
                                           'class': 'switched',
                                           'data-switch-on': 'remote',
                                           'data-remote-sg': _('Security '
                                                               'Group')}))
    # When cidr is used ethertype is determined from IP version of cidr.
    # When source group, ethertype needs to be specified explicitly.
    ethertype = forms.ChoiceField(label=_('Ether Type'),
                                  required=False,
                                  choices=[('IPv4', _('IPv4')),
                                           ('IPv6', _('IPv6'))],
                                  widget=forms.Select(attrs={
                                      'class': 'switched',
                                      'data-slug': 'ethertype',
                                      'data-switch-on': 'remote',
                                      'data-remote-sg': _('Ether Type')}))

    def __init__(self, *args, **kwargs):
        sg_list = kwargs.pop('sg_list', [])
        super(AddRule, self).__init__(*args, **kwargs)
        # Determine if there are security groups available for the
        # remote group option; add the choices and enable the option if so.
        if sg_list:
            security_groups_choices = sg_list
        else:
            security_groups_choices = [("", _("No security groups available"))]
        self.fields['security_group'].choices = security_groups_choices

        backend = api.network.security_group_backend(self.request)

        rules_dict = getattr(settings, 'SECURITY_GROUP_RULES', [])
        common_rules = [(k, rules_dict[k]['name'])
                        for k in rules_dict
                        if rules_dict[k].get('backend', backend) == backend]
        common_rules.sort()
        custom_rules = [('tcp', _('Custom TCP Rule')),
                        ('udp', _('Custom UDP Rule')),
                        ('icmp', _('Custom ICMP Rule'))]
        if backend == 'neutron':
            custom_rules.append(('custom', _('Other Protocol')))
        self.fields['rule_menu'].choices = custom_rules + common_rules
        self.rules = rules_dict

        if backend == 'neutron':
            self.fields['direction'].choices = [('ingress', _('Ingress')),
                                                ('egress', _('Egress'))]
        else:
            # direction and ethertype are not supported in Nova secgroup.
            self.fields['direction'].widget = forms.HiddenInput()
            self.fields['ethertype'].widget = forms.HiddenInput()
            # ip_protocol field is to specify arbitrary protocol number
            # and it is available only for neutron security group.
            self.fields['ip_protocol'].widget = forms.HiddenInput()

    def _update_and_pop_error(self, cleaned_data, key, value):
        cleaned_data[key] = value
        self.errors.pop(key, None)

    def _clean_rule_icmp(self, cleaned_data, rule_menu):
        icmp_type = cleaned_data.get("icmp_type", None)
        icmp_code = cleaned_data.get("icmp_code", None)

        self._update_and_pop_error(cleaned_data, 'ip_protocol', rule_menu)
        if icmp_type is None:
            msg = _('The ICMP type is invalid.')
            raise ValidationError(msg)
        if icmp_code is None:
            msg = _('The ICMP code is invalid.')
            raise ValidationError(msg)
        if icmp_type not in range(-1, 256):
            msg = _('The ICMP type not in range (-1, 255)')
            raise ValidationError(msg)
        if icmp_code not in range(-1, 256):
            msg = _('The ICMP code not in range (-1, 255)')
            raise ValidationError(msg)
        self._update_and_pop_error(cleaned_data, 'from_port', icmp_type)
        self._update_and_pop_error(cleaned_data, 'to_port', icmp_code)
        self._update_and_pop_error(cleaned_data, 'port', None)

    def _clean_rule_tcp_udp(self, cleaned_data, rule_menu):
        port_or_range = cleaned_data.get("port_or_range")
        from_port = cleaned_data.get("from_port", None)
        to_port = cleaned_data.get("to_port", None)
        port = cleaned_data.get("port", None)

        self._update_and_pop_error(cleaned_data, 'ip_protocol', rule_menu)
        self._update_and_pop_error(cleaned_data, 'icmp_code', None)
        self._update_and_pop_error(cleaned_data, 'icmp_type', None)
        if port_or_range == "port":
            self._update_and_pop_error(cleaned_data, 'from_port', port)
            self._update_and_pop_error(cleaned_data, 'to_port', port)
            if port is None:
                msg = _('The specified port is invalid.')
                raise ValidationError(msg)
        else:
            self._update_and_pop_error(cleaned_data, 'port', None)
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

    def _clean_rule_custom(self, cleaned_data, rule_menu):
        # custom IP protocol rule so we need to fill unused fields so
        # the validation works
        self._update_and_pop_error(cleaned_data, 'icmp_code', None)
        self._update_and_pop_error(cleaned_data, 'icmp_type', None)

    def _apply_rule_menu(self, cleaned_data, rule_menu):
        cleaned_data['ip_protocol'] = self.rules[rule_menu]['ip_protocol']
        cleaned_data['from_port'] = int(self.rules[rule_menu]['from_port'])
        cleaned_data['to_port'] = int(self.rules[rule_menu]['to_port'])
        self._update_and_pop_error(cleaned_data, 'icmp_code', None)
        self._update_and_pop_error(cleaned_data, 'icmp_type', None)
        if rule_menu not in ['all_tcp', 'all_udp', 'all_icmp']:
            direction = self.rules[rule_menu].get('direction')
            cleaned_data['direction'] = direction

    def _clean_rule_menu(self, cleaned_data):
        rule_menu = cleaned_data.get('rule_menu')
        if rule_menu == 'icmp':
            self._clean_rule_icmp(cleaned_data, rule_menu)
        elif rule_menu == 'tcp' or rule_menu == 'udp':
            self._clean_rule_tcp_udp(cleaned_data, rule_menu)
        elif rule_menu == 'custom':
            self._clean_rule_custom(cleaned_data, rule_menu)
        else:
            self._apply_rule_menu(cleaned_data, rule_menu)

    def clean(self):
        cleaned_data = super(AddRule, self).clean()

        self._clean_rule_menu(cleaned_data)

        # NOTE(amotoki): There are two cases where cleaned_data['direction']
        # is empty: (1) Nova Security Group is used. Since "direction" is
        # HiddenInput, direction field exists but its value is ''.
        # (2) Template except all_* is used. In this case, the default value
        # is None. To make sure 'direction' field has 'ingress' or 'egress',
        # fill this field here if it is not specified.
        if not cleaned_data['direction']:
            cleaned_data['direction'] = 'ingress'

        remote = cleaned_data.get("remote")
        if remote == "cidr":
            self._update_and_pop_error(cleaned_data, 'security_group', None)
        else:
            self._update_and_pop_error(cleaned_data, 'cidr', None)

        # If cleaned_data does not contain a non-empty value, IPField already
        # has validated it, so skip the further validation for cidr.
        # In addition cleaned_data['cidr'] is None means source_group is used.
        if 'cidr' in cleaned_data and cleaned_data['cidr'] is not None:
            cidr = cleaned_data['cidr']
            if not cidr:
                msg = _('CIDR must be specified.')
                self._errors['cidr'] = self.error_class([msg])
            else:
                # If cidr is specified, ethertype is determined from IP address
                # version. It is used only when Neutron is enabled.
                ip_ver = netaddr.IPNetwork(cidr).version
                cleaned_data['ethertype'] = 'IPv6' if ip_ver == 6 else 'IPv4'

        return cleaned_data

    def handle(self, request, data):
        redirect = reverse("horizon:project:access_and_security:"
                           "security_groups:detail", args=[data['id']])
        try:
            rule = api.network.security_group_rule_create(
                request,
                filters.get_int_or_uuid(data['id']),
                data['direction'],
                data['ethertype'],
                data['ip_protocol'],
                data['from_port'],
                data['to_port'],
                data['cidr'],
                data['security_group'])
            messages.success(request,
                             _('Successfully added rule: %s')
                             % six.text_type(rule))
            return rule
        except exceptions.Conflict as error:
            exceptions.handle(request, error, redirect=redirect)
        except Exception:
            exceptions.handle(request,
                              _('Unable to add rule to security group.'),
                              redirect=redirect)
