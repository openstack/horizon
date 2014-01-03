# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.core import urlresolvers
from django import shortcuts
from django.utils.http import urlencode
from django.utils.translation import string_concat  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.usage import quotas
from openstack_dashboard.utils import filters


LOG = logging.getLogger(__name__)


class AllocateIP(tables.LinkAction):
    name = "allocate"
    verbose_name = _("Allocate IP To Project")
    classes = ("ajax-modal", "btn-allocate")
    url = "horizon:project:access_and_security:floating_ips:allocate"

    def single(self, data_table, request, *args):
        return shortcuts.redirect('horizon:project:access_and_security:index')

    def allowed(self, request, volume=None):
        usages = quotas.tenant_quota_usages(request)
        if usages['floating_ips']['available'] <= 0:
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = string_concat(self.verbose_name, ' ',
                                                  _("(Quota exceeded)"))
        else:
            self.verbose_name = _("Allocate IP To Project")
            classes = [c for c in self.classes if c != "disabled"]
            self.classes = classes
        return True


class ReleaseIPs(tables.BatchAction):
    name = "release"
    action_present = _("Release")
    action_past = _("Released")
    data_type_singular = _("Floating IP")
    data_type_plural = _("Floating IPs")
    classes = ('btn-danger', 'btn-release')

    def action(self, request, obj_id):
        api.network.tenant_floating_ip_release(request, obj_id)


class AssociateIP(tables.LinkAction):
    name = "associate"
    verbose_name = _("Associate")
    url = "horizon:project:access_and_security:floating_ips:associate"
    classes = ("ajax-modal", "btn-associate")

    def allowed(self, request, fip):
        if fip.port_id:
            return False
        return True

    def get_link_url(self, datum):
        base_url = urlresolvers.reverse(self.url)
        params = urlencode({"ip_id": self.table.get_object_id(datum)})
        return "?".join([base_url, params])


class DisassociateIP(tables.Action):
    name = "disassociate"
    verbose_name = _("Disassociate")
    classes = ("btn-disassociate", "btn-danger")

    def allowed(self, request, fip):
        if fip.port_id:
            return True
        return False

    def single(self, table, request, obj_id):
        try:
            fip = table.get_object_by_id(filters.get_int_or_uuid(obj_id))
            api.network.floating_ip_disassociate(request, fip.id,
                                                 fip.port_id)
            LOG.info('Disassociating Floating IP "%s".' % obj_id)
            messages.success(request,
                             _('Successfully disassociated Floating IP: %s')
                             % fip.ip)
        except Exception:
            exceptions.handle(request,
                              _('Unable to disassociate floating IP.'))
        return shortcuts.redirect('horizon:project:access_and_security:index')


def get_instance_info(instance):
    return getattr(instance, "instance_name", None)


def get_instance_link(datum):
    view = "horizon:project:instances:detail"
    if datum.instance_id:
        return urlresolvers.reverse(view, args=(datum.instance_id,))
    else:
        return None


class FloatingIPsTable(tables.DataTable):
    ip = tables.Column("ip",
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
    instance = tables.Column(get_instance_info,
                             link=get_instance_link,
                             verbose_name=_("Instance"),
                             empty_value="-")
    pool = tables.Column("pool_name",
                         verbose_name=_("Floating IP Pool"),
                         empty_value="-")

    def sanitize_id(self, obj_id):
        return filters.get_int_or_uuid(obj_id)

    def get_object_display(self, datum):
        return datum.ip

    class Meta:
        name = "floating_ips"
        verbose_name = _("Floating IPs")
        table_actions = (AllocateIP, ReleaseIPs)
        row_actions = (AssociateIP, DisassociateIP, ReleaseIPs)
