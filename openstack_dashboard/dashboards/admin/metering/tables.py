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

from django.template.defaultfilters import filesizeformat  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tables
from openstack_dashboard import api


class CommonFilterAction(tables.FilterAction):
    def filter(self, table, resources, filter_string):
        q = filter_string.lower()
        return [resource for resource in resources
                if q in resource.resource.lower() or
                   q in resource.tenant.lower() or
                   q in resource.user.lower()]


def get_status(fields):
    # TODO(lsmola) it should periodically renew the tables I guess
    def transform(datum):
        if any([getattr(datum, field, None) is 0 or getattr(datum, field, None)
                for field in fields]):
            return _("up")
        else:
            return _("none")
    return transform


class GlobalUsageTable(tables.DataTable):
    tenant = tables.Column("tenant", verbose_name=_("Tenant"), sortable=True,
                           filters=(lambda (t): getattr(t, 'name', ""),))
    user = tables.Column("user", verbose_name=_("User"), sortable=True,
                         filters=(lambda (u): getattr(u, 'name', ""),))
    instance = tables.Column("resource",
                             verbose_name=_("Resource"),
                             sortable=True)


class GlobalDiskUsageTable(tables.DataTable):
    tenant = tables.Column("id", verbose_name=_("Tenant"), sortable=True)
    disk_read_bytes = tables.Column("disk_read_bytes",
                                    filters=(filesizeformat,),
                                    verbose_name=_("Disk Read Bytes"),
                                    sortable=True)
    disk_read_requests = tables.Column("disk_read_requests",
                                       verbose_name=_("Disk Read Requests"),
                                       sortable=True)
    disk_write_bytes = tables.Column("disk_write_bytes",
                                     verbose_name=_("Disk Write Bytes"),
                                     filters=(filesizeformat,),
                                     sortable=True)
    disk_write_requests = tables.Column("disk_write_requests",
                                        verbose_name=_("Disk Write Requests"),
                                        sortable=True)

    class Meta:
        name = "global_disk_usage"
        verbose_name = _("Global Disk Usage (average of last 30 days)")
        table_actions = (CommonFilterAction,)
        multi_select = False


class GlobalNetworkTrafficUsageTable(tables.DataTable):
    tenant = tables.Column("id", verbose_name=_("Tenant"), sortable=True)
    network_incoming_bytes = tables\
            .Column("network_incoming_bytes",
                    verbose_name=_("Network Incoming Bytes"),
                    filters=(filesizeformat,),
                    sortable=True)
    network_incoming_packets = tables\
            .Column("network_incoming_packets",
                    verbose_name=_("Network Incoming Packets"),
                    sortable=True)
    network_outgoing_bytes = tables\
            .Column("network_outgoing_bytes",
                    verbose_name=_("Network Outgoing Bytes"),
                    filters=(filesizeformat,),
                    sortable=True)
    network_outgoing_packets = tables\
            .Column("network_outgoing_packets",
                    verbose_name=_("Network Outgoing Packets"),
                    sortable=True)

    class Meta:
        name = "global_network_traffic_usage"
        verbose_name = _("Global Network Traffic Usage (average "
                         "of last 30 days)")
        table_actions = (CommonFilterAction,)
        multi_select = False


class GlobalNetworkUsageTable(tables.DataTable):
    tenant = tables.Column("id", verbose_name=_("Tenant"), sortable=True)
    network_duration = tables.Column("network",
                                     verbose_name=_("Network Duration"),
                                     sortable=True)
    network_creation_requests = tables\
            .Column("network_create",
                    verbose_name=_("Network Creation Requests"),
                    sortable=True)
    subnet_duration = tables.Column("subnet",
                                    verbose_name=_("Subnet Duration"),
                                    sortable=True)
    subnet_creation = tables.Column("subnet_create",
                                    verbose_name=_("Subnet Creation Requests"),
                                    sortable=True)
    port_duration = tables.Column("port",
                                  verbose_name=_("Port Duration"),
                                  sortable=True)
    port_creation = tables.Column("port_create",
                                  verbose_name=_("Port Creation Requests"),
                                  sortable=True)
    router_duration = tables.Column("router",
                                    verbose_name=_("Router Duration"),
                                    sortable=True)
    router_creation = tables.Column("router_create",
                                    verbose_name=_("Router Creation Requests"),
                                    sortable=True)
    port_duration = tables.Column("port",
                                  verbose_name=_("Port Duration"),
                                  sortable=True)
    port_creation = tables.Column("port_create",
                                  verbose_name=_("Port Creation Requests"),
                                  sortable=True)
    ip_floating_duration = tables\
            .Column("ip_floating",
                    verbose_name=_("Floating IP Duration"),
                    sortable=True)
    ip_floating_creation = tables\
            .Column("ip_floating_create",
                    verbose_name=_("Floating IP Creation Requests"),
                    sortable=True)

    class Meta:
        name = "global_network_usage"
        verbose_name = _("Global Network Usage (average of last 30 days)")
        table_actions = (CommonFilterAction,)
        multi_select = False


class GlobalObjectStoreUsageUpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, object_id):
        ceilometer_usage = api.ceilometer.CeilometerUsage(request)

        query = ceilometer_usage.query_from_object_id(object_id)
        try:
            data = ceilometer_usage.global_object_store_usage(
                query,
                with_statistics=True)
        except Exception:
            data = []
            exceptions.handle(request,
                              _('Unable to retrieve statistics.'))
            return None
        return data[0]


class GlobalObjectStoreUsageTable(tables.DataTable):
    tenant = tables.Column("tenant", verbose_name=_("Tenant"), sortable=True,
                           filters=(lambda (t): getattr(t, 'name', ""),))
    status = tables.Column(get_status(["storage_objects",
                                       "storage_objects_size",
                                       "storage_objects_incoming_bytes",
                                       "storage_objects_outgoing_bytes"]),
                           verbose_name=_("Status"),
                           hidden=True)
    resource = tables.Column("resource",
                             verbose_name=_("Resource"),
                             sortable=True)
    storage_incoming_bytes = tables.Column(
        "storage_objects_incoming_bytes",
        verbose_name=_("Object Storage Incoming Bytes"),
        filters=(filesizeformat,),
        sortable=True)
    storage_outgoing_bytes = tables.Column(
        "storage_objects_outgoing_bytes",
        verbose_name=_("Object Storage Outgoing Bytes"),
        filters=(filesizeformat,),
        sortable=True)
    storage_objects = tables.Column(
        "storage_objects",
        verbose_name=_("Total Number of Objects"),
        sortable=True)
    storage_objects_size = tables.Column(
        "storage_objects_size",
        filters=(filesizeformat,),
        verbose_name=_("Total Size of Objects "),
        sortable=True)

    class Meta:
        name = "global_object_store_usage"
        verbose_name = _("Global Object Store Usage (average of last 30 days)")
        table_actions = (CommonFilterAction,)
        row_class = GlobalObjectStoreUsageUpdateRow
        status_columns = ["status"]
        multi_select = False
