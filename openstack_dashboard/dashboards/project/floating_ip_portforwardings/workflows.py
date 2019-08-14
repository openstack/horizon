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

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from neutronclient.common import exceptions as neutron_exc

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.floating_ip_portforwardings import (
    tables as project_tables)

LOG = logging.getLogger(__name__)


class CommonMetaData(object):
    name = _("Description")
    help_text = _(
        "Description:"
        ""
        "IP floating rules define external specific traffic that is bound "
        "from a public IP to an internal address of a specific port.\n"
        "Protocol: The protocol configured for the IP forwarding rule. "
        "You can choose between TCP and UDP.\n"
        "External port: The external port of the floating IP that"
        " will be "
        "bound to the internal port in the internal address. This field"
        " allow values "
        "between 1 and 65535 and also support ranges using the following"
        " format:\n"
        "InitialPort:FinalPort where InitialPort <= FinalPort.\n"
        "Internal port: The internal port of the given internal IP "
        "address that will be bound to the port that is exposed to the "
        "internet via the public floating IP. This field allow values "
        "between 1 and 65535 and also support ranges using the following"
        " format:\n"
        "InitialPort:FinalPort where InitialPort <= FinalPort.\n"
        "Internal IP address: The internal IP address where the "
        "internal ports will be running.\n"
        "Description: Describes the reason why this rule is being "
        "created.")


class CreateFloatingIpPortForwardingRuleAction(workflows.Action):
    protocol = forms.ThemableChoiceField(
        required=True,
        choices=project_tables.PROTOCOL_CHOICES,
        label=_("Protocol"))
    external_port = forms.CharField(max_length=11, label=_("External port"))
    internal_port = forms.CharField(max_length=11, label=_("Internal port"))
    internal_ip_address = forms.ThemableChoiceField(required=True, label=_(
        "Internal IP address"))
    description = forms.CharField(required=False, widget=forms.Textarea,
                                  max_length=255, label=_("Description"))
    floating_ip_id = forms.CharField(max_length=255,
                                     widget=forms.HiddenInput())

    class Meta(CommonMetaData):
        pass

    def ignore_validation(self, portforward=None):
        return False

    def validate_input_selects(self):
        err_msg = "You must select a%s"
        internal_ip_address = self.cleaned_data.get('internal_ip_address')
        protocol = self.cleaned_data.get('protocol')

        if protocol == "Select a protocol":
            raise ValidationError(message=err_msg % " Protocol.")

        if internal_ip_address in ('Select an IP-Address',
                                   'No ports available'):
            raise ValidationError(message=err_msg % "n Ip-Address.")

    def clean(self):
        request = self.request
        if request.method == "GET":
            return self.cleaned_data

        self.validate_input_selects()

        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        floating_ip_id = self.request.GET.get('floating_ip_id')
        self.initial['floating_ip_id'] = floating_ip_id

    def populate_internal_ip_address_choices(self, request, context):
        targets = api.neutron.floating_ip_target_list(self.request)
        instances = sorted([(target.id, target.name) for target in targets],
                           key=lambda x: x[1])
        if instances:
            instances.insert(0, ("Select an IP-Address", _(
                "Select an IP-Address")))
        else:
            instances = (("No ports available", _(
                "No ports available")),)
        return instances


class EditFloatingIpPortForwardingRuleAction(
        CreateFloatingIpPortForwardingRuleAction):
    portforwading_id = forms.CharField(max_length=255,
                                       widget=forms.HiddenInput())
    instance_id = None

    class Meta(CommonMetaData):
        pass

    def ignore_validation(self, portforward=None):
        return (super().ignore_validation(portforward) or
                portforward.id == self.cleaned_data.get(
                    'portforwading_id'))

    def __init__(self, *args, **kwargs):
        request = args[0]
        if request.method == 'POST':
            super().__init__(
                *args, **kwargs)
        else:
            floating_ip_id = request.GET.get('floating_ip_id')
            port_forwarding_id = request.GET.get('pfwd_id')
            port_forwarding = api.neutron.floating_ip_port_forwarding_get(
                request, floating_ip_id, port_forwarding_id)
            port_forwarding_rule = port_forwarding['port_forwarding']
            self.instance_id = "%s_%s" % (
                port_forwarding_rule['internal_port_id'],
                port_forwarding_rule['internal_ip_address'])
            super().__init__(
                *args, **kwargs)
            self.initial['portforwading_id'] = port_forwarding_id
            self.initial['protocol'] = str(
                port_forwarding_rule['protocol']).upper()
            self.initial['internal_port'] = port_forwarding_rule[
                'internal_port_range']
            self.initial['external_port'] = port_forwarding_rule[
                'external_port_range']
            if 'description' in port_forwarding_rule.keys():
                self.initial['description'] = port_forwarding_rule[
                    'description']

    def populate_internal_ip_address_choices(self, request, context):
        targets = api.neutron.floating_ip_target_list(self.request)
        instances = sorted([(target.id, target.name) for target in targets],
                           key=lambda x: '0'
                           if x[0] == self.instance_id else x[1])
        return instances


