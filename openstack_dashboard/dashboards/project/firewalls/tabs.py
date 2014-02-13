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
#
# @author: KC Wang, Big Switch Networks

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.firewalls import tables

FirewallsTable = tables.FirewallsTable
PoliciesTable = tables.PoliciesTable
RulesTable = tables.RulesTable


class RulesTab(tabs.TableTab):
    table_classes = (RulesTable,)
    name = _("Firewall Rules")
    slug = "rules"
    template_name = "horizon/common/_detail_table.html"

    def get_rulestable_data(self):
        try:
            tenant_id = self.request.user.tenant_id
            rules = api.fwaas.rule_list(self.tab_group.request,
                                        tenant_id=tenant_id)
        except Exception:
            rules = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve rules list.'))
        for r in rules:
            r.set_id_as_name_if_empty()

        return rules


class PoliciesTab(tabs.TableTab):
    table_classes = (PoliciesTable,)
    name = _("Firewall Policies")
    slug = "policies"
    template_name = "horizon/common/_detail_table.html"

    def get_policiestable_data(self):
        try:
            tenant_id = self.request.user.tenant_id
            policies = api.fwaas.policy_list(self.tab_group.request,
                                             tenant_id=tenant_id)
        except Exception:
            policies = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve policies list.'))
        for p in policies:
            p.set_id_as_name_if_empty()

        return policies


class FirewallsTab(tabs.TableTab):
    table_classes = (FirewallsTable,)
    name = _("Firewalls")
    slug = "firewalls"
    template_name = "horizon/common/_detail_table.html"

    def get_firewallstable_data(self):
        try:
            tenant_id = self.request.user.tenant_id
            firewalls = api.fwaas.firewall_list(self.tab_group.request,
                                                tenant_id=tenant_id)
        except Exception:
            firewalls = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve firewall list.'))

        for f in firewalls:
            f.set_id_as_name_if_empty()

        return firewalls


class RuleDetailsTab(tabs.Tab):
    name = _("Firewall Rule Details")
    slug = "ruledetails"
    template_name = "project/firewalls/_rule_details.html"
    failure_url = reverse_lazy('horizon:project:firewalls:index')

    def get_context_data(self, request):
        rid = self.tab_group.kwargs['rule_id']
        try:
            rule = api.fwaas.rule_get(request, rid)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve rule details.'),
                              redirect=self.failure_url)
        return {'rule': rule}


class PolicyDetailsTab(tabs.Tab):
    name = _("Firewall Policy Details")
    slug = "policydetails"
    template_name = "project/firewalls/_policy_details.html"
    failure_url = reverse_lazy('horizon:project:firewalls:index')

    def get_context_data(self, request):
        pid = self.tab_group.kwargs['policy_id']
        try:
            policy = api.fwaas.policy_get(request, pid)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve policy details.'),
                              redirect=self.failure_url)
        return {'policy': policy}


class FirewallDetailsTab(tabs.Tab):
    name = _("Firewall Details")
    slug = "firewalldetails"
    template_name = "project/firewalls/_firewall_details.html"
    failure_url = reverse_lazy('horizon:project:firewalls:index')

    def get_context_data(self, request):
        fid = self.tab_group.kwargs['firewall_id']
        try:
            firewall = api.fwaas.firewall_get(request, fid)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve firewall details.'),
                              redirect=self.failure_url)
        return {'firewall': firewall}


class FirewallTabs(tabs.TabGroup):
    slug = "fwtabs"
    tabs = (FirewallsTab, PoliciesTab, RulesTab)
    sticky = True


class RuleDetailsTabs(tabs.TabGroup):
    slug = "ruletabs"
    tabs = (RuleDetailsTab,)


class PolicyDetailsTabs(tabs.TabGroup):
    slug = "policytabs"
    tabs = (PolicyDetailsTab,)


class FirewallDetailsTabs(tabs.TabGroup):
    slug = "firewalltabs"
    tabs = (FirewallDetailsTab,)
