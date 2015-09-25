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

import logging

from django.core.urlresolvers import reverse
from django.template import defaultfilters as filters
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables
from openstack_dashboard import api
from openstack_dashboard import policy

LOG = logging.getLogger(__name__)


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
    icon = "plus"
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
    policy_rules = (("network", "delete_firewall_rule"),)

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

    def allowed(self, request, datum=None):
        if datum and datum.policy:
            return False
        return True

    def delete(self, request, obj_id):
        try:
            api.fwaas.rule_delete(request, obj_id)
        except Exception as e:
            exceptions.handle(request, _('Unable to delete rule. %s') % e)


class DeletePolicyLink(policy.PolicyTargetMixin, tables.DeleteAction):
    name = "deletepolicy"
    policy_rules = (("network", "delete_firewall_policy"),)

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

    def delete(self, request, obj_id):
        try:
            api.fwaas.policy_delete(request, obj_id)
        except Exception as e:
            exceptions.handle(request, _('Unable to delete policy. %s') % e)


class DeleteFirewallLink(policy.PolicyTargetMixin,
                         tables.DeleteAction):
    name = "deletefirewall"
    policy_rules = (("network", "delete_firewall"),)

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

    def delete(self, request, obj_id):
        try:
            api.fwaas.firewall_delete(request, obj_id)
        except Exception as e:
            exceptions.handle(request, _('Unable to delete firewall. %s') % e)


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

    def allowed(self, request, firewall):
        if firewall.status in ("PENDING_CREATE",
                               "PENDING_UPDATE",
                               "PENDING_DELETE"):
            return False
        return True


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

    def allowed(self, request, policy):
        if len(policy.rules) > 0:
            return True
        return False


class AddRouterToFirewallLink(policy.PolicyTargetMixin,
                              tables.LinkAction):
    name = "addrouter"
    verbose_name = _("Add Router")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "get_firewall"),
                    ("network", "add_router"),)

    def get_link_url(self, firewall):
        base_url = reverse("horizon:project:firewalls:addrouter",
                           kwargs={'firewall_id': firewall.id})
        return base_url

    def allowed(self, request, firewall):
        if not api.neutron.is_extension_supported(request,
                                                  'fwaasrouterinsertion'):
            return False
        tenant_id = firewall['tenant_id']
        available_routers = api.fwaas.firewall_unassociated_routers_list(
            request, tenant_id)
        return bool(available_routers)


class RemoveRouterFromFirewallLink(policy.PolicyTargetMixin,
                                   tables.LinkAction):
    name = "removerouter"
    verbose_name = _("Remove Router")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "get_firewall"),
                    ("network", "remove_router"),)

    def get_link_url(self, firewall):
        base_url = reverse("horizon:project:firewalls:removerouter",
                           kwargs={'firewall_id': firewall.id})
        return base_url

    def allowed(self, request, firewall):
        if not api.neutron.is_extension_supported(request,
                                                  'fwaasrouterinsertion'):
            return False
        return bool(firewall['router_ids'])


def get_rules_name(datum):
    return ', '.join([rule.name or rule.id[:13]
                      for rule in datum.rules])


def get_routers_name(firewall):
    if firewall.routers:
        return ', '.join(router.name_or_id for router in firewall.routers)


def get_policy_name(datum):
    if datum.policy:
        return datum.policy.name or datum.policy.id


def get_policy_link(datum):
    if datum.policy:
        return reverse('horizon:project:firewalls:policydetails',
                       kwargs={'policy_id': datum.policy.id})


