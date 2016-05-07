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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.firewalls \
    import forms as fw_forms
from openstack_dashboard.dashboards.project.firewalls \
    import tabs as fw_tabs
from openstack_dashboard.dashboards.project.firewalls \
    import workflows as fw_workflows

AddRouterToFirewall = fw_forms.AddRouterToFirewall
InsertRuleToPolicy = fw_forms.InsertRuleToPolicy
RemoveRouterFromFirewall = fw_forms.RemoveRouterFromFirewall
RemoveRuleFromPolicy = fw_forms.RemoveRuleFromPolicy
UpdateFirewall = fw_forms.UpdateFirewall
UpdatePolicy = fw_forms.UpdatePolicy
UpdateRule = fw_forms.UpdateRule

FirewallDetailsTabs = fw_tabs.FirewallDetailsTabs
FirewallTabs = fw_tabs.FirewallTabs
PolicyDetailsTabs = fw_tabs.PolicyDetailsTabs
RuleDetailsTabs = fw_tabs.RuleDetailsTabs

AddFirewall = fw_workflows.AddFirewall
AddPolicy = fw_workflows.AddPolicy
AddRule = fw_workflows.AddRule


class IndexView(tabs.TabbedTableView):
    tab_group_class = FirewallTabs
    template_name = 'project/firewalls/details_tabs.html'
    page_title = _("Firewalls")


class AddRuleView(workflows.WorkflowView):
    workflow_class = AddRule
    template_name = "project/firewalls/addrule.html"
    page_title = _("Add New Rule")


class AddPolicyView(workflows.WorkflowView):
    workflow_class = AddPolicy
    template_name = "project/firewalls/addpolicy.html"
    page_title = _("Add New Policy")


class AddFirewallView(workflows.WorkflowView):
    workflow_class = AddFirewall
    template_name = "project/firewalls/addfirewall.html"
    page_title = _("Add New Firewall")

    def get_workflow(self):
        if api.neutron.is_extension_supported(self.request,
                                              'fwaasrouterinsertion'):
            AddFirewall.register(fw_workflows.SelectRoutersStep)
        workflow = super(AddFirewallView, self).get_workflow()
        return workflow


class RuleDetailsView(tabs.TabView):
    tab_group_class = (RuleDetailsTabs)
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ rule.name|default:rule.id }}"
    failure_url = reverse_lazy('horizon:project:firewalls:index')

    def get_context_data(self, **kwargs):
        context = super(RuleDetailsView, self).get_context_data(**kwargs)
        rule = self.get_data()
        table = fw_tabs.RulesTable(self.request)
        breadcrumb = [
            (_("Rules"), reverse_lazy('horizon:project:firewalls:rules'))]
        context["custom_breadcrumb"] = breadcrumb
        context["rule"] = rule
        context["url"] = self.failure_url
        context["actions"] = table.render_row_actions(rule)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            rule_id = self.kwargs['rule_id']
            rule = api.fwaas.rule_get(self.request, rule_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve rule details.'),
                              redirect=self.failure_url)
        return rule

    def get_tabs(self, request, *args, **kwargs):
        rule = self.get_data()
        return self.tab_group_class(request, rule=rule, **kwargs)


class PolicyDetailsView(tabs.TabView):
    tab_group_class = (PolicyDetailsTabs)
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ policy.name|default:policy.id }}"
    failure_url = reverse_lazy('horizon:project:firewalls:index')

    def get_context_data(self, **kwargs):
        context = super(PolicyDetailsView, self).get_context_data(**kwargs)
        policy = self.get_data()
        table = fw_tabs.PoliciesTable(self.request)
        breadcrumb = [
            (_("Policies"),
             reverse_lazy('horizon:project:firewalls:policies'))]
        context["custom_breadcrumb"] = breadcrumb
        context["policy"] = policy
        context["url"] = self.failure_url
        context["actions"] = table.render_row_actions(policy)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            policy_id = self.kwargs['policy_id']
            policy = api.fwaas.policy_get(self.request, policy_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve policy details.'),
                              redirect=self.failure_url)
        return policy

    def get_tabs(self, request, *args, **kwargs):
        policy = self.get_data()
        return self.tab_group_class(request, policy=policy, **kwargs)


