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

import json

from django.http import HttpResponse   # noqa
from django.utils.translation import ugettext_lazy as _  # noqa
from django.views.generic import TemplateView  # noqa

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.api import ceilometer

from openstack_dashboard.dashboards.admin.metering import tabs as \
    metering_tabs


class IndexView(tabs.TabbedTableView):
    tab_group_class = metering_tabs.CeilometerOverviewTabs
    template_name = 'admin/metering/index.html'


class SamplesView(TemplateView):
    template_name = "admin/metering/samples.csv"

    def get(self, request, *args, **kwargs):
        meter = request.GET.get('meter', None)
        meter_name = meter.replace(".", "_")
        date_options = request.GET.get('date_options', None)
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)
        resource = request.GET.get('resource', None)
        stats_attr = request.GET.get('stats_attr', 'avg')

        # TODO(lsmola) all timestamps should probably work with
        # current timezone. And also show the current timezone in chart.
        if (date_options == "other"):
            try:
                if date_from:
                    date_from = datetime.strptime(date_from,
                                                  "%Y-%m-%d")
                else:
                    # TODO(lsmola) there should be probably the date
                    # of the first sample as default, so it correctly
                    # counts the time window. Though I need ordering
                    # and limit of samples to obtain that.
                    pass
                if date_to:
                    date_to = datetime.strptime(date_to,
                                                "%Y-%m-%d")
                    # It return beginning of the day, I want the and of
                    # the day, so i will add one day without a second.
                    date_to = (date_to + timedelta(days=1) -
                               timedelta(seconds=1))
                else:
                    date_to = datetime.now()
            except Exception:
                raise ValueError("The dates haven't been "
                                 "recognized")
        else:
            try:
                date_from = datetime.now() - timedelta(days=int(date_options))
                date_to = datetime.now()
            except Exception:
                raise ValueError("The time delta must be an "
                                 "integer representing days.")

        if date_from and date_to:
            if date_to < date_from:
                # TODO(lsmola) propagate the Value error through Horizon
                # handler to the client with verbose message.
                raise ValueError("Date to must be bigger than date "
                                 "from.")
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

        query = [{"field": "metadata.OS-EXT-AZ:availability_zone",
                  "op": "eq",
                  "value": "nova"}]

        additional_query = []
        if date_from:
            additional_query += [{'field': 'timestamp',
                                  'op': 'ge',
                                  'value': date_from}]
        if date_to:
            additional_query += [{'field': 'timestamp',
                                  'op': 'le',
                                  'value': date_to}]

        # TODO(lsmola) replace this by logic implemented in I1 in bugs
        # 1226479 and 1226482, this is just a quick fix for RC1
        try:
            meter_list = [m for m in ceilometer.meter_list(request)
                            if m.name == meter]
            unit = meter_list[0].unit
        except Exception:
            unit = ""

        if request.GET.get('group_by', None) == "project":
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

            ceilometer_usage = ceilometer.CeilometerUsage(request)
            resources = ceilometer_usage.resource_aggregates_with_statistics(
                queries, [meter], period=period, stats_attr=None,
                additional_query=additional_query)

            series = []
            for resource in resources:
                name = resource.id
                if getattr(resource, meter_name):
                    serie = {'unit': unit,
                             'name': name,
                             'data': []}

                    for statistic in getattr(resource, meter_name):
                        date = statistic.duration_end[:19]
                        value = int(getattr(statistic, stats_attr))
                        serie['data'].append({'x': date, 'y': value})

                    series.append(serie)
        else:
            ceilometer_usage = ceilometer.CeilometerUsage(request)
            try:
                resources = ceilometer_usage.resources_with_statistics(
                    query, [meter], period=period, stats_attr=None,
                    additional_query=additional_query)
            except Exception:
                resources = []
                exceptions.handle(request,
                                  _('Unable to retrieve statistics.'))

            series = []
            for resource in resources:
                if getattr(resource, meter_name):
                    serie = {'unit': unit,
                             'name': resource.resource_id,
                             'data': []}
                    for statistic in getattr(resource, meter_name):
                        date = statistic.duration_end[:19]
                        value = int(getattr(statistic, stats_attr))
                        serie['data'].append({'x': date, 'y': value})

                    series.append(serie)

        ret = {}
        ret['series'] = series
        ret['settings'] = {}

        return HttpResponse(json.dumps(ret),
            mimetype='application/json')
