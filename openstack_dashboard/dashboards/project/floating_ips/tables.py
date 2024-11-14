# Copyright 2012 Nebula, Inc.
# Copyright (c) 2012 X.commerce, a business unit of eBay Inc.
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

from django import shortcuts
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from django.utils.translation import pgettext_lazy

from horizon import exceptions
from horizon import messages
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy
from openstack_dashboard.usage import quotas
from openstack_dashboard.utils import filters


LOG = logging.getLogger(__name__)


class AllocateIP(tables.LinkAction):
    name = "allocate"
    verbose_name = _("Allocate IP To Project")
    classes = ("ajax-modal",)
    icon = "link"
    url = "horizon:project:floating_ips:allocate"

    def single(self, data_table, request, *args):
        return shortcuts.redirect('horizon:project:floating_ips:index')

    def allowed(self, request, fip=None):
        usages = quotas.tenant_quota_usages(request,
                                            targets=('floatingip', ))
        if 'floatingip' in usages and usages['floatingip']['available'] <= 0:
            if "disabled" not in self.classes:
                self.classes = list(self.classes) + ['disabled']
                self.verbose_name = format_lazy(
                    '{verbose_name} {quota_exceeded}',
                    verbose_name=self.verbose_name,
                    quota_exceeded=_("(Quota exceeded)"))
        else:
            self.verbose_name = _("Allocate IP To Project")
            classes = [c for c in self.classes if c != "disabled"]
            self.classes = classes

        policy_rules = (("network", "create_floatingip"),)
        return policy.check(policy_rules, request)


class ReleaseIPs(tables.BatchAction):
    name = "release"
    action_type = "danger"
    icon = "unlink"
    help_text = _("Once a floating IP is released, there is"
                  " no guarantee the same IP can be allocated again.")

    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            "Release Floating IP",
            "Release Floating IPs",
            count
        )

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            "Released Floating IP",
            "Released Floating IPs",
            count
        )

    def allowed(self, request, fip=None):
        policy_rules = (("network", "delete_floatingip"),)

        port_forwarding_occurrence = 0

        if fip:
            pwds = fip.port_forwardings
            port_forwarding_occurrence = len(pwds)

        return port_forwarding_occurrence == 0 and policy.check(policy_rules,
                                                                request)

    def action(self, request, obj_id):
        api.neutron.tenant_floating_ip_release(request, obj_id)


class ReleaseIPsPortForwarding(ReleaseIPs):
    name = "release_floating_ip_portforwarding_rule"
    help_text = _(
        "This floating IP has port forwarding rules configured to it."
        " Therefore,"
        " you will need to remove all of these rules before being able"
        " to release it.")

    def __init__(self, **kwargs):
        attributes = {"title": "Release Floating IP with port forwarding rules",
                      "confirm-button-text": "Edit floating IP port"
                                             " forwarding rules"}
        super().__init__(attrs=attributes, **kwargs)

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            u"Successfully redirected",
            u"Successfully redirected",
            count
        )

    def allowed(self, request, fip=None):

        policy_rules = (("network", "delete_floatingip_port_forwarding"),)
        pwds = fip.port_forwardings
        return (
            len(pwds) > 0 and
            policy.check(policy_rules, request) and
            api.neutron.is_extension_floating_ip_port_forwarding_supported(
                request)
        )

    def action(self, request, obj_id):
        self.success_url = reverse(
            'horizon:project:floating_ip_portforwardings:show') \
            + '?floating_ip_id=' \
            + str(obj_id)


class AssociateIP(tables.LinkAction):
    name = "associate"
    verbose_name = _("Associate")
    url = "horizon:project:floating_ips:associate"
    classes = ("ajax-modal",)
    icon = "link"

    def allowed(self, request, fip):
        policy_rules = (("network", "update_floatingip"),)
        pwds = fip.port_forwardings
        return len(pwds) == 0 and not fip.port_id and policy.check(policy_rules,
                                                                   request)

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"ip_id": self.table.get_object_id(datum)})
        return "?".join([base_url, params])


class ListAllFloatingIpPortForwardingRules(tables.LinkAction):
    name = "List floating_ip_portforwardings_rules"
    verbose_name = _("List all floating IP port forwarding rules")
    url = "horizon:project:floating_ip_portforwardings:index"
    classes = ("btn-edit",)
    icon = "link"

    def exists_floating_ip_with_port_forwarding_rules_configurable(self,
                                                                   request):
        floating_ips = api.neutron.tenant_floating_ip_list(request)
        for floating_ip in floating_ips:
            if not floating_ip.port_id:
                return True

        return False

    def allowed(self, request, fip):
        policy_rules = (("network", "get_floatingip_port_forwarding"),)
        return (self.exists_floating_ip_with_port_forwarding_rules_configurable(
                request) and policy.check(policy_rules, request) and
                api.neutron.is_extension_floating_ip_port_forwarding_supported(
                    request))