class RulesTable(tables.DataTable):
    ACTION_DISPLAY_CHOICES = (
        ("Allow", pgettext_lazy("Action Name of a Firewall Rule", u"ALLOW")),
        ("Deny", pgettext_lazy("Action Name of a Firewall Rule", u"DENY")),
    )
    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link="horizon:project:firewalls:ruledetails")
    description = tables.Column('description', verbose_name=_('Description'))
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
                           display_choices=ACTION_DISPLAY_CHOICES,
                           verbose_name=_("Action"))
    shared = tables.Column("shared",
                           verbose_name=_("Shared"),
                           filters=(filters.yesno, filters.capfirst))
    enabled = tables.Column("enabled",
                            verbose_name=_("Enabled"),
                            filters=(filters.yesno, filters.capfirst))
    firewall_policy_id = tables.Column(get_policy_name,
                                       link=get_policy_link,
                                       verbose_name=_("In Policy"))

    class Meta(object):
        name = "rulestable"
        verbose_name = _("Rules")
        table_actions = (AddRuleLink, DeleteRuleLink)
        row_actions = (UpdateRuleLink, DeleteRuleLink)


class PoliciesTable(tables.DataTable):
    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link="horizon:project:firewalls:policydetails")
    description = tables.Column('description', verbose_name=_('Description'))
    firewall_rules = tables.Column(get_rules_name,
                                   verbose_name=_("Rules"))
    shared = tables.Column("shared",
                           verbose_name=_("Shared"),
                           filters=(filters.yesno, filters.capfirst))
    audited = tables.Column("audited",
                            verbose_name=_("Audited"),
                            filters=(filters.yesno, filters.capfirst))

    class Meta(object):
        name = "policiestable"
        verbose_name = _("Policies")
        table_actions = (AddPolicyLink, DeletePolicyLink)
        row_actions = (UpdatePolicyLink, InsertRuleToPolicyLink,
                       RemoveRuleFromPolicyLink, DeletePolicyLink)


class FirewallsTable(tables.DataTable):
    STATUS_DISPLAY_CHOICES = (
        ("Active", pgettext_lazy("Current status of a Firewall",
                                 u"Active")),
        ("Down", pgettext_lazy("Current status of a Firewall",
                               u"Down")),
        ("Error", pgettext_lazy("Current status of a Firewall",
                                u"Error")),
        ("Created", pgettext_lazy("Current status of a Firewall",
                                  u"Created")),
        ("Pending_Create", pgettext_lazy("Current status of a Firewall",
                                         u"Pending Create")),
        ("Pending_Update", pgettext_lazy("Current status of a Firewall",
                                         u"Pending Update")),
        ("Pending_Delete", pgettext_lazy("Current status of a Firewall",
                                         u"Pending Delete")),
        ("Inactive", pgettext_lazy("Current status of a Firewall",
                                   u"Inactive")),
    )
    ADMIN_STATE_DISPLAY_CHOICES = (
        ("UP", pgettext_lazy("Admin state of a Firewall", u"UP")),
        ("DOWN", pgettext_lazy("Admin state of a Firewall", u"DOWN")),
    )

    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link="horizon:project:firewalls:firewalldetails")
    description = tables.Column('description', verbose_name=_('Description'))
    firewall_policy_id = tables.Column(get_policy_name,
                                       link=get_policy_link,
                                       verbose_name=_("Policy"))
    router_ids = tables.Column(get_routers_name,
                               verbose_name=_("Associated Routers"))
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           display_choices=STATUS_DISPLAY_CHOICES)
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"),
                                display_choices=ADMIN_STATE_DISPLAY_CHOICES)

    class Meta(object):
        name = "firewallstable"
        verbose_name = _("Firewalls")
        table_actions = (AddFirewallLink, DeleteFirewallLink)
        row_actions = (UpdateFirewallLink, DeleteFirewallLink,
                       AddRouterToFirewallLink, RemoveRouterFromFirewallLink)

    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super(FirewallsTable, self).__init__(
            request, data=data,
            needs_form_wrapper=needs_form_wrapper, **kwargs)
        try:
            if not api.neutron.is_extension_supported(request,
                                                      'fwaasrouterinsertion'):
                del self.columns['router_ids']
        except Exception as e:
            msg = _('Failed to verify extension support %(reason)s') % {
                'reason': e}
            LOG.error(msg)
            exceptions.handle(request, msg)
