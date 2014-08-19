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


from django.core.urlresolvers import reverse
from django.template import defaultfilters as filters
from django.utils import http
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy


class AddPoolLink(tables.LinkAction):
    name = "addpool"
    verbose_name = _("Add Pool")
    url = "horizon:project:loadbalancers:addpool"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_pool"),)


class AddVipLink(tables.LinkAction):
    name = "addvip"
    verbose_name = _("Add VIP")
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_vip"),)

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
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_member"),)


class AddMonitorLink(tables.LinkAction):
    name = "addmonitor"
    verbose_name = _("Add Monitor")
    url = "horizon:project:loadbalancers:addmonitor"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_health_monitor"),)


class DeleteVipLink(policy.PolicyTargetMixin, tables.DeleteAction):
    name = "deletevip"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of %(data_type)s")
    data_type_singular = _("VIP")
    data_type_plural = _("VIPs")
    policy_rules = (("network", "delete_vip"),)

    def allowed(self, request, datum=None):
        if datum and not datum.vip_id:
            return False
        return True


class DeletePoolLink(policy.PolicyTargetMixin, tables.DeleteAction):
    name = "deletepool"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of %(data_type)s")
    data_type_singular = _("Pool")
    data_type_plural = _("Pools")
    policy_rules = (("network", "delete_pool"),)

    def allowed(self, request, datum=None):
        if datum and datum.vip_id:
            return False
        return True


class DeleteMonitorLink(policy.PolicyTargetMixin,
                        tables.DeleteAction):
    name = "deletemonitor"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of %(data_type)s")
    data_type_singular = _("Monitor")
    data_type_plural = _("Monitors")
    policy_rules = (("network", "delete_health_monitor"),)


class DeleteMemberLink(policy.PolicyTargetMixin, tables.DeleteAction):
    name = "deletemember"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of %(data_type)s")
    data_type_singular = _("Member")
    data_type_plural = _("Members")
    policy_rules = (("network", "delete_member"),)


class UpdatePoolLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updatepool"
    verbose_name = _("Edit Pool")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_pool"),)

    def get_link_url(self, pool):
        base_url = reverse("horizon:project:loadbalancers:updatepool",
                           kwargs={'pool_id': pool.id})
        return base_url


class UpdateVipLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updatevip"
    verbose_name = _("Edit VIP")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_vip"),)

    def get_link_url(self, pool):
        base_url = reverse("horizon:project:loadbalancers:updatevip",
                           kwargs={'vip_id': pool.vip_id})
        return base_url

    def allowed(self, request, datum=None):
        if datum and not datum.vip_id:
            return False
        return True


class UpdateMemberLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updatemember"
    verbose_name = _("Edit Member")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_member"),)

    def get_link_url(self, member):
        base_url = reverse("horizon:project:loadbalancers:updatemember",
                           kwargs={'member_id': member.id})
        return base_url


class UpdateMonitorLink(policy.PolicyTargetMixin, tables.LinkAction):
    name = "updatemonitor"
    verbose_name = _("Edit Monitor")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_health_monitor"),)

    def get_link_url(self, monitor):
        base_url = reverse("horizon:project:loadbalancers:updatemonitor",
                           kwargs={'monitor_id': monitor.id})
        return base_url


def get_vip_link(pool):
    if pool.vip_id:
        return reverse("horizon:project:loadbalancers:vipdetails",
                       args=(http.urlquote(pool.vip_id),))
    else:
        return None


class AddPMAssociationLink(policy.PolicyTargetMixin,
                           tables.LinkAction):
    name = "addassociation"
    verbose_name = _("Associate Monitor")
    url = "horizon:project:loadbalancers:addassociation"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_pool_health_monitor"),)

    def allowed(self, request, datum=None):
        try:
            tenant_id = request.user.tenant_id
            monitors = api.lbaas.pool_health_monitor_list(request,
                                                          tenant_id=tenant_id)
            for m in monitors:
                if m.id not in datum['health_monitors']:
                    return True
        except Exception:
            exceptions.handle(request,
                              _('Failed to retrieve health monitors.'))
        return False


class DeletePMAssociationLink(policy.PolicyTargetMixin,
                              tables.LinkAction):
    name = "deleteassociation"
    verbose_name = _("Disassociate Monitor")
    url = "horizon:project:loadbalancers:deleteassociation"
    classes = ("ajax-modal", "btn-danger")
    icon = "remove"
    policy_rules = (("network", "delete_pool_health_monitor"),)

    def allowed(self, request, datum=None):
        if datum and not datum['health_monitors']:
            return False
        return True


class PoolsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:loadbalancers:pooldetails")
    description = tables.Column('description', verbose_name=_("Description"))
    provider = tables.Column('provider', verbose_name=_("Provider"),
                             filters=(lambda v: filters.default(v, _('N/A')),))
    subnet_name = tables.Column('subnet_name', verbose_name=_("Subnet"))
    protocol = tables.Column('protocol', verbose_name=_("Protocol"))
    status = tables.Column('status', verbose_name=_("Status"))
    vip_name = tables.Column('vip_name', verbose_name=_("VIP"),
                             link=get_vip_link)

    class Meta:
        name = "poolstable"
        verbose_name = _("Pools")
        table_actions = (AddPoolLink, DeletePoolLink)
        row_actions = (UpdatePoolLink, AddVipLink, UpdateVipLink,
                       DeleteVipLink, AddPMAssociationLink,
                       DeletePMAssociationLink, DeletePoolLink)


def get_pool_link(member):
    return reverse("horizon:project:loadbalancers:pooldetails",
                   args=(http.urlquote(member.pool_id),))


def get_member_link(member):
    return reverse("horizon:project:loadbalancers:memberdetails",
                   args=(http.urlquote(member.id),))


class MembersTable(tables.DataTable):
    address = tables.Column('address',
                            verbose_name=_("IP Address"),
                            link=get_member_link,
                            attrs={'data-type': "ip"})
    protocol_port = tables.Column('protocol_port',
                                  verbose_name=_("Protocol Port"))
    weight = tables.Column('weight',
                           verbose_name=_("Weight"))
    pool_name = tables.Column('pool_name',
                              verbose_name=_("Pool"), link=get_pool_link)
    status = tables.Column('status', verbose_name=_("Status"))

    class Meta:
        name = "memberstable"
        verbose_name = _("Members")
        table_actions = (AddMemberLink, DeleteMemberLink)
        row_actions = (UpdateMemberLink, DeleteMemberLink)


def get_monitor_details(monitor):
    if monitor.type in ('HTTP', 'HTTPS'):
        return ("%(http_method)s %(url_path)s => %(codes)s" %
                {'http_method': monitor.http_method,
                 'url_path': monitor.url_path,
                 'codes': monitor.expected_codes})
    else:
        return _("-")


class MonitorsTable(tables.DataTable):
    monitor_type = tables.Column(
        "type", verbose_name=_("Monitor Type"),
        link="horizon:project:loadbalancers:monitordetails")
    delay = tables.Column("delay", verbose_name=_("Delay"))
    timeout = tables.Column("timeout", verbose_name=_("Timeout"))
    max_retries = tables.Column("max_retries", verbose_name=_("Max Retries"))
    details = tables.Column(get_monitor_details, verbose_name=_("Details"))

    class Meta:
        name = "monitorstable"
        verbose_name = _("Monitors")
        table_actions = (AddMonitorLink, DeleteMonitorLink)
        row_actions = (UpdateMonitorLink, DeleteMonitorLink)