class FirewallDetailsView(tabs.TabView):
    tab_group_class = (FirewallDetailsTabs)
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ firewall.name|default:firewall.id }}"
    failure_url = reverse_lazy('horizon:project:firewalls:index')

    def get_context_data(self, **kwargs):
        context = super(FirewallDetailsView, self).get_context_data(**kwargs)
        firewall = self.get_data()
        routers = self.get_routers_data(firewall)
        table = fw_tabs.FirewallsTable(self.request)
        context["firewall"] = firewall
        context["routers"] = routers
        context["url"] = self.failure_url
        context["actions"] = table.render_row_actions(firewall)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            firewall_id = self.kwargs['firewall_id']
            firewall = api.fwaas.firewall_get(self.request, firewall_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve firewall details.'),
                              redirect=self.failure_url)
        return firewall

    @memoized.memoized_method
    def get_routers_data(self, firewall):
        routers = []
        try:
            if api.neutron.is_extension_supported(self.request,
                                                  'fwaasrouterinsertion'):
                tenant_id = self.request.user.tenant_id
                tenant_routers = api.neutron.router_list(self.request,
                                                         tenant_id=tenant_id)
                router_ids = firewall.get_dict()['router_ids']
                routers = [r for r in tenant_routers
                           if r['id'] in router_ids]
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve list of routers.'), )
        return routers

    def get_tabs(self, request, *args, **kwargs):
        firewall = self.get_data()
        return self.tab_group_class(request, firewall=firewall, **kwargs)


