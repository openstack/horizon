#    Copyright 2013, Big Switch Networks, Inc.
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

from django.utils.translation import ugettext_lazy as _
import netaddr

from horizon import exceptions
from horizon import forms
from horizon.utils import validators
from horizon import workflows

from openstack_dashboard import api

port_validator = validators.validate_port_or_colon_separated_port_range


class AddRuleAction(workflows.Action):
    name = forms.CharField(
        max_length=80,
        label=_("Name"),
        required=False)
    description = forms.CharField(
        max_length=80,
        label=_("Description"),
        required=False)
    protocol = forms.ChoiceField(
        label=_("Protocol"),
        choices=[('tcp', _('TCP')),
                 ('udp', _('UDP')),
                 ('icmp', _('ICMP')),
                 ('any', _('ANY'))],)
    action = forms.ChoiceField(
        label=_("Action"),
        choices=[('allow', _('ALLOW')),
                 ('deny', _('DENY'))],)
    source_ip_address = forms.IPField(
        label=_("Source IP Address/Subnet"),
        version=forms.IPv4 | forms.IPv6,
        required=False, mask=True)
    destination_ip_address = forms.IPField(
        label=_("Destination IP Address/Subnet"),
        version=forms.IPv4 | forms.IPv6,
        required=False, mask=True)
    source_port = forms.CharField(
        max_length=80,
        label=_("Source Port/Port Range"),
        required=False,
        validators=[port_validator])
    destination_port = forms.CharField(
        max_length=80,
        label=_("Destination Port/Port Range"),
        required=False,
        validators=[port_validator])
    ip_version = forms.ChoiceField(
        label=_("IP Version"), required=False,
        choices=[('4', '4'), ('6', '6')])
    shared = forms.BooleanField(
        label=_("Shared"), initial=False, required=False)
    enabled = forms.BooleanField(
        label=_("Enabled"), initial=True, required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddRuleAction, self).__init__(request, *args, **kwargs)

    def _check_ip_addr_and_ip_version(self, cleaned_data):
        ip_version = int(str(cleaned_data.get('ip_version')))
        src_ip = cleaned_data.get('source_ip_address')
        dst_ip = cleaned_data.get('destination_ip_address')
        msg = _('Source/Destination Network Address and IP version '
                'are inconsistent. Please make them consistent.')
        if (src_ip and
                netaddr.IPNetwork(src_ip).version != ip_version):
                self._errors['ip_version'] = self.error_class([msg])

        elif (dst_ip and
              netaddr.IPNetwork(dst_ip).version != ip_version):
            self._errors['ip_version'] = self.error_class([msg])

    def clean(self):
        cleaned_data = super(AddRuleAction, self).clean()
        self._check_ip_addr_and_ip_version(cleaned_data)

    class Meta(object):
        name = _("Rule")
        permissions = ('openstack.services.network',)
        help_text = _("Create a firewall rule.\n\n"
                      "Protocol and action must be specified. "
                      "Other fields are optional.")


class AddRuleStep(workflows.Step):
    action_class = AddRuleAction
    contributes = ("name", "description", "protocol", "action",
                   "source_ip_address", "source_port",
                   "destination_ip_address", "destination_port",
                   "enabled", "shared", "ip_version")

    def contribute(self, data, context):
        context = super(AddRuleStep, self).contribute(data, context)
        if data:
            if context['protocol'] == 'any':
                del context['protocol']
            for field in ['source_port',
                          'destination_port',
                          'source_ip_address',
                          'destination_ip_address']:
                if not context[field]:
                    del context[field]
            return context


class AddRule(workflows.Workflow):
    slug = "addrule"
    name = _("Add Rule")
    finalize_button_name = _("Add")
    success_message = _('Added Rule "%s".')
    failure_message = _('Unable to add Rule "%s".')
    success_url = "horizon:project:firewalls:index"
    # fwaas is designed to support a wide range of vendor
    # firewalls. Considering the multitude of vendor firewall
    # features in place today, firewall_rule definition can
    # involve more complex configuration over time. Hence,
    # a workflow instead of a single form is used for
    # firewall_rule add to be ready for future extension.
    default_steps = (AddRuleStep,)

    def format_status_message(self, message):
        return message % self.context.get('name')

    def handle(self, request, context):
        try:
            api.fwaas.rule_create(request, **context)
            return True
        except Exception as e:
            msg = self.format_status_message(self.failure_message) + str(e)
            exceptions.handle(request, msg)
            return False


class SelectRulesAction(workflows.Action):
    rule = forms.MultipleChoiceField(
        label=_("Rules"),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text=_("Create a policy with selected rules."))

    class Meta(object):
        name = _("Rules")
        permissions = ('openstack.services.network',)
        help_text = _("Select rules for your policy.")

    def populate_rule_choices(self, request, context):
        try:
            tenant_id = self.request.user.tenant_id
            rules = api.fwaas.rule_list_for_tenant(request, tenant_id)
            rules = sorted(rules,
                           key=lambda rule: rule.name_or_id)
            rule_list = [(rule.id, rule.name_or_id) for rule in rules
                         if not rule.firewall_policy_id]
        except Exception as e:
            rule_list = []
            exceptions.handle(request,
                              _('Unable to retrieve rules (%(error)s).') % {
                                  'error': str(e)})
        return rule_list


class SelectRulesStep(workflows.Step):
    action_class = SelectRulesAction
    template_name = "project/firewalls/_update_rules.html"
    contributes = ("firewall_rules",)

    def contribute(self, data, context):
        if data:
            rules = self.workflow.request.POST.getlist("rule")
            if rules:
                rules = [r for r in rules if r != '']
                context['firewall_rules'] = rules
            return context


