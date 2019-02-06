# Copyright 2013 NEC Corporation
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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks import workflows \
    as network_workflows


LOG = logging.getLogger(__name__)


class CreateSubnetInfoAction(network_workflows.CreateSubnetInfoAction):
    with_subnet = forms.BooleanField(initial=True, required=False,
                                     widget=forms.HiddenInput())
    cidr = forms.IPField(label=_("Network Address"),
                         initial="",
                         error_messages={
                             'required': _("Specify network address")},
                         widget=forms.TextInput(attrs={
                             'class': 'switched',
                             'data-switch-on': 'source',
                             'data-source-manual': _("Network Address"),
                         }),
                         help_text=_("Network address in CIDR format "
                                     "(e.g. 192.168.0.0/24, 2001:DB8::/48)"),
                         version=forms.IPv4 | forms.IPv6,
                         mask=True)

    class Meta(object):
        name = _("Subnet")
        help_text = _('Create a subnet associated with the network. '
                      'Advanced configuration is available by clicking on the '
                      '"Subnet Details" tab.')

    def clean(self):
        cleaned_data = workflows.Action.clean(self)
        self._check_subnet_data(cleaned_data)
        return cleaned_data


class CreateSubnetInfo(network_workflows.CreateSubnetInfo):
    action_class = CreateSubnetInfoAction
    depends_on = ("network",)


class CreateSubnet(network_workflows.CreateNetwork):
    slug = "create_subnet"
    name = _("Create Subnet")
    finalize_button_name = _("Create")
    success_message = _('Created subnet "%s".')
    failure_message = _('Unable to create subnet "%s".')
    default_steps = (CreateSubnetInfo,
                     network_workflows.CreateSubnetDetail)

    def format_status_message(self, message):
        name = self.context.get('subnet_name') or self.context.get('subnet_id')
        return message % name

    def get_success_url(self):
        return reverse("horizon:project:networks:detail",
                       args=(self.context['network'].id,))

    def get_failure_url(self):
        return reverse("horizon:project:networks:detail",
                       args=(self.context['network'].id,))

    def handle(self, request, data):
        network = self.context_seed['network']
        # network argument is required to show error message correctly.
        subnet = self._create_subnet(request, data, network=network)
        return bool(subnet)


class UpdateSubnetInfoAction(CreateSubnetInfoAction):
    address_source = forms.ThemableChoiceField(widget=forms.HiddenInput(),
                                               required=False)
    subnetpool = forms.ThemableChoiceField(widget=forms.HiddenInput(),
                                           required=False)
    prefixlen = forms.ThemableChoiceField(widget=forms.HiddenInput(),
                                          required=False)
    cidr = forms.IPField(label=_("Network Address"),
                         required=False,
                         initial="",
                         widget=forms.TextInput(
                             attrs={'readonly': 'readonly'}),
                         help_text=_("Network address in CIDR format "
                                     "(e.g. 192.168.0.0/24)"),
                         version=forms.IPv4 | forms.IPv6,
                         mask=True)
    # NOTE(amotoki): When 'disabled' attribute is set for the ChoiceField
    # and ValidationError is raised for POST request, the initial value of
    # the ip_version ChoiceField is not set in the re-displayed form
    # As a result, 'IPv4' is displayed even when IPv6 is used if
    # ValidationError is detected. In addition 'required=True' check complains
    # when re-POST since the value of the ChoiceField is not set.
    # Thus now I use HiddenInput for the ip_version ChoiceField as a work
    # around.
    ip_version = forms.ThemableChoiceField(choices=[(4, 'IPv4'), (6, 'IPv6')],
                                           widget=forms.HiddenInput(),
                                           label=_("IP Version"))
    gateway_ip = forms.IPField(
        label=_("Gateway IP"),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'gateway_ip',
            'data-source-manual': _("Gateway IP")
        }),
        initial="",
        error_messages={
            'required': _('Specify IP address of gateway or '
                          'check "Disable Gateway" checkbox.')
        },
        help_text=_("IP address of Gateway (e.g. 192.168.0.254) "
                    "If you do not want to use a gateway, "
                    "check 'Disable Gateway' below."),
        version=forms.IPv4 | forms.IPv6,
        mask=False)

    class Meta(object):
        name = _("Subnet")
        help_text = _('Update a subnet associated with the network. '
                      'Advanced configuration are available at '
                      '"Subnet Details" tab.')

    def clean(self):
        cleaned_data = workflows.Action.clean(self)
        self._check_subnet_data(cleaned_data)
        return cleaned_data


class UpdateSubnetInfo(CreateSubnetInfo):
    action_class = UpdateSubnetInfoAction
    depends_on = ("network_id", "subnet_id")


class UpdateSubnetDetailAction(network_workflows.CreateSubnetDetailAction):

    def __init__(self, request, context, *args, **kwargs):
        super(UpdateSubnetDetailAction, self).__init__(request, context,
                                                       *args, **kwargs)
        # TODO(amotoki): Due to Neutron bug 1362966, we cannot pass "None"
        # to Neutron. It means we cannot set IPv6 two modes to
        # "No option selected".
        # Until bug 1362966 is fixed, we disable this field.
        # if context['ip_version'] != 6:
        #     self.fields['ipv6_modes'].widget = forms.HiddenInput()
        #     self.fields['ipv6_modes'].required = False
        self.fields['ipv6_modes'].widget = forms.HiddenInput()
        self.fields['ipv6_modes'].required = False

    class Meta(object):
        name = _("Subnet Details")
        help_text = _('Specify additional attributes for the subnet.')


class UpdateSubnetDetail(network_workflows.CreateSubnetDetail):
    action_class = UpdateSubnetDetailAction


class UpdateSubnet(network_workflows.CreateNetwork):
    slug = "update_subnet"
    name = _("Edit Subnet")
    finalize_button_name = _("Save")
    success_message = _('Updated subnet "%s".')
    failure_message = _('Unable to update subnet "%s".')
    success_url = "horizon:project:networks:detail"
    failure_url = "horizon:project:networks:detail"
    default_steps = (UpdateSubnetInfo,
                     UpdateSubnetDetail)

    def format_status_message(self, message):
        name = self.context.get('subnet_name') or self.context.get('subnet_id')
        return message % name

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.context.get('network_id'),))

    def _update_subnet(self, request, data):
        network_id = self.context.get('network_id')
        try:
            subnet_id = self.context.get('subnet_id')
            params = {}
            params['name'] = data['subnet_name']
            if data['no_gateway']:
                params['gateway_ip'] = None
            elif data['gateway_ip']:
                params['gateway_ip'] = data['gateway_ip']

            # We should send gateway_ip only when it is changed, because
            # updating gateway_ip is prohibited when the ip is used.
            # See bug 1227268.
            subnet = api.neutron.subnet_get(request, subnet_id)
            if params['gateway_ip'] == subnet.gateway_ip:
                del params['gateway_ip']

            self._setup_subnet_parameters(params, data, is_create=False)

            subnet = api.neutron.subnet_update(request, subnet_id, **params)
            LOG.debug('Subnet "%s" was successfully updated.', data['cidr'])
            return subnet
        except Exception as e:
            msg = (_('Failed to update subnet "%(sub)s": '
                     ' %(reason)s') %
                   {"sub": data['cidr'], "reason": e})
            redirect = reverse(self.failure_url, args=(network_id,))
            exceptions.handle(request, msg, redirect=redirect)
            return False

    def handle(self, request, data):
        subnet = self._update_subnet(request, data)
        return bool(subnet)
