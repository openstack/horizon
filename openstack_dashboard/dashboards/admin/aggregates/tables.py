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

from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.aggregates import constants


class DeleteAggregateAction(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Host Aggregate",
            u"Delete Host Aggregates",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Host Aggregate",
            u"Deleted Host Aggregates",
            count
        )

    def delete(self, request, obj_id):
        api.nova.aggregate_delete(request, obj_id)


class CreateAggregateAction(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Host Aggregate")
    url = constants.AGGREGATES_CREATE_URL
    classes = ("ajax-modal",)
    icon = "plus"


class ManageHostsAction(tables.LinkAction):
    name = "manage"
    verbose_name = _("Manage Hosts")
    url = constants.AGGREGATES_MANAGE_HOSTS_URL
    classes = ("ajax-modal",)
    icon = "plus"


class UpdateMetadataAction(tables.LinkAction):
    name = "update-metadata"
    verbose_name = _("Update Metadata")
    ajax = False
    icon = "pencil"
    attrs = {"ng-controller": "MetadataModalHelperController as modal"}

    def __init__(self, attrs=None, **kwargs):
        kwargs['preempt'] = True
        super(UpdateMetadataAction, self).__init__(attrs, **kwargs)

    def get_link_url(self, datum):
        image_id = self.table.get_object_id(datum)
        self.attrs['ng-click'] = (
            "modal.openMetadataModal('aggregate', '%s', true)" % image_id)
        return "javascript:void(0);"


class UpdateAggregateAction(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Host Aggregate")
    url = constants.AGGREGATES_UPDATE_URL
    classes = ("ajax-modal",)
    icon = "pencil"


class AggregateFilterAction(tables.FilterAction):
    def filter(self, table, aggregates, filter_string):
        q = filter_string.lower()

        def comp(aggregate):
            return q in aggregate.name.lower()

        return filter(comp, aggregates)


class AvailabilityZoneFilterAction(tables.FilterAction):
    def filter(self, table, availability_zones, filter_string):
        q = filter_string.lower()

        def comp(availabilityZone):
            return q in availabilityZone.zoneName.lower()

        return filter(comp, availability_zones)


def get_aggregate_hosts(aggregate):
    return [host for host in aggregate.hosts]


def get_metadata(aggregate):
    return [' = '.join([key, val]) for key, val
            in aggregate.metadata.items()]


def get_available(zone):
    return zone.zoneState['available']


def get_zone_hosts(zone):
    hosts = zone.hosts
    host_details = []
    if hosts is None:
        return []
    for name, services in hosts.items():
        up = all(s['active'] and s['available'] for s in services.values())
        up = _("Services Up") if up else _("Services Down")
        host_details.append("%(host)s (%(up)s)" % {'host': name, 'up': up})
    return host_details


def safe_unordered_list(value):
    return filters.unordered_list(value, autoescape=True)


class HostAggregatesTable(tables.DataTable):
    name = tables.WrappingColumn('name', verbose_name=_('Name'))
    availability_zone = tables.Column('availability_zone',
                                      verbose_name=_('Availability Zone'))
    hosts = tables.Column(get_aggregate_hosts,
                          verbose_name=_("Hosts"),
                          wrap_list=True,
                          filters=(safe_unordered_list,))
    metadata = tables.Column(get_metadata,
                             verbose_name=_("Metadata"),
                             wrap_list=True,
                             filters=(safe_unordered_list,))

    class Meta(object):
        name = "host_aggregates"
        hidden_title = False
        verbose_name = _("Host Aggregates")
        table_actions = (AggregateFilterAction,
                         CreateAggregateAction,
                         DeleteAggregateAction)
        row_actions = (UpdateAggregateAction,
                       ManageHostsAction,
                       UpdateMetadataAction,
                       DeleteAggregateAction)


class AvailabilityZonesTable(tables.DataTable):
    name = tables.WrappingColumn('zoneName',
                                 verbose_name=_('Availability Zone Name'))
    hosts = tables.Column(get_zone_hosts,
                          verbose_name=_('Hosts'),
                          wrap_list=True,
                          filters=(safe_unordered_list,))
    available = tables.Column(get_available,
                              verbose_name=_('Available'),
                              status=True,
                              filters=(filters.yesno, filters.capfirst))

    def get_object_id(self, zone):
        return zone.zoneName

    class Meta(object):
        name = "availability_zones"
        hidden_title = False
        verbose_name = _("Availability Zones")
        table_actions = (AvailabilityZoneFilterAction,)
        multi_select = False