class SelectRoutersAction(workflows.Action):
    router = forms.MultipleChoiceField(
        label=_("Routers"),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text=_("Create a firewall with selected routers."))

    class Meta(object):
        name = _("Routers")
        permissions = ('openstack.services.network',)
        help_text = _("Select routers for your firewall.")

    def populate_router_choices(self, request, context):
        try:
            tenant_id = self.request.user.tenant_id
            routers_list = api.fwaas.firewall_unassociated_routers_list(
                request, tenant_id)

        except Exception as e:
            routers_list = []
            exceptions.handle(request,
                              _('Unable to retrieve routers (%(error)s).') % {
                                  'error': str(e)})
        routers_list = [(router.id, router.name_or_id)
                        for router in routers_list]
        return routers_list


class SelectRoutersStep(workflows.Step):
    action_class = SelectRoutersAction
    template_name = "project/firewalls/_update_routers.html"
    contributes = ("router_ids", "all_routers_selected",
                   "Select No Routers")

    def contribute(self, data, context):
        if data:
            routers = self.workflow.request.POST.getlist("router")
            if routers:
                routers = [r for r in routers if r != '']
                context['router_ids'] = routers
            else:
                context['router_ids'] = []
            return context


class AddPolicyAction(workflows.Action):
    name = forms.CharField(max_length=80,
                           label=_("Name"))
    description = forms.CharField(max_length=80,
                                  label=_("Description"),
                                  required=False)
    shared = forms.BooleanField(label=_("Shared"),
                                initial=False,
                                required=False)
    audited = forms.BooleanField(label=_("Audited"),
                                 initial=False,
                                 required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddPolicyAction, self).__init__(request, *args, **kwargs)

    class Meta(object):
        name = _("Policy")
        permissions = ('openstack.services.network',)
        help_text = _("Create a firewall policy with an ordered list "
                      "of firewall rules.\n\n"
                      "A name must be given. Firewall rules are "
                      "added in the order placed under the Rules tab.")


class AddPolicyStep(workflows.Step):
    action_class = AddPolicyAction
    contributes = ("name", "description", "shared", "audited")

    def contribute(self, data, context):
        context = super(AddPolicyStep, self).contribute(data, context)
        if data:
            return context


class AddPolicy(workflows.Workflow):
    slug = "addpolicy"
    name = _("Add Policy")
    finalize_button_name = _("Add")
    success_message = _('Added Policy "%s".')
    failure_message = _('Unable to add Policy "%s".')
    success_url = "horizon:project:firewalls:index"
    default_steps = (AddPolicyStep, SelectRulesStep)

    def format_status_message(self, message):
        return message % self.context.get('name')

    def handle(self, request, context):
        try:
            api.fwaas.policy_create(request, **context)
            return True
        except Exception as e:
            msg = self.format_status_message(self.failure_message) + str(e)
            exceptions.handle(request, msg)
            return False


class AddFirewallAction(workflows.Action):
    name = forms.CharField(max_length=80,
                           label=_("Name"),
                           required=False)
    description = forms.CharField(max_length=80,
                                  label=_("Description"),
                                  required=False)
    firewall_policy_id = forms.ChoiceField(label=_("Policy"))
    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    def __init__(self, request, *args, **kwargs):
        super(AddFirewallAction, self).__init__(request, *args, **kwargs)

        firewall_policy_id_choices = [('', _("Select a Policy"))]
        try:
            tenant_id = self.request.user.tenant_id
            policies = api.fwaas.policy_list_for_tenant(request, tenant_id)
            policies = sorted(policies, key=lambda policy: policy.name)
        except Exception as e:
            exceptions.handle(
                request,
                _('Unable to retrieve policy list (%(error)s).') % {
                    'error': str(e)})
            policies = []
        for p in policies:
            firewall_policy_id_choices.append((p.id, p.name_or_id))
        self.fields['firewall_policy_id'].choices = firewall_policy_id_choices

    class Meta(object):
        name = _("Firewall")
        permissions = ('openstack.services.network',)
        help_text = _("Create a firewall based on a policy.\n\n"
                      "A policy must be selected. "
                      "Other fields are optional.")


class AddFirewallStep(workflows.Step):
    action_class = AddFirewallAction
    contributes = ("name", "firewall_policy_id", "description",
                   "admin_state_up")

    def contribute(self, data, context):
        context = super(AddFirewallStep, self).contribute(data, context)
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        return context


class AddFirewall(workflows.Workflow):
    slug = "addfirewall"
    name = _("Add Firewall")
    finalize_button_name = _("Add")
    success_message = _('Added Firewall "%s".')
    failure_message = _('Unable to add Firewall "%s".')
    success_url = "horizon:project:firewalls:index"
    # fwaas is designed to support a wide range of vendor
    # firewalls. Considering the multitude of vendor firewall
    # features in place today, firewall definition can
    # involve more complex configuration over time. Hence,
    # a workflow instead of a single form is used for
    # firewall_rule add to be ready for future extension.
    default_steps = (AddFirewallStep, )

    def format_status_message(self, message):
        return message % self.context.get('name')

    def handle(self, request, context):
        try:
            api.fwaas.firewall_create(request, **context)
            return True
        except Exception as e:
            msg = self.format_status_message(self.failure_message) + str(e)
            exceptions.handle(request, msg)
            return False