class CreateFloatingIpPortForwardingRule(workflows.Step):
    action_class = CreateFloatingIpPortForwardingRuleAction
    contributes = ("internal_port", "protocol", "external_port",
                   "internal_ip_address", "description", "floating_ip_id",
                   "portforwading_id")

    def contribute(self, data, context):
        context = super().contribute(data, context)
        return context


class EditFloatingIpPortForwardingRule(
        CreateFloatingIpPortForwardingRule):
    action_class = EditFloatingIpPortForwardingRuleAction

    def contribute(self, data, context):
        context = super().contribute(data, context)
        return context


class FloatingIpPortForwardingRuleCreationWorkflow(workflows.Workflow):
    slug = "floating_ip_port_forwarding_rule_creation"
    name = _("Add floating IP port forwarding rule")
    finalize_button_name = _("Add")
    success_message = _('Floating IP port forwarding rule %s created. '
                        'It might take a few minutes to apply all rules.')
    failure_message = _('Unable to create floating IP port forwarding rule'
                        ' %s.')
    success_url = "horizon:project:floating_ip_portforwardings:show"
    default_steps = (CreateFloatingIpPortForwardingRule,)

    def format_status_message(self, message):
        if "%s" in message:
            return message % self.context.get('ip_address',
                                              _('unknown IP address'))
        return message

    def handle_using_api_method(self, request, data, api_method,
                                **api_params):
        try:
            floating_ip_id = data['floating_ip_id']
            self.success_url = reverse(
                self.success_url) + "?floating_ip_id=" + str(
                floating_ip_id)
            port_id, internal_ip = data['internal_ip_address'].split('_')
            self.context['ip_address'] = internal_ip
            param = {}
            if data['description']:
                param['description'] = data['description']
            if data['internal_port']:
                param['internal_port'] = data['internal_port']
            if data['external_port']:
                param['external_port'] = data['external_port']
            if internal_ip:
                param['internal_ip_address'] = internal_ip
            if data['protocol']:
                param['protocol'] = data['protocol']
            if port_id:
                param['internal_port_id'] = port_id

            param.update(**api_params)
            api_method(request, floating_ip_id, **param)

        except neutron_exc.Conflict as ex:
            msg = _('The requested instance port is already'
                    ' associated with another floating IP.')
            LOG.exception(msg, ex)
            exceptions.handle(request, msg)
            self.failure_message = msg
            return False

        except Exception:
            exceptions.handle(request)
            return False
        return True

    def handle(self, request, data):
        return self.handle_using_api_method(
            request, data, api.neutron.floating_ip_port_forwarding_create)


class FloatingIpPortForwardingRuleEditWorkflow(
        FloatingIpPortForwardingRuleCreationWorkflow):
    slug = "floating_ip_port_forwarding_rule_edit"
    name = _("Edit floating IP port forwarding rule")
    finalize_button_name = _("Update")
    success_message = _('Floating IP port forwarding rule %s updated. '
                        'It might take a few minutes to apply all rules.')
    failure_message = _('Unable to updated floating IP port forwarding'
                        ' rule %s.')
    success_url = "horizon:project:floating_ip_portforwardings:show"
    default_steps = (EditFloatingIpPortForwardingRule,)

    def handle(self, request, data):
        return self.handle_using_api_method(
            request, data, api.neutron.floating_ip_port_forwarding_update,
            portforwarding_id=data['portforwading_id'])


class FloatingIpPortForwardingRuleEditWorkflowToAll(
        FloatingIpPortForwardingRuleEditWorkflow):
    slug = "floating_ip_port_forwarding_rule_edit_all"
    success_url = "horizon:project:floating_ip_portforwardings:index"
