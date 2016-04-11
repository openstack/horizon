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
from django import shortcuts
from django import template
from django.template import defaultfilters as filters
from django.utils import http
from django.utils.http import urlencode
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import conf
from horizon import exceptions
from horizon import messages
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.access_and_security.floating_ips \
    import workflows
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


class DeleteVipLink(policy.PolicyTargetMixin, tables.Action):
    name = "deletevip"
    preempt = True
    verbose_name = _("Delete VIP")
    policy_rules = (("network", "delete_vip"),)
    classes = ('btn-danger',)

    def allowed(self, request, datum=None):
        if datum and datum.vip_id:
            self.help_text = _("Deleting VIP %s from this pool "
                               "cannot be undone.") % datum.vip_id
            return True
        return False

    def single(self, table, request, obj_id):
        try:
            vip_id = api.lbaas.pool_get(request, obj_id).vip_id
        except Exception as e:
            exceptions.handle(request,
                              _('Unable to locate VIP to delete. %s')
                              % e)
        if vip_id is not None:
            try:
                api.lbaas.vip_delete(request, vip_id)
                messages.success(request, _('Deleted VIP %s') % vip_id)
            except Exception as e:
                exceptions.handle(request,
                                  _('Unable to delete VIP. %s') % e)


class DeletePoolLink(policy.PolicyTargetMixin, tables.DeleteAction):
    name = "deletepool"
    policy_rules = (("network", "delete_pool"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Pool",
            u"Delete Pools",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Pool",
            u"Scheduled deletion of Pools",
            count
        )

    def allowed(self, request, datum=None):
        if datum and datum.vip_id:
            return False
        return True

    def delete(self, request, obj_id):
        try:
            api.lbaas.pool_delete(request, obj_id)
        except Exception as e:
            exceptions.handle(request,
                              _('Unable to delete pool. %s') % e)


class DeleteMonitorLink(policy.PolicyTargetMixin,
                        tables.DeleteAction):
    name = "deletemonitor"
    policy_rules = (("network", "delete_health_monitor"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Monitor",
            u"Delete Monitors",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Monitor",
            u"Scheduled deletion of Monitors",
            count
        )

    def delete(self, request, obj_id):
        try:
            api.lbaas.pool_health_monitor_delete(request, obj_id)
        except Exception as e:
            exceptions.handle(request,
                              _('Unable to delete monitor. %s') % e)


class DeleteMemberLink(policy.PolicyTargetMixin, tables.DeleteAction):
    name = "deletemember"
    policy_rules = (("network", "delete_member"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Member",
            u"Delete Members",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Member",
            u"Scheduled deletion of Members",
            count
        )

    def delete(self, request, obj_id):
        try:
            api.lbaas.member_delete(request, obj_id)
        except Exception as e:
            exceptions.handle(request,
                              _('Unable to delete member. %s') % e)


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
    icon = "trash"
    policy_rules = (("network", "delete_pool_health_monitor"),)

    def allowed(self, request, datum=None):
        if datum and not datum['health_monitors']:
            return False
        return True


class AddVIPFloatingIP(policy.PolicyTargetMixin, tables.LinkAction):
    """Add floating ip to VIP

    This class is extremely similar to AssociateIP from
    the instances page
    """
    name = "associate"
    verbose_name = _("Associate Floating IP")
    url = "horizon:project:access_and_security:floating_ips:associate"
    classes = ("ajax-modal",)
    icon = "link"
    policy_rules = (("compute", "network:associate_floating_ip"),)

    def allowed(self, request, pool):
        if not api.network.floating_ip_supported(request):
            return False
        if api.network.floating_ip_simple_associate_supported(request):
            return False
        if hasattr(pool, "vip") and pool.vip:
            vip = pool.vip
            return not (hasattr(vip, "fip") and vip.fip)
        return False

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        next_url = self.table.get_full_url()
        params = {
            workflows.IPAssociationWorkflow.redirect_param_name: next_url}
        if hasattr(datum, "vip") and datum.vip:
            vip = datum.vip
            params['port_id'] = vip.port_id
        params = urlencode(params)
        return "?".join([base_url, params])


class RemoveVIPFloatingIP(policy.PolicyTargetMixin, tables.Action):
    """Remove floating IP from VIP

    This class is extremely similar to the project instance table
    SimpleDisassociateIP feature, but just different enough to not
    be able to share much code
    """
    name = "disassociate"
    preempt = True
    icon = "unlink"
    verbose_name = _("Disassociate Floating IP")
    classes = ("btn-danger", "btn-disassociate",)
    policy_rules = (("compute", "network:disassociate_floating_ip"),)

    def allowed(self, request, pool):
        if not api.network.floating_ip_supported(request):
            return False
        if not conf.HORIZON_CONFIG["simple_ip_management"]:
            return False
        if hasattr(pool, "vip") and pool.vip:
            vip = pool.vip
            self.help_text = _('Floating IP will be removed '
                               'from VIP "%s".') % vip.name
            return hasattr(vip, "fip") and vip.fip
        return False

    def single(self, table, request, pool_id):
        try:
            pool = api.lbaas.pool_get(request, pool_id)
            fips = api.network.tenant_floating_ip_list(request)
            vip_fips = [fip for fip in fips
                        if fip.port_id == pool.vip.port_id]
            if not vip_fips:
                messages.info(request, _("No floating IPs to disassociate."))
            else:
                api.network.floating_ip_disassociate(request,
                                                     vip_fips[0].id)
                messages.success(request,
                                 _("Successfully disassociated "
                                   "floating IP: %s") % fip.ip)
        except Exception:
            exceptions.handle(request,
                              _("Unable to disassociate floating IP."))
        return shortcuts.redirect(request.get_full_path())


class UpdatePoolsRow(tables.Row):
    ajax = True

    def get_data(self, request, pool_id):
        pool = api.lbaas.pool_get(request, pool_id)
        try:
            vip = api.lbaas.vip_get(request, pool.vip_id)
            pool.vip = vip
        except Exception:
            pass
        try:
            subnet = api.neutron.subnet_get(request, pool.subnet_id)
            pool.subnet_name = subnet.cidr
        except Exception:
            pool.subnet_name = pool.subnet_id
        return pool


STATUS_CHOICES = (
    ("Active", True),
    ("Down", True),
    ("Error", False),
)


STATUS_DISPLAY_CHOICES = (
    ("Active", pgettext_lazy("Current status of a Pool",
                             u"Active")),
    ("Down", pgettext_lazy("Current status of a Pool",
                           u"Down")),
    ("Error", pgettext_lazy("Current status of a Pool",
                            u"Error")),
    ("Created", pgettext_lazy("Current status of a Pool",
                              u"Created")),
    ("Pending_Create", pgettext_lazy("Current status of a Pool",
                                     u"Pending Create")),
    ("Pending_Update", pgettext_lazy("Current status of a Pool",
                                     u"Pending Update")),
    ("Pending_Delete", pgettext_lazy("Current status of a Pool",
                                     u"Pending Delete")),
    ("Inactive", pgettext_lazy("Current status of a Pool",
                               u"Inactive")),
)


ADMIN_STATE_DISPLAY_CHOICES = (
    ("UP", pgettext_lazy("Admin state of a Load balancer", u"UP")),
    ("DOWN", pgettext_lazy("Admin state of a Load balancer", u"DOWN")),
)


def get_vip_name(pool):
    if hasattr(pool, "vip") and pool.vip:
        template_name = 'project/loadbalancers/_pool_table_vip_cell.html'
        context = {"vip": pool.vip, }
        return template.loader.render_to_string(template_name, context)
    else:
        return None


def get_subnet(pool):
    if hasattr(pool, "subnet") and pool.subnet:
        template_name = 'project/loadbalancers/_pool_table_subnet_cell.html'
        context = {"subnet": pool.subnet}
        return template.loader.render_to_string(template_name, context)
    else:
        return None


class PoolsTable(tables.DataTable):
    METHOD_DISPLAY_CHOICES = (
        ("round_robin", pgettext_lazy("load balancing method",
                                      u"Round Robin")),
        ("least_connections", pgettext_lazy("load balancing method",
                                            u"Least Connections")),
        ("source_ip", pgettext_lazy("load balancing method",
                                    u"Source IP")),
    )

    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link="horizon:project:loadbalancers:pooldetails")
    description = tables.Column('description', verbose_name=_("Description"))
    provider = tables.Column('provider', verbose_name=_("Provider"),
                             filters=(lambda v: filters.default(v, _('N/A')),))
    subnet_name = tables.Column(get_subnet, verbose_name=_("Subnet"))
    protocol = tables.Column('protocol', verbose_name=_("Protocol"))
    method = tables.Column('lb_method',
                           verbose_name=_("LB Method"),
                           display_choices=METHOD_DISPLAY_CHOICES)
    status = tables.Column('status',
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)
    vip_name = tables.Column(get_vip_name, verbose_name=_("VIP"))
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"),
                                display_choices=ADMIN_STATE_DISPLAY_CHOICES)

    class Meta(object):
        name = "poolstable"
        verbose_name = _("Pools")
        status_columns = ["status"]
        row_class = UpdatePoolsRow
        table_actions = (AddPoolLink, DeletePoolLink)
        row_actions = (UpdatePoolLink, AddVipLink, UpdateVipLink,
                       DeleteVipLink, AddPMAssociationLink,
                       DeletePMAssociationLink, DeletePoolLink,
                       AddVIPFloatingIP, RemoveVIPFloatingIP)


def get_pool_link(member):
    return reverse("horizon:project:loadbalancers:pooldetails",
                   args=(http.urlquote(member.pool_id),))


def get_member_link(member):
    return reverse("horizon:project:loadbalancers:memberdetails",
                   args=(http.urlquote(member.id),))


class UpdateMemberRow(tables.Row):
    ajax = True

    def get_data(self, request, member_id):
        member = api.lbaas.member_get(request, member_id)
        try:
            pool = api.lbaas.pool_get(request, member.pool_id)
            member.pool_name = pool.name
        except Exception:
            member.pool_name = member.pool_id
        return member


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
    status = tables.Column('status',
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"),
                                display_choices=ADMIN_STATE_DISPLAY_CHOICES)

    class Meta(object):
        name = "memberstable"
        verbose_name = _("Members")
        status_columns = ["status"]
        row_class = UpdateMemberRow
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
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"),
                                display_choices=ADMIN_STATE_DISPLAY_CHOICES)

    class Meta(object):
        name = "monitorstable"
        verbose_name = _("Monitors")
        table_actions = (AddMonitorLink, DeleteMonitorLink)
        row_actions = (UpdateMonitorLink, DeleteMonitorLink)
