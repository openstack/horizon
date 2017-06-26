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

from django.core.urlresolvers import reverse
from django import shortcuts
from django.utils.http import urlencode
from django.utils.translation import pgettext_lazy
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

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
                                            targets=('floating_ips', ))
        if usages['floating_ips']['available'] <= 0:
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = string_concat(self.verbose_name, ' ',
                                                  _("(Quota exceeded)"))
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
        return ungettext_lazy(
            u"Release Floating IP",
            u"Release Floating IPs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Released Floating IP",
            u"Released Floating IPs",
            count
        )

    def allowed(self, request, fip=None):
        policy_rules = (("network", "delete_floatingip"),)
        return policy.check(policy_rules, request)

    def action(self, request, obj_id):
        api.neutron.tenant_floating_ip_release(request, obj_id)


class AssociateIP(tables.LinkAction):
    name = "associate"
    verbose_name = _("Associate")
    url = "horizon:project:floating_ips:associate"
    classes = ("ajax-modal",)
    icon = "link"

    def allowed(self, request, fip):
        policy_rules = (("network", "update_floatingip"),)
        return not fip.port_id and policy.check(policy_rules, request)

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"ip_id": self.table.get_object_id(datum)})
        return "?".join([base_url, params])


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
    elif fip.instance_type == 'loadbalancer':
        return _("Load Balancer VIP %s") % fip.fixed_ip
    elif fip.instance_type:
        return fip.fixed_ip
    else:
        return None


def get_instance_link(datum):
    if getattr(datum, 'instance_id'):
        return reverse("horizon:project:instances:detail",
                       args=(datum.instance_id,))
    else:
        return None


STATUS_DISPLAY_CHOICES = (
    ("active", pgettext_lazy("Current status of a Floating IP", u"Active")),
    ("down", pgettext_lazy("Current status of a Floating IP", u"Down")),
    ("error", pgettext_lazy("Current status of a Floating IP", u"Error")),
)


class FloatingIPsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("active", True),
        ("down", True),
        ("error", False)
    )
    ip = tables.Column("ip",
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
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
        super(FloatingIPsTable, self).__init__(
            request, data=data, needs_form_wrapper=needs_form_wrapper,
            **kwargs)

    def sanitize_id(self, obj_id):
        return filters.get_int_or_uuid(obj_id)

    def get_object_display(self, datum):
        return datum.ip

    class Meta(object):
        name = "floating_ips"
        verbose_name = _("Floating IPs")
        table_actions = (AllocateIP, ReleaseIPs)
        row_actions = (AssociateIP, DisassociateIP, ReleaseIPs)