class ConfigureFloatingIpPortForwarding(tables.Action):
    name = "configure_floating_ip_portforwarding_rules"
    verbose_name = _("Configure floating IP port forwarding rules")
    classes = ("btn-edit",)
    icon = "link"

    def allowed(self, request, fip):
        policy_rules = (("network", "get_floatingip_port_forwarding"),)
        return (
            not fip.port_id and
            policy.check(policy_rules, request) and
            api.neutron.is_extension_floating_ip_port_forwarding_supported(
                request)
        )

    def single(self, table, request, obj_id):
        fip = {}
        try:
            fip = table.get_object_by_id(filters.get_int_or_uuid(obj_id))
        except Exception as ex:
            err_msg = 'Unable to find a floating IP.'
            LOG.debug(err_msg, ex)
            exceptions.handle(request,
                              _('Unable to find a floating IP.'))
        return shortcuts.redirect(
            reverse('horizon:project:floating_ip_portforwardings:show') +
            '?floating_ip_id=' + str(fip.id))


class DisassociateIP(tables.Action):
    name = "disassociate"
    verbose_name = _("Disassociate")
    classes = ("btn-disassociate",)
    icon = "unlink"
    action_type = "danger"

    def allowed(self, request, fip):
        policy_rules = (("network", "update_floatingip"),)
        return fip.port_id and policy.check(policy_rules, request)

    def single(self, table, request, obj_id):
        try:
            fip = table.get_object_by_id(filters.get_int_or_uuid(obj_id))
            api.neutron.floating_ip_disassociate(request, fip.id)
            LOG.info('Disassociating Floating IP "%s".', obj_id)
            messages.success(request,
                             _('Successfully disassociated Floating IP: %s')
                             % fip.ip)
        except Exception:
            exceptions.handle(request,
                              _('Unable to disassociate floating IP.'))
        return shortcuts.redirect('horizon:project:floating_ips:index')


def get_instance_info(fip):
    if fip.instance_type == 'compute':
        return (_("%(instance_name)s %(fixed_ip)s")
                % {'instance_name': getattr(fip, "instance_name", ''),
                   'fixed_ip': fip.fixed_ip})
    if fip.instance_type == 'loadbalancer':
        return _("Load Balancer VIP %s") % fip.fixed_ip
    return getattr(fip, 'fixed_ip', None)


def get_instance_link(datum):
    if getattr(datum, 'instance_id'):
        return reverse("horizon:project:instances:detail",
                       args=(datum.instance_id,))
    return None


STATUS_DISPLAY_CHOICES = (
    ("active", pgettext_lazy("Current status of a Floating IP", "Active")),
    ("down", pgettext_lazy("Current status of a Floating IP", "Down")),
    ("error", pgettext_lazy("Current status of a Floating IP", "Error")),
)

FLOATING_IPS_FILTER_CHOICES = (
    ('floating_ip_address', _('Floating IP Address ='), True),
    ('network_id', _('Network ID ='), True),
    ('router_id', _('Router ID ='), True),
    ('port_id', _('Port ID ='), True),
    ('status', _('Status ='), True, _("e.g. ACTIVE / DOWN / ERROR")),
)


class FloatingIPsFilterAction(tables.FilterAction):
    filter_type = "server"
    filter_choices = FLOATING_IPS_FILTER_CHOICES


class FloatingIPsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("active", True),
        ("down", True),
        ("error", False)
    )
    ip = tables.Column("ip",
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
    description = tables.Column("description",
                                verbose_name=_("Description"))
    dns_name = tables.Column("dns_name",
                             verbose_name=_("DNS Name"))
    dns_domain = tables.Column("dns_domain",
                               verbose_name=_("DNS Domain"))
    fixed_ip = tables.Column(get_instance_info,
                             link=get_instance_link,
                             verbose_name=_("Mapped Fixed IP Address"))
    pool = tables.Column("pool_name",
                         verbose_name=_("Pool"))
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)

    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super().__init__(request, data=data,
                         needs_form_wrapper=needs_form_wrapper,
                         **kwargs)
        dns_supported = api.neutron.is_extension_supported(
            request,
            "dns-integration")
        if not dns_supported:
            del self.columns["dns_name"]
            del self.columns["dns_domain"]

    def sanitize_id(self, obj_id):
        return filters.get_int_or_uuid(obj_id)

    def get_object_display(self, datum):
        return datum.ip

    class Meta(object):
        name = "floating_ips"
        verbose_name = _("Floating IPs")
        table_actions = (
            ListAllFloatingIpPortForwardingRules, AllocateIP, ReleaseIPs,
            FloatingIPsFilterAction)
        row_actions = (AssociateIP, DisassociateIP, ReleaseIPs,
                       ReleaseIPsPortForwarding,
                       ConfigureFloatingIpPortForwarding)