class UpdateRuleView(forms.ModalFormView):
    form_class = UpdateRule
    form_id = "update_rule_form"
    template_name = "project/firewalls/updaterule.html"
    context_object_name = 'rule'
    modal_header = _("Edit Rule")
    submit_label = _("Save Changes")
    submit_url = "horizon:project:firewalls:updaterule"
    success_url = reverse_lazy("horizon:project:firewalls:index")
    page_title = _("Edit Rule {{ name }}")

    def get_context_data(self, **kwargs):
        context = super(UpdateRuleView, self).get_context_data(**kwargs)
        context['rule_id'] = self.kwargs['rule_id']
        args = (self.kwargs['rule_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        obj = self._get_object()
        if obj:
            context['name'] = obj.name_or_id
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        rule_id = self.kwargs['rule_id']
        try:
            rule = api.fwaas.rule_get(self.request, rule_id)
            return rule
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve rule details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        rule = self._get_object()
        initial = rule.get_dict()
        protocol = initial['protocol']
        initial['protocol'] = protocol.upper() if protocol else 'ANY'
        initial['action'] = initial['action'].upper()
        return initial


class UpdatePolicyView(forms.ModalFormView):
    form_class = UpdatePolicy
    form_id = "update_policy_form"
    template_name = "project/firewalls/updatepolicy.html"
    context_object_name = 'policy'
    modal_header = _("Edit Policy")
    submit_label = _("Save Changes")
    submit_url = "horizon:project:firewalls:updatepolicy"
    success_url = reverse_lazy("horizon:project:firewalls:index")
    page_title = _("Edit Policy {{ name }}")

    def get_context_data(self, **kwargs):
        context = super(UpdatePolicyView, self).get_context_data(**kwargs)
        context["policy_id"] = self.kwargs['policy_id']
        args = (self.kwargs['policy_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        obj = self._get_object()
        if obj:
            context['name'] = obj.name_or_id
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        policy_id = self.kwargs['policy_id']
        try:
            policy = api.fwaas.policy_get(self.request, policy_id)
            return policy
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve policy details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        policy = self._get_object()
        initial = policy.get_dict()
        return initial


class UpdateFirewallView(forms.ModalFormView):
    form_class = UpdateFirewall
    form_id = "update_firewall_form"
    template_name = "project/firewalls/updatefirewall.html"
    context_object_name = 'firewall'
    modal_header = _("Edit Firewall")
    submit_label = _("Save Changes")
    submit_url = "horizon:project:firewalls:updatefirewall"
    success_url = reverse_lazy("horizon:project:firewalls:index")
    page_title = _("Edit Firewall {{ name }}")

    def get_context_data(self, **kwargs):
        context = super(UpdateFirewallView, self).get_context_data(**kwargs)
        context["firewall_id"] = self.kwargs['firewall_id']
        args = (self.kwargs['firewall_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        obj = self._get_object()
        if obj:
            context['name'] = obj.name
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        firewall_id = self.kwargs['firewall_id']
        try:
            firewall = api.fwaas.firewall_get(self.request,
                                              firewall_id)
            return firewall
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve firewall details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        firewall = self._get_object()
        initial = firewall.get_dict()
        return initial


class InsertRuleToPolicyView(forms.ModalFormView):
    form_class = InsertRuleToPolicy
    form_id = "update_policy_form"
    modal_header = _("Insert Rule into Policy")
    template_name = "project/firewalls/insert_rule_to_policy.html"
    context_object_name = 'policy'
    submit_url = "horizon:project:firewalls:insertrule"
    submit_label = _("Save Changes")
    success_url = reverse_lazy("horizon:project:firewalls:index")
    page_title = _("Insert Rule to Policy")

    def get_context_data(self, **kwargs):
        context = super(InsertRuleToPolicyView,
                        self).get_context_data(**kwargs)
        context["policy_id"] = self.kwargs['policy_id']
        args = (self.kwargs['policy_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        obj = self._get_object()
        if obj:
            context['name'] = obj.name_or_id
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        policy_id = self.kwargs['policy_id']
        try:
            policy = api.fwaas.policy_get(self.request, policy_id)
            return policy
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve policy details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        policy = self._get_object()
        initial = policy.get_dict()
        initial['policy_id'] = initial['id']
        return initial


class RemoveRuleFromPolicyView(forms.ModalFormView):
    form_class = RemoveRuleFromPolicy
    form_id = "update_policy_form"
    modal_header = _("Remove Rule from Policy")
    template_name = "project/firewalls/remove_rule_from_policy.html"
    context_object_name = 'policy'
    submit_label = _("Save Changes")
    submit_url = "horizon:project:firewalls:removerule"
    success_url = reverse_lazy("horizon:project:firewalls:index")
    page_title = _("Remove Rule from Policy")

    def get_context_data(self, **kwargs):
        context = super(RemoveRuleFromPolicyView,
                        self).get_context_data(**kwargs)
        context["policy_id"] = self.kwargs['policy_id']
        args = (self.kwargs['policy_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        obj = self._get_object()
        if obj:
            context['name'] = obj.name_or_id
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        policy_id = self.kwargs['policy_id']
        try:
            policy = api.fwaas.policy_get(self.request, policy_id)
            return policy
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve policy details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        policy = self._get_object()
        initial = policy.get_dict()
        initial['policy_id'] = initial['id']
        return initial


class RouterCommonView(forms.ModalFormView):
    form_id = "update_firewall_form"
    context_object_name = 'firewall'
    submit_label = _("Save Changes")
    success_url = reverse_lazy("horizon:project:firewalls:index")

    def get_context_data(self, **kwargs):
        context = super(RouterCommonView,
                        self).get_context_data(**kwargs)
        context["firewall_id"] = self.kwargs['firewall_id']
        args = (self.kwargs['firewall_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        obj = self._get_object()
        if obj:
            context['name'] = obj.name_or_id
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        firewall_id = self.kwargs['firewall_id']
        try:
            firewall = api.fwaas.firewall_get(self.request, firewall_id)
            return firewall
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve firewall details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        firewall = self._get_object()
        initial = firewall.get_dict()
        return initial


class AddRouterToFirewallView(RouterCommonView):
    form_class = AddRouterToFirewall
    modal_header = _("Add Router to Firewall")
    template_name = "project/firewalls/add_router_to_firewall.html"
    submit_url = "horizon:project:firewalls:addrouter"
    page_title = _("Add Router to Firewall")


class RemoveRouterFromFirewallView(RouterCommonView):
    form_class = RemoveRouterFromFirewall
    modal_header = _("Remove Router from Firewall")
    template_name = "project/firewalls/remove_router_from_firewall.html"
    submit_url = "horizon:project:firewalls:removerouter"
    page_title = _("Remove Router from Firewall")
