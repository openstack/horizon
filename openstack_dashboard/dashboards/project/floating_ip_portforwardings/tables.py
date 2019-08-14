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

from django import shortcuts
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy

PROTOCOL_CHOICES = (
    ("Select a protocol", "Select a protocol"),
    ("UDP", "UDP"),
    ("TCP", "TCP"),
)


class CreateFloatingIpPortForwardingRule(tables.LinkAction):
    name = "create"
    verbose_name = _("Add floating IP port forwarding rule")
    classes = ("ajax-modal",)
    icon = "plus"
    url = "horizon:project:floating_ip_portforwardings:create"
    floating_ip_id = None

    def allowed(self, request, fip=None):
        policy_rules = (("network", "create_floatingip_port_forwarding"),)
        return policy.check(policy_rules, request)

    def single(self, data_table, request, *args):
        return shortcuts.redirect(
            'horizon:project:floating_ip_portforwardings:show')

    def get_url_params(self, datum=None):
        return urlencode({"floating_ip_id": self.floating_ip_id})

    def get_link_url(self, datum=None):
        base_url = reverse(self.url)
        join = "?".join([base_url, self.get_url_params(datum)])
        return join


class EditFloatingIpPortForwardingRule(CreateFloatingIpPortForwardingRule):
    name = "edit"
    verbose_name = _("Edit floating IP port forwarding rule")
    classes = ("ajax-modal", "btn-edit")
    url = "horizon:project:floating_ip_portforwardings:edit"

    def allowed(self, request, fip=None):
        policy_rules = (("network", "update_floatingip_port_forwarding"),)
        return policy.check(policy_rules, request)

    def get_url_params(self, datum=None):
        portforwading_id = self.table.get_object_id(datum)
        return urlencode({"floating_ip_id": self.floating_ip_id,
                          "pfwd_id": portforwading_id})


class EditFloatingIpPortForwardingRuleFromAllPanel(
        EditFloatingIpPortForwardingRule):
    name = "edit-from-all"
    url = "horizon:project:floating_ip_portforwardings:editToAll"

    def single(self, data_table, request, *args):
        return shortcuts.redirect(
            'horizon:project:floating_ip_portforwardings:index')

    def get_url_params(self, datum=None):
        portforwading_id = self.table.get_object_id(datum)
        return urlencode({"floating_ip_id": datum.floating_ip_id,
                          "pfwd_id": portforwading_id})


class DeleteRule(tables.DeleteAction):
    name = "delete"
    help_text = _(
        "This action will delete the "
        "selected floating IP port forwarding rule(s); "
        "this process cannot be undone.")
    floating_ip_id = None

    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            u"Delete Rule",
            u"Delete Rules",
            count
        )

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            u"Deleted Rule",
            u"Deleted Rules",
            count
        )

    def allowed(self, request, fip=None):
        policy_rules = (("network", "delete_floatingip_port_forwarding"),)
        return policy.check(policy_rules, request)

    def action(self, request, obj_id):
        api.neutron.floating_ip_port_forwarding_delete(request,
                                                       self.floating_ip_id,
                                                       obj_id)


class DeleteRuleFromAllPanel(DeleteRule):
    name = "delete-from-all"

    def action(self, request, obj_id):
        datum = self.table.get_object_by_id(obj_id)
        api.neutron.floating_ip_port_forwarding_delete(request,
                                                       datum.floating_ip_id,
                                                       obj_id)


class FloatingIpPortForwardingRulesTable(tables.DataTable):
    protocol = tables.Column("protocol", verbose_name=_("Protocol"))
    external_port_range = tables.Column("external_port_range",
                                        verbose_name=_("External port"))
    internal_port_range = tables.Column("internal_port_range",
                                        verbose_name=_("Internal port"))
    internal_ip_address = tables.Column("internal_ip_address",
                                        verbose_name=_("Internal IP address"))
    description = tables.Column("description", verbose_name=_("Description"))

    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super().__init__(
            request, data=data, needs_form_wrapper=needs_form_wrapper,
            **kwargs)

        floating_ip_id = request.GET.get('floating_ip_id')

        for action in self.get_table_actions():
            action.floating_ip_id = floating_ip_id

        for action in self._meta.row_actions:
            action.floating_ip_id = floating_ip_id

    def get_object_display(self, datum):
        return str(datum.internal_ip_address) + ':' + str(
            datum.internal_port_range)

    class Meta(object):
        name = "floating_ip_portforwardings"
        verbose_name = _("Floating IP port forwarding rules")
        table_actions = (CreateFloatingIpPortForwardingRule, DeleteRule)
        row_actions = (EditFloatingIpPortForwardingRule, DeleteRule)


class AllFloatingIpPortForwardingRulesTable(tables.DataTable):
    floating_ip_id = tables.Column("floating_ip_id",
                                   verbose_name=_("floating_ip_id"),
                                   hidden=True)
    protocol = tables.Column("protocol", verbose_name=_("Protocol"))
    external_port_range = tables.Column("external_port_range",
                                        verbose_name=_("External port"))
    internal_port_range = tables.Column("internal_port_range",
                                        verbose_name=_("Internal port"))
    external_ip_address = tables.Column("external_ip_address",
                                        verbose_name=_("External IP address"))
    internal_ip_address = tables.Column("internal_ip_address",
                                        verbose_name=_("Internal IP address"))
    description = tables.Column("description", verbose_name=_("Description"))

    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super().__init__(
            request, data=data, needs_form_wrapper=needs_form_wrapper, **kwargs)

    def get_object_display(self, datum):
        return str(datum.internal_ip_address) + ':' + str(
            datum.internal_port_range)

    class Meta(object):
        name = "floating_ip_portforwardings"
        verbose_name = _("Floating IP port forwarding rules")
        table_actions = (DeleteRuleFromAllPanel,)
        row_actions = (
            EditFloatingIpPortForwardingRuleFromAllPanel,
            DeleteRuleFromAllPanel)
