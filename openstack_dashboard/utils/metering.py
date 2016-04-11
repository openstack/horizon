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

import datetime
import logging

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
import pytz

from horizon.utils import units

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


METER_API_MAPPINGS = {
    "instance": 'nova',
    "cpu": 'nova',
    "cpu_util": 'nova',
    "disk_read_requests": 'nova',
    "disk_write_requests": 'nova',
    "disk_read_bytes": 'nova',
    "disk_write_bytes": 'nova',
    "image": 'glance',
    "image_size": 'glance'
}


def calc_period(date_from, date_to, number_of_samples=400):
    if date_from and date_to:
        if date_to < date_from:
            # TODO(lsmola) propagate the Value error through Horizon
            # handler to the client with verbose message.
            raise ValueError(_("To date to must be greater than From date."))

        delta = date_to - date_from
        delta_in_seconds = delta.days * 24 * 3600 + delta.seconds
        period = delta_in_seconds / number_of_samples
    else:
        # If some date is missing, just set static window to one day.
        period = 3600 * 24
    return period


def calc_date_args(date_from, date_to, date_options):
    # TODO(lsmola) all timestamps should probably work with
    # current timezone. And also show the current timezone in chart.
    if date_options == "other":
        try:
            if date_from:
                date_from = pytz.utc.localize(
                    datetime.datetime.strptime(str(date_from), "%Y-%m-%d"))
            else:
                # TODO(lsmola) there should be probably the date
                # of the first sample as default, so it correctly
                # counts the time window. Though I need ordering
                # and limit of samples to obtain that.
                pass
            if date_to:
                date_to = pytz.utc.localize(
                    datetime.datetime.strptime(str(date_to), "%Y-%m-%d"))
                # It returns the beginning of the day, I want the end of
                # the day, so I add one day without a second.
                date_to = (date_to + datetime.timedelta(days=1) -
                           datetime.timedelta(seconds=1))
            else:
                date_to = timezone.now()
        except Exception:
            raise ValueError(_("The dates haven't been recognized"))
    else:
        try:
            date_to = timezone.now()
            date_from = date_to - datetime.timedelta(days=float(date_options))
        except Exception:
            raise ValueError(_("The time delta must be a number representing "
                               "the time span in days"))
    return date_from, date_to


def get_resource_name(request, resource_id, resource_name, meter_name):
    resource = None
    try:
        if resource_name == "resource_id":
            meter_name = 'instance' if "instance" in meter_name else meter_name
            api_type = METER_API_MAPPINGS.get(meter_name, '')
            if api_type == 'nova':
                resource = api.nova.server_get(request, resource_id)
            elif api_type == 'glance':
                resource = api.glance.image_get(request, resource_id)

    except Exception:
        LOG.info(_("Failed to get the resource name: %s"), resource_id,
                 exc_info=True)
    return resource.name if resource else resource_id


def series_for_meter(request, aggregates, group_by, meter_id,
                     meter_name, stats_name, unit, label=None):
    """Construct datapoint series for a meter from resource aggregates."""
    series = []
    for resource in aggregates:
        if resource.get_meter(meter_name):
            if label:
                name = label
            else:
                resource_name = ('id' if group_by == "project"
                                 else 'resource_id')
                resource_id = getattr(resource, resource_name)
                name = get_resource_name(request, resource_id,
                                         resource_name, meter_name)
            point = {'unit': unit,
                     'name': name,
                     'meter': meter_id,
                     'data': []}
            for statistic in resource.get_meter(meter_name):
                date = statistic.duration_end[:19]
                value = float(getattr(statistic, stats_name))
                point['data'].append({'x': date, 'y': value})
            series.append(point)
    return series


def normalize_series_by_unit(series):
    """Transform series' values into a more human readable form:
    1) Determine the data point with the maximum value
    2) Decide the unit appropriate for this value (normalize it)
    3) Convert other values to this new unit, if necessary
    """
    if not series:
        return series

    source_unit = target_unit = series[0]['unit']

    if not units.is_supported(source_unit):
        return series

    # Find the data point with the largest value and normalize it to
    # determine its unit - that will be the new unit
    maximum = max([d['y'] for point in series for d in point['data']])
    unit = units.normalize(maximum, source_unit)[1]

    # If unit needs to be changed, set the new unit for all data points
    # and convert all values to that unit
    if units.is_larger(unit, target_unit):
        target_unit = unit
        for i, point in enumerate(series[:]):
            if point['unit'] != target_unit:
                series[i]['unit'] = target_unit
                for j, d in enumerate(point['data'][:]):
                    series[i]['data'][j]['y'] = units.convert(
                        d['y'], source_unit, target_unit, fmt=True)[0]

    return series


def get_unit(meter, request):
    sample_list = api.ceilometer.sample_list(request, meter, limit=1)
    unit = ""
    if sample_list:
        unit = sample_list[0].counter_unit
    return unit


class ProjectAggregatesQuery(object):
    def __init__(self, request, date_from, date_to,
                 period=None, additional_query=None):
        additional_query = additional_query or []
        if not period:
            period = calc_period(date_from, date_to)
        if date_from:
            additional_query.append({'field': 'timestamp',
                                     'op': 'ge',
                                     'value': date_from})
        if date_to:
            additional_query.append({'field': 'timestamp',
                                     'op': 'le',
                                     'value': date_to})

        self.request = request
        self.period = period
        self.additional_query = additional_query
        tenants, more = api.keystone.tenant_list(request,
                                                 domain=None,
                                                 paginate=False)
        self.queries = {}

        for tenant in tenants:
            tenant_query = [{
                            "field": "project_id",
                            "op": "eq",
                            "value": tenant.id}]

            self.queries[tenant.name] = tenant_query

    def query(self, meter):
        unit = get_unit(meter, self.request)
        ceilometer_usage = api.ceilometer.CeilometerUsage(self.request)
        resources = ceilometer_usage.resource_aggregates_with_statistics(
            self.queries, [meter], period=self.period,
            stats_attr=None,
            additional_query=self.additional_query)
        return resources, unit


class MeterQuery(ProjectAggregatesQuery):
    def __init__(self, *args, **kwargs):
        # pop filterfunc and add it later to self.
        filterfunc = kwargs.pop('filterfunc', None)
        super(MeterQuery, self).__init__(*args, **kwargs)
        self.filterfunc = filterfunc
        # Resetting the tenant based filter set in base class
        self.queries = None

    def query(self, meter):
        def filter_by_meter_name(resource):
            """Function for filtering of the list of resources.

            Will pick the right resources according to currently selected
            meter.
            """
            for link in resource.links:
                if link['rel'] == meter:
                    # If resource has the currently chosen meter.
                    return True
            return False

        unit = get_unit(meter, self.request)

        ceilometer_usage = api.ceilometer.CeilometerUsage(self.request)
        resources = ceilometer_usage.resources_with_statistics(
            self.queries, [meter],
            period=self.period,
            stats_attr=None,
            additional_query=self.additional_query,
            filter_func=filter_by_meter_name)

        return resources, unit
