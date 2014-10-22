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

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard import api


def calc_period(date_from, date_to):
    if date_from and date_to:
        if date_to < date_from:
            # TODO(lsmola) propagate the Value error through Horizon
            # handler to the client with verbose message.
            raise ValueError(_("To date to must be greater than From date."))

        # get the time delta in seconds
        delta = date_to - date_from
        if delta.days <= 0:
            # it's one day
            delta_in_seconds = 3600 * 24
        else:
            delta_in_seconds = delta.days * 24 * 3600 + delta.seconds
            # Lets always show 400 samples in the chart. Know that it is
        # maximum amount of samples and it can be lower.
        number_of_samples = 400
        period = delta_in_seconds / number_of_samples
    else:
        # If some date is missing, just set static window to one day.
        period = 3600 * 24
    return period


def calc_date_args(date_from, date_to, date_options):
    if date_options == "other":
        if date_from and not isinstance(date_from, datetime.date):
            try:
                date_from = datetime.datetime.strptime(date_from,
                                                       "%Y-%m-%d")
            except Exception:
                raise ValueError(_("From-date is not recognized"))

        if date_to:
            if not isinstance(date_to, datetime.date):
                try:
                    date_to = datetime.datetime.strptime(date_to,
                                                         "%Y-%m-%d")
                except Exception:
                    raise ValueError(_("To-date is not recognized"))
        else:
            date_to = timezone.now()
    else:
        try:
            date_to = timezone.now()
            date_from = date_to - datetime.timedelta(days=int(date_options))
        except Exception:
            raise ValueError(_("The time delta must be an "
                             "integer representing days."))
    return date_from, date_to


class ProjectAggregatesQuery(object):
    def __init__(self, request, date_from, date_to,
                 period=None, additional_query=[]):
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
        meter_list = [m for m in api.ceilometer.meter_list(self.request)
                      if m.name == meter]
        unit = ""
        if len(meter_list) > 0:
            unit = meter_list[0].unit
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

        meter_list = [m for m in api.ceilometer.meter_list(self.request)
                      if m.name == meter]

        unit = ""
        if len(meter_list) > 0:
            unit = meter_list[0].unit

        ceilometer_usage = api.ceilometer.CeilometerUsage(self.request)
        resources = ceilometer_usage.resources_with_statistics(
            self.queries, [meter],
            period=self.period,
            stats_attr=None,
            additional_query=self.additional_query,
            filter_func=filter_by_meter_name)

        return resources, unit
