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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy
from openstack_dashboard.usage import quotas
from openstack_dashboard.utils import filters


POLICY_CHECK = getattr(settings, "POLICY_CHECK_FUNCTION",
                       lambda policy, request, target: True)


class DeleteGroup(policy.PolicyTargetMixin, tables.DeleteAction):

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Security Group",
            u"Delete Security Groups",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Security Group",
            u"Deleted Security Groups",
            count
        )

    def allowed(self, request, security_group=None):
        policy_target = self.get_policy_target(request, security_group)
        if api.base.is_service_enabled(request, "network"):
            policy = (("network", "delete_security_group"),)
        else:
            policy = (("compute", "compute_extension:security_groups"),)

        if not POLICY_CHECK(policy, request, policy_target):
            return False

        if not security_group:
            return True
        return security_group.name != 'default'

    def delete(self, request, obj_id):
        api.network.security_group_delete(request, obj_id)


class CreateGroup(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Security Group")
    url = "horizon:project:access_and_security:security_groups:create"
    classes = ("ajax-modal",)
    icon = "plus"

    def allowed(self, request, security_group=None):
        if api.base.is_service_enabled(request, "network"):
            policy = (("network", "create_security_group"),)
        else:
            policy = (("compute", "compute_extension:security_groups"),)

        usages = quotas.tenant_quota_usages(request)
        if usages['security_groups'].get('available', 1) <= 0:
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ["disabled"]
                self.verbose_name = _("Create Security Group (Quota exceeded)")
        else:
            self.verbose_name = _("Create Security Group")
            self.classes = [c for c in self.classes if c != "disabled"]

        return POLICY_CHECK(policy, request, target={})


class EditGroup(policy.PolicyTargetMixin, tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Security Group")
    url = "horizon:project:access_and_security:security_groups:update"
    classes = ("ajax-modal",)
    icon = "pencil"

    def allowed(self, request, security_group=None):
        policy_target = self.get_policy_target(request, security_group)
        if api.base.is_service_enabled(request, "network"):
            policy = (("network", "update_security_group"),)
        else:
            policy = (("compute", "compute_extension:security_groups"),)

        if not POLICY_CHECK(policy, request, policy_target):
            return False

        if not security_group:
            return True
        return security_group.name != 'default'


class ManageRules(policy.PolicyTargetMixin, tables.LinkAction):
    name = "manage_rules"
    verbose_name = _("Manage Rules")
    url = "horizon:project:access_and_security:security_groups:detail"
    icon = "pencil"

    def allowed(self, request, security_group=None):
        policy_target = self.get_policy_target(request, security_group)
        if api.base.is_service_enabled(request, "network"):
            policy = (("network", "get_security_group"),)
        else:
            policy = (("compute", "compute_extension:security_groups"),)

        return POLICY_CHECK(policy, request, policy_target)


class SecurityGroupsFilterAction(tables.FilterAction):

    def filter(self, table, security_groups, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [security_group for security_group in security_groups
                if query in security_group.name.lower()]


class SecurityGroupsTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Name"))
    description = tables.Column("description", verbose_name=_("Description"))

    def sanitize_id(self, obj_id):
        return filters.get_int_or_uuid(obj_id)

    class Meta(object):
        name = "security_groups"
        verbose_name = _("Security Groups")
        table_actions = (CreateGroup, DeleteGroup, SecurityGroupsFilterAction)
        row_actions = (ManageRules, EditGroup, DeleteGroup)


class CreateRule(tables.LinkAction):
    name = "add_rule"
    verbose_name = _("Add Rule")
    url = "horizon:project:access_and_security:security_groups:add_rule"
    classes = ("ajax-modal",)
    icon = "plus"

    def allowed(self, request, security_group_rule=None):
        if api.base.is_service_enabled(request, "network"):
            policy = (("network", "create_security_group_rule"),)
        else:
            policy = (("compute", "compute_extension:security_groups"),)

        return POLICY_CHECK(policy, request, target={})

    def get_link_url(self):
        return reverse(self.url, args=[self.table.kwargs['security_group_id']])


class DeleteRule(tables.DeleteAction):
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
            u"Deleted Rule",
            u"Deleted Rules",
            count
        )

    def allowed(self, request, security_group_rule=None):
        if api.base.is_service_enabled(request, "network"):
            policy = (("network", "delete_security_group_rule"),)
        else:
            policy = (("compute", "compute_extension:security_groups"),)

        return POLICY_CHECK(policy, request, target={})

    def delete(self, request, obj_id):
        api.network.security_group_rule_delete(request, obj_id)

    def get_success_url(self, request):
        sg_id = self.table.kwargs['security_group_id']
        return reverse("horizon:project:access_and_security:"
                       "security_groups:detail", args=[sg_id])


def get_remote_ip_prefix(rule):
    if 'cidr' in rule.ip_range:
        if rule.ip_range['cidr'] is None:
            range = '::/0' if rule.ethertype == 'IPv6' else '0.0.0.0/0'
        else:
            range = rule.ip_range['cidr']
        return range
    else:
        return None


def get_remote_security_group(rule):
    return rule.group.get('name')


def get_port_range(rule):
    # There is no case where from_port is None and to_port has a value,
    # so it is enough to check only from_port.
    if rule.from_port is None:
        return _('Any')
    ip_proto = rule.ip_protocol
    if rule.from_port == rule.to_port:
        return check_rule_template(rule.from_port, ip_proto)
    else:
        return (u"%(from)s - %(to)s" %
                {'from': check_rule_template(rule.from_port, ip_proto),
                 'to': check_rule_template(rule.to_port, ip_proto)})


def filter_direction(direction):
    if direction is None or direction.lower() == 'ingress':
        return _('Ingress')
    else:
        return _('Egress')


def filter_protocol(protocol):
    if protocol is None:
        return _('Any')
    return unicode.upper(protocol)


def check_rule_template(port, ip_proto):
    rules_dict = getattr(settings, 'SECURITY_GROUP_RULES', {})
    if not rules_dict:
        return port
    templ_rule = filter(lambda rule: str(port) == rule['from_port']
                        and str(port) == rule['to_port']
                        and ip_proto == rule['ip_protocol'],
                        [rule for rule in rules_dict.values()])
    if templ_rule:
        return u"%(from_port)s (%(name)s)" % templ_rule[0]
    return port


class RulesTable(tables.DataTable):
    direction = tables.Column("direction",
                              verbose_name=_("Direction"),
                              filters=(filter_direction,))
    ethertype = tables.Column("ethertype",
                              verbose_name=_("Ether Type"))
    protocol = tables.Column("ip_protocol",
                             verbose_name=_("IP Protocol"),
                             filters=(filter_protocol,))
    port_range = tables.Column(get_port_range,
                               verbose_name=_("Port Range"))
    remote_ip_prefix = tables.Column(get_remote_ip_prefix,
                                     verbose_name=_("Remote IP Prefix"))
    remote_security_group = tables.Column(get_remote_security_group,
                                          verbose_name=_("Remote Security"
                                                         " Group"))

    def sanitize_id(self, obj_id):
        return filters.get_int_or_uuid(obj_id)

    def get_object_display(self, rule):
        return unicode(rule)

    class Meta(object):
        name = "rules"
        verbose_name = _("Security Group Rules")
        table_actions = (CreateRule, DeleteRule)
        row_actions = (DeleteRule,)
