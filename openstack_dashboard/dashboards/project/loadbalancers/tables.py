# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.utils import http
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from horizon import tables
from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class AddPoolLink(tables.LinkAction):
    name = "addpool"
    verbose_name = _("Add Pool")
    url = "horizon:project:loadbalancers:addpool"
    classes = ("btn-addpool",)


class AddVipLink(tables.LinkAction):
    name = "addvip"
    verbose_name = _("Add Vip")
    classes = ("btn-addvip",)

    def get_link_url(self, pool):
        base_url = reverse("horizon:project:loadbalancers:addvip",
                           kwargs={'pool_id': pool.id})
        return base_url

    def allowed(self, request, datum=None):
        if datum and datum.vip_id:
            return False
        return True


class AddMemberLink(tables.LinkAction):
    name = "addmember"
    verbose_name = _("Add Member")
    url = "horizon:project:loadbalancers:addmember"
    classes = ("btn-addmember",)


class AddMonitorLink(tables.LinkAction):
    name = "addmonitor"
    verbose_name = _("Add Monitor")
    url = "horizon:project:loadbalancers:addmonitor"
    classes = ("btn-addmonitor",)


class DeleteVipLink(tables.DeleteAction):
    name = "deletevip"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of")
    data_type_singular = _("Vip")
    data_type_plural = _("Vips")

    def allowed(self, request, datum=None):
        if datum and not datum.vip_id:
            return False
        return True


class DeletePoolLink(tables.DeleteAction):
    name = "deletepool"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of")
    data_type_singular = _("Pool")
    data_type_plural = _("Pools")


class DeleteMonitorLink(tables.DeleteAction):
    name = "deletemonitor"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of")
    data_type_singular = _("Monitor")
    data_type_plural = _("Monitors")


class DeleteMemberLink(tables.DeleteAction):
    name = "deletemember"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of")
    data_type_singular = _("Member")
    data_type_plural = _("Members")


def get_vip_link(pool):
    return reverse("horizon:project:loadbalancers:vipdetails",
                   args=(http.urlquote(pool.vip_id),))


class PoolsTable(tables.DataTable):
    name = tables.Column("name",
                       verbose_name=_("Name"),
                       link="horizon:project:loadbalancers:pooldetails")
    description = tables.Column('description', verbose_name=_("Description"))
    subnet_name = tables.Column('subnet_name', verbose_name=_("Subnet"))
    protocol = tables.Column('protocol', verbose_name=_("Protocol"))
    vip_name = tables.Column('vip_name', verbose_name=_("VIP"),
                             link=get_vip_link)

    class Meta:
        name = "poolstable"
        verbose_name = _("Pools")
        table_actions = (AddPoolLink, DeletePoolLink)
        row_actions = (AddVipLink, DeleteVipLink, DeletePoolLink)


def get_pool_link(member):
    return reverse("horizon:project:loadbalancers:pooldetails",
                   args=(http.urlquote(member.pool_id),))


def get_member_link(member):
    return reverse("horizon:project:loadbalancers:memberdetails",
                   args=(http.urlquote(member.id),))


class MembersTable(tables.DataTable):
    address = tables.Column('address',
                            verbose_name=_("IP Address"),
                            link=get_member_link)
    protocol_port = tables.Column('protocol_port',
                                  verbose_name=_("Protocol Port"))
    pool_name = tables.Column("pool_name",
                            verbose_name=_("Pool"), link=get_pool_link)

    class Meta:
        name = "memberstable"
        verbose_name = _("Members")
        table_actions = (AddMemberLink, DeleteMemberLink)
        row_actions = (DeleteMemberLink,)


class MonitorsTable(tables.DataTable):
    id = tables.Column("id",
                       verbose_name=_("ID"),
                       link="horizon:project:loadbalancers:monitordetails")
    monitorType = tables.Column('type', verbose_name=_("Monitor Type"))

    class Meta:
        name = "monitorstable"
        verbose_name = _("Monitors")
        table_actions = (AddMonitorLink, DeleteMonitorLink)
        row_actions = (DeleteMonitorLink,)
