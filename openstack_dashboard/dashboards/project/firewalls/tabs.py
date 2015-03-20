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
            request = self.tab_group.request
            rules = api.fwaas.rule_list_for_tenant(request, tenant_id)
        except Exception:
            rules = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve rules list.'))

        return rules


class PoliciesTab(tabs.TableTab):
    table_classes = (PoliciesTable,)
    name = _("Firewall Policies")
    slug = "policies"
    template_name = "horizon/common/_detail_table.html"

    def get_policiestable_data(self):
        try:
            tenant_id = self.request.user.tenant_id
            request = self.tab_group.request
            policies = api.fwaas.policy_list_for_tenant(request, tenant_id)
        except Exception:
            policies = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve policies list.'))

        return policies


class FirewallsTab(tabs.TableTab):
    table_classes = (FirewallsTable,)
    name = _("Firewalls")
    slug = "firewalls"
    template_name = "horizon/common/_detail_table.html"

    def get_firewallstable_data(self):
        try:
            tenant_id = self.request.user.tenant_id
            request = self.tab_group.request
            firewalls = api.fwaas.firewall_list_for_tenant(request, tenant_id)

            if api.neutron.is_extension_supported(request,
                                                  'fwaasrouterinsertion'):
                routers = api.neutron.router_list(request, tenant_id=tenant_id)

                for fw in firewalls:
                    router_list = [r for r in routers
                                   if r['id'] in fw['router_ids']]
                    fw.get_dict()['routers'] = router_list

        except Exception:
            firewalls = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve firewall list.'))

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
            body = {'firewall': firewall}
            if api.neutron.is_extension_supported(request,
                                                  'fwaasrouterinsertion'):
                tenant_id = self.request.user.tenant_id
                tenant_routers = api.neutron.router_list(request,
                                                         tenant_id=tenant_id)
                router_ids = firewall.get_dict()['router_ids']
                routers = [r for r in tenant_routers
                           if r['id'] in router_ids]
                body['routers'] = routers
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve firewall details.'),
                              redirect=self.failure_url)
        return body


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
