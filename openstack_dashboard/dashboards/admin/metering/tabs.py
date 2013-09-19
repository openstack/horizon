# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from datetime import datetime  # noqa
from datetime import timedelta  # noqa

from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tabs
from openstack_dashboard import api
from openstack_dashboard.api import ceilometer

from openstack_dashboard.dashboards.admin.metering import tables


def make_tenant_queries(request, days_before=30):
    try:
        tenants, more = api.keystone.tenant_list(
            request,
            domain=None,
            paginate=True,
            marker="tenant_marker")
    except Exception:
        tenants = []
        exceptions.handle(request,
                          _('Unable to retrieve tenant list.'))
    queries = {}
    for tenant in tenants:
        tenant_query = [{
            "field": "project_id",
            "op": "eq",
            "value": tenant.id}]

        queries[tenant.name] = tenant_query

    # TODO(lsmola) Just show last 30 days, should be switchable somewhere
    # above the table.
    date_from = datetime.now() - timedelta(days_before)
    date_to = datetime.now()
    additional_query = [{'field': 'timestamp',
                         'op': 'ge',
                         'value': date_from},
                        {'field': 'timestamp',
                         'op': 'le',
                         'value': date_to}]

    return queries, additional_query


def list_of_resource_aggregates(request, meters, stats_attr="avg"):
    queries, additional_query = make_tenant_queries(request)

    ceilometer_usage = ceilometer.CeilometerUsage(request)
    try:
        resource_aggregates = ceilometer_usage.\
            resource_aggregates_with_statistics(
                queries, meters, stats_attr="avg",
                additional_query=additional_query)
    except Exception:
        resource_aggregates = []
        exceptions.handle(request,
                          _('Unable to retrieve statistics.'))

    return resource_aggregates


class GlobalDiskUsageTab(tabs.TableTab):
    table_classes = (tables.GlobalDiskUsageTable,)
    name = _("Global Disk Usage")
    slug = "global_disk_usage"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_global_disk_usage_data(self):
        """ Disk usage table data aggregated by project """
        request = self.tab_group.request
        return list_of_resource_aggregates(request,
            ceilometer.GlobalDiskUsage.meters)


class GlobalNetworkTrafficUsageTab(tabs.TableTab):
    table_classes = (tables.GlobalNetworkTrafficUsageTable,)
    name = _("Global Network Traffic Usage")
    slug = "global_network_traffic_usage"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_global_network_traffic_usage_data(self):
        request = self.tab_group.request
        return list_of_resource_aggregates(request,
            ceilometer.GlobalNetworkTrafficUsage.meters)


class GlobalNetworkUsageTab(tabs.TableTab):
    table_classes = (tables.GlobalNetworkUsageTable,)
    name = _("Global Network Usage")
    slug = "global_network_usage"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_global_network_usage_data(self):
        request = self.tab_group.request
        return list_of_resource_aggregates(request,
            ceilometer.GlobalNetworkUsage.meters)

    def allowed(self, request):
        permissions = ("openstack.services.network",)
        return request.user.has_perms(permissions)


class GlobalObjectStoreUsageTab(tabs.TableTab):
    table_classes = (tables.GlobalObjectStoreUsageTable,)
    name = _("Global Object Store Usage")
    slug = "global_object_store_usage"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_global_object_store_usage_data(self):
        request = self.tab_group.request
        ceilometer_usage = ceilometer.CeilometerUsage(request)

        date_from = datetime.now() - timedelta(30)
        date_to = datetime.now()
        additional_query = [{'field': 'timestamp',
                             'op': 'ge',
                             'value': date_from},
                            {'field': 'timestamp',
                             'op': 'le',
                             'value': date_to}]
        try:
            result = ceilometer_usage.global_object_store_usage(
                with_statistics=True, additional_query=additional_query)
        except Exception:
            result = []
            exceptions.handle(request,
                              _('Unable to retrieve statistics.'))
        return result

    def allowed(self, request):
        permissions = ("openstack.services.object-store",)
        return request.user.has_perms(permissions)


class GlobalStatsTab(tabs.Tab):
    name = _("Stats")
    slug = "stats"
    template_name = ("admin/metering/stats.html")
    preload = False

    def get_context_data(self, request):
        query = [{"field": "metadata.OS-EXT-AZ:availability_zone",
                  "op": "eq",
                  "value": "nova"}]
        try:
            resources = ceilometer.resource_list(request, query,
                ceilometer_usage_object=None)
        except Exception:
            resources = []
            exceptions.handle(request,
                              _('Unable to retrieve Nova Ceilometer '
                                'resources.'))
        try:
            resource = resources[0]
            meters = [link['rel'] for link in resource.links
                if link['rel'] != "self"]
        except IndexError:
            resource = None
            meters = []

        meter_titles = {"instance": _("Duration of instance"),
                        "instance:<type>": _("Duration of instance <type>"
                            " (openstack types)"),
                        "memory": _("Volume of RAM in MB"),
                        "cpu": _("CPU time used"),
                        "cpu_util": _("Average CPU utilisation"),
                        "vcpus": _("Number of VCPUs"),
                        "disk.read.requests": _("Number of read requests"),
                        "disk.write.requests": _("Number of write requests"),
                        "disk.read.bytes": _("Volume of reads in B"),
                        "disk.write.bytes": _("Volume of writes in B"),
                        "disk.root.size": _("Size of root disk in GB"),
                        "disk.ephemeral.size": _("Size of ephemeral disk "
                            "in GB"),
                        "network.incoming.bytes": _("Number of incoming bytes "
                            "on the network for a VM interface"),
                        "network.outgoing.bytes": _("Number of outgoing bytes "
                            "on the network for a VM interface"),
                        "network.incoming.packets": _("Number of incoming "
                            "packets for a VM interface"),
                        "network.outgoing.packets": _("Number of outgoing "
                            "packets for a VM interface")}

        class MetersWrap(object):
            """ A quick wrapper for meter and associated titles. """
            def __init__(self, meter, meter_titles):
                self.name = meter
                self.title = meter_titles.get(meter, "")

        meters_objs = []
        for meter in meters:
            meters_objs.append(MetersWrap(meter, meter_titles))

        context = {'meters': meters_objs}
        return context


class CeilometerOverviewTabs(tabs.TabGroup):
    slug = "ceilometer_overview"
    tabs = (GlobalDiskUsageTab, GlobalNetworkTrafficUsageTab,
            GlobalObjectStoreUsageTab, GlobalNetworkUsageTab, GlobalStatsTab,)
    sticky = True
