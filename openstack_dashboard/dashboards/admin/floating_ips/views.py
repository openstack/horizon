# Copyright 2016 Letv Cloud Computing
# All Rights Reserved.
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

from collections import OrderedDict

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
import netaddr
from oslo_utils import uuidutils

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized
from horizon import views

from openstack_dashboard import api
from openstack_dashboard import exceptions as dashboard_exception
from openstack_dashboard.utils import futurist_utils

from openstack_dashboard.dashboards.admin.floating_ips \
    import forms as fip_forms
from openstack_dashboard.dashboards.admin.floating_ips \
    import tables as fip_tables
from openstack_dashboard.dashboards.project.floating_ips \
    import tables as project_tables

# Servers the floating IPs are associated with are fetched by ID,
# SERVER_GET_BATCH_SIZE requests at a time. With more than
# ASSOCIATED_SERVERS_MAX servers one server list request is used like before.
SERVER_GET_BATCH_SIZE = 10
ASSOCIATED_SERVERS_MAX = 50


def get_floatingip_pools(request):
    pools = []
    try:
        search_opts = {'router:external': True}
        pools = api.neutron.network_list(request, **search_opts)
    except Exception:
        exceptions.handle(request,
                          _("Unable to retrieve floating IP pools."))
    return pools


def get_tenant_list(request):
    tenants = []
    try:
        tenants, has_more = api.keystone.tenant_list(request)
    except Exception:
        msg = _('Unable to retrieve project list.')
        exceptions.handle(request, msg)
    return tenants


class IndexView(tables.DataTableView):
    table_class = fip_tables.FloatingIPsTable
    page_title = _("Floating IPs")

    def _get_server(self, server_id):
        try:
            return api.nova.server_get(self.request, server_id)
        except dashboard_exception.NOT_FOUND:
            return None

    def _get_instances(self, instance_ids):
        instance_ids = sorted(set(instance_ids))
        if len(instance_ids) > ASSOCIATED_SERVERS_MAX:
            return api.nova.server_list(
                self.request,
                search_opts={'all_tenants': True},
                detailed=False)[0]
        instances = []
        for i in range(0, len(instance_ids), SERVER_GET_BATCH_SIZE):
            batch = instance_ids[i:i + SERVER_GET_BATCH_SIZE]
            servers = futurist_utils.call_functions_parallel(
                *[(self._get_server, [server_id]) for server_id in batch])
            instances.extend(s for s in servers if s is not None)
        return instances

    @memoized.memoized_method
    def get_data(self):
        floating_ips = []
        search_opts = self.get_filters()
        try:
            floating_ips = api.neutron.tenant_floating_ip_list(
                self.request,
                all_tenants=True,
                **search_opts)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve floating IP list.'))

        if floating_ips:
            instances = []
            try:
                # instance_id is the port's device_id, which the port owner
                # can set to anything; server IDs are UUIDs.
                instances = self._get_instances(
                    ip.instance_id for ip in floating_ips
                    if (ip.instance_type == 'compute' and
                        uuidutils.is_uuid_like(ip.instance_id)))
            except Exception:
                exceptions.handle(
                    self.request,
                    _('Unable to retrieve instance list.'))
            instances_dict = dict((obj.id, obj.name) for obj in instances)

            tenants = get_tenant_list(self.request)
            tenant_dict = OrderedDict([(t.id, t) for t in tenants])

            pools = get_floatingip_pools(self.request)
            pool_dict = dict((obj.id, obj.name) for obj in pools)

            for ip in floating_ips:
                ip.instance_name = instances_dict.get(ip.instance_id)
                ip.pool_name = pool_dict.get(ip.pool, ip.pool)
                tenant = tenant_dict.get(ip.tenant_id, None)
                ip.tenant_name = getattr(tenant, "name", None)

        return floating_ips


class DetailView(views.HorizonTemplateView):
    template_name = 'admin/floating_ips/detail.html'
    page_title = _("Floating IP Details")

    def _get_corresponding_data(self, resource, resource_id):
        function_dict = {"floating IP": api.neutron.tenant_floating_ip_get,
                         "instance": api.nova.server_get,
                         "network": api.neutron.network_get,
                         "router": api.neutron.router_get}
        url = reverse('horizon:admin:floating_ips:index')
        try:
            res = function_dict[resource](
                self.request, resource_id)
            if resource in ["network", "router"]:
                res.set_id_as_name_if_empty(length=0)
            return res
        except KeyError:
            msg = _('Unknown resource type for detail API.')
            exceptions.handle(self.request, msg, redirect=url)
        except Exception:
            msg = _('Unable to retrieve details for '
                    '%(resource)s "%(resource_id)s".') % {
                        "resource": resource,
                        "resource_id": resource_id}
            exceptions.handle(self.request, msg, redirect=url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        floating_ip_id = self.kwargs['floating_ip_id']
        floating_ip = self._get_corresponding_data("floating IP",
                                                   floating_ip_id)

        network = self._get_corresponding_data("network", floating_ip.pool)
        floating_ip.pool_name = network.name

        if floating_ip.instance_id and floating_ip.instance_type == 'compute':
            instance = self._get_corresponding_data(
                "instance", floating_ip.instance_id)
            floating_ip.instance_name = instance.name
        floating_ip.mapped_fixed_ip = project_tables.get_instance_info(
            floating_ip)

        if floating_ip.router_id:
            router = self._get_corresponding_data("router",
                                                  floating_ip.router_id)
            floating_ip.router_name = router.name
        table = fip_tables.FloatingIPsTable(self.request)
        context['floating_ip'] = floating_ip
        context["url"] = reverse('horizon:admin:floating_ips:index')
        context["actions"] = table.render_row_actions(floating_ip)
        return context


class AllocateView(forms.ModalFormView):
    form_class = fip_forms.AdminFloatingIpAllocate
    form_id = "allocate_floating_ip_form"
    template_name = 'admin/floating_ips/allocate.html'
    submit_label = _("Allocate Floating IP")
    submit_url = reverse_lazy("horizon:admin:floating_ips:allocate")
    cancel_url = reverse_lazy('horizon:admin:floating_ips:index')
    success_url = reverse_lazy('horizon:admin:floating_ips:index')
    page_title = _("Allocate Floating IP")

    @memoized.memoized_method
    def get_initial(self):
        tenants = get_tenant_list(self.request)
        tenant_list = [(t.id, t.name) for t in tenants]
        if not tenant_list:
            tenant_list = [(None, _("No project available"))]

        pools = get_floatingip_pools(self.request)
        pool_list = []
        for pool in pools:
            for subnet in pool.subnets:
                if netaddr.IPNetwork(subnet.cidr).version != 4:
                    continue
                pool_display_name = (_("%(pool_name)s %(cidr)s")
                                     % {'pool_name': pool.name,
                                        'cidr': subnet.cidr})
                pool_list.append((subnet.id, pool_display_name))
        if not pool_list:
            pool_list = [
                (None, _("No floating IP pools with IPv4 subnet available"))]

        return {'pool_list': pool_list,
                'tenant_list': tenant_list}
