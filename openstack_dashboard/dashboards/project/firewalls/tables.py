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

from django.core.urlresolvers import reverse
from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from openstack_dashboard import policy


class AddRuleLink(tables.LinkAction):
    name = "addrule"
    verbose_name = _("Add Rule")
    url = "horizon:project:firewalls:addrule"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_firewall_rule"),)


class AddPolicyLink(tables.LinkAction):
    name = "addpolicy"
    verbose_name = _("Add Policy")
    url = "horizon:project:firewalls:addpolicy"
    classes = ("ajax-modal", "btn-addpolicy",)
    policy_rules = (("network", "create_firewall_policy"),)


class AddFirewallLink(tables.LinkAction):
    name = "addfirewall"
    verbose_name = _("Create Firewall")
    url = "horizon:project:firewalls:addfirewall"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_firewall"),)


class DeleteRuleLink(policy.PolicyTargetMixin, tables.DeleteAction):
    name = "deleterule"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Rule",
            u"Delete Rules",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Rule",
            u"Scheduled deletion of Rules",
            count
        )

    policy_rules = (("network", "delete_firewall_rule"),)


class DeletePolicyLink(policy.PolicyTargetMixin, tables.DeleteAction):
    name = "deletepolicy"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Policy",
            u"Delete Policies",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Policy",
            u"Scheduled deletion of Policies",
            count
        )

    policy_rules = (("network", "delete_firewall_policy"),)


class DeleteFirewallLink(policy.PolicyTargetMixin,
                         tables.DeleteAction):
    name = "deletefirewall"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Firewall",
            u"Delete Firewalls",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Firewall",
            u"Scheduled deletion of Firewalls",
            count
        )

    policy_rules = (("network", "delete_firewall"),)


class UpdateRuleLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updaterule"
    verbose_name = _("Edit Rule")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_firewall_rule"),)

    def get_link_url(self, rule):
        base_url = reverse("horizon:project:firewalls:updaterule",
                           kwargs={'rule_id': rule.id})
        return base_url


class UpdatePolicyLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updatepolicy"
    verbose_name = _("Edit Policy")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_firewall_policy"),)

    def get_link_url(self, policy):
        base_url = reverse("horizon:project:firewalls:updatepolicy",
                           kwargs={'policy_id': policy.id})
        return base_url


class UpdateFirewallLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updatefirewall"
    verbose_name = _("Edit Firewall")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_firewall"),)

    def get_link_url(self, firewall):
        base_url = reverse("horizon:project:firewalls:updatefirewall",
                           kwargs={'firewall_id': firewall.id})
        return base_url


class InsertRuleToPolicyLink(policy.PolicyTargetMixin,
                             tables.LinkAction):
    name = "insertrule"
    verbose_name = _("Insert Rule")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "get_firewall_policy"),
        ("network", "insert_rule"),)

    def get_link_url(self, policy):
        base_url = reverse("horizon:project:firewalls:insertrule",
                           kwargs={'policy_id': policy.id})
        return base_url


class RemoveRuleFromPolicyLink(policy.PolicyTargetMixin,
                               tables.LinkAction):
    name = "removerule"
    verbose_name = _("Remove Rule")
    classes = ("ajax-modal", "btn-danger",)
    policy_rules = (("network", "get_firewall_policy"),
        ("network", "remove_rule"),)

    def get_link_url(self, policy):
        base_url = reverse("horizon:project:firewalls:removerule",
                           kwargs={'policy_id': policy.id})
        return base_url


def get_rules_name(datum):
    return ', '.join([rule.name or rule.id[:13]
                      for rule in datum.rules])


def get_policy_name(datum):
    if datum.policy:
        return datum.policy.name or datum.policy.id


def get_policy_link(datum):
    return reverse('horizon:project:firewalls:policydetails',
                   kwargs={'policy_id': datum.policy.id})


class RulesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:firewalls:ruledetails")
    protocol = tables.Column("protocol",
                             filters=(lambda v: filters.default(v, _("ANY")),
                                      filters.upper,),
                             verbose_name=_("Protocol"))
    source_ip_address = tables.Column("source_ip_address",
                                      verbose_name=_("Source IP"))
    source_port = tables.Column("source_port",
                                verbose_name=_("Source Port"))
    destination_ip_address = tables.Column("destination_ip_address",
                                           verbose_name=_("Destination IP"))
    destination_port = tables.Column("destination_port",
                                     verbose_name=_("Destination Port"))
    action = tables.Column("action",
                           filters=(filters.upper,),
                           verbose_name=_("Action"))
    enabled = tables.Column("enabled",
                           verbose_name=_("Enabled"))
    firewall_policy_id = tables.Column(get_policy_name,
                                       link=get_policy_link,
                                       verbose_name=_("In Policy"))

    class Meta:
        name = "rulestable"
        verbose_name = _("Rules")
        table_actions = (AddRuleLink, DeleteRuleLink)
        row_actions = (UpdateRuleLink, DeleteRuleLink)


class PoliciesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:firewalls:policydetails")
    firewall_rules = tables.Column(get_rules_name,
                                   verbose_name=_("Rules"))
    audited = tables.Column("audited",
                            verbose_name=_("Audited"))

    class Meta:
        name = "policiestable"
        verbose_name = _("Policies")
        table_actions = (AddPolicyLink, DeletePolicyLink)
        row_actions = (UpdatePolicyLink, InsertRuleToPolicyLink,
                       RemoveRuleFromPolicyLink, DeletePolicyLink)


class FirewallsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:firewalls:firewalldetails")
    firewall_policy_id = tables.Column(get_policy_name,
                                       link=get_policy_link,
                                       verbose_name=_("Policy"))
    status = tables.Column("status",
                           verbose_name=_("Status"))

    class Meta:
        name = "firewallstable"
        verbose_name = _("Firewalls")
        table_actions = (AddFirewallLink, DeleteFirewallLink)
        row_actions = (UpdateFirewallLink, DeleteFirewallLink)
