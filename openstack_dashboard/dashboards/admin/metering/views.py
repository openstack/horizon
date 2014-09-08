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

from django.core.urlresolvers import reverse
from django.http import HttpResponse   # noqa
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
import django.views

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon.utils import csvbase

from openstack_dashboard import api
from openstack_dashboard.api import ceilometer

from openstack_dashboard.dashboards.admin.metering import tables as \
    metering_tables
from openstack_dashboard.dashboards.admin.metering import tabs as \
    metering_tabs


class IndexView(tabs.TabbedTableView):
    tab_group_class = metering_tabs.CeilometerOverviewTabs
    template_name = 'admin/metering/index.html'


class SamplesView(django.views.generic.TemplateView):
    template_name = "admin/metering/samples.csv"

    @staticmethod
    def _series_for_meter(aggregates,
                          resource_name,
                          meter_name,
                          stats_name,
                          unit):
        """Construct datapoint series for a meter from resource aggregates."""
        series = []
        for resource in aggregates:
            if resource.get_meter(meter_name):
                point = {'unit': unit,
                         'name': getattr(resource, resource_name),
                         'data': []}
                for statistic in resource.get_meter(meter_name):
                    date = statistic.duration_end[:19]
                    value = float(getattr(statistic, stats_name))
                    point['data'].append({'x': date, 'y': value})
                series.append(point)
        return series

    def get(self, request, *args, **kwargs):
        meter = request.GET.get('meter', None)
        if not meter:
            return HttpResponse(json.dumps({}),
                                content_type='application/json')

        meter_name = meter.replace(".", "_")
        date_options = request.GET.get('date_options', None)
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)
        stats_attr = request.GET.get('stats_attr', 'avg')
        group_by = request.GET.get('group_by', None)

        resources, unit = query_data(request,
                                     date_from,
                                     date_to,
                                     date_options,
                                     group_by,
                                     meter)
        resource_name = 'id' if group_by == "project" else 'resource_id'
        series = self._series_for_meter(resources,
                                        resource_name,
                                        meter_name,
                                        stats_attr,
                                        unit)

        ret = {}
        ret['series'] = series
        ret['settings'] = {}

        return HttpResponse(json.dumps(ret),
            content_type='application/json')


class ReportView(tables.MultiTableView):
    template_name = 'admin/metering/report.html'

    def get_tables(self):
        if self._tables:
            return self._tables
        project_data = load_report_data(self.request)
        table_instances = []
        limit = int(self.request.POST.get('limit', '1000'))
        for project in project_data.keys():
            table = metering_tables.UsageTable(self.request,
                                               data=project_data[project],
                                               kwargs=self.kwargs.copy())
            table.title = project
            t = (table.name, table)
            table_instances.append(t)
            if len(table_instances) == limit:
                break
        self._tables = SortedDict(table_instances)
        self.project_data = project_data
        return self._tables

    def handle_table(self, table):
        name = table.name
        handled = self._tables[name].maybe_handle()
        return handled

    def get_context_data(self, **kwargs):
        context = {'tables': self.get_tables().values()}
        context['csv_url'] = reverse('horizon:admin:metering:csvreport')
        return context


class CsvReportView(django.views.generic.View):
    def get(self, request, **response_kwargs):
        render_class = ReportCsvRenderer
        response_kwargs.setdefault("filename", "usage.csv")
        context = {'usage': load_report_data(request)}
        resp = render_class(request=request,
                            template=None,
                            context=context,
                            content_type='csv',
                            **response_kwargs)
        return resp


class ReportCsvRenderer(csvbase.BaseCsvResponse):

    columns = [_("Project Name"), _("Meter"), _("Description"),
               _("Service"), _("Time"), _("Value (Avg)")]

    def get_row_data(self):

        for p in self.context['usage'].values():
            for u in p:
                yield (u["project"],
                       u["meter"],
                       u["description"],
                       u["service"],
                       u["time"],
                       u["value"])


def _calc_period(date_from, date_to):
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
    return period


def _calc_date_args(date_from, date_to, date_options):
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
            raise ValueError("The dates are not "
                             "recognized.")
    else:
        try:
            date_from = datetime.now() - timedelta(days=int(date_options))
            date_to = datetime.now()
        except Exception:
            raise ValueError("The time delta must be an "
                             "integer representing days.")
    return date_from, date_to


def query_data(request,
               date_from,
               date_to,
               date_options,
               group_by,
               meter,
               period=None,
               additional_query=None):
    date_from, date_to = _calc_date_args(date_from,
                                         date_to,
                                         date_options)
    if not period:
        period = _calc_period(date_from, date_to)
    if additional_query is None:
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
    if group_by == "project":
        try:
            tenants, more = api.keystone.tenant_list(
                request,
                domain=None,
                paginate=False)
        except Exception:
            tenants = []
            exceptions.handle(request,
                              _('Unable to retrieve project list.'))
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

    else:
        query = []

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

        ceilometer_usage = ceilometer.CeilometerUsage(request)
        try:
            resources = ceilometer_usage.resources_with_statistics(
                query, [meter], period=period, stats_attr=None,
                additional_query=additional_query,
                filter_func=filter_by_meter_name)
        except Exception:
            resources = []
            exceptions.handle(request,
                              _('Unable to retrieve statistics.'))
    return resources, unit


def load_report_data(request):
    meters = ceilometer.Meters(request)
    services = {
        _('Nova'): meters.list_nova(),
        _('Neutron'): meters.list_neutron(),
        _('Glance'): meters.list_glance(),
        _('Cinder'): meters.list_cinder(),
        _('Swift_meters'): meters.list_swift(),
        _('Kwapi'): meters.list_kwapi(),
    }
    project_rows = {}
    date_options = request.GET.get('date_options', 7)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    for meter in meters._cached_meters.values():
        service = None
        for name, m_list in services.items():
            if meter in m_list:
                service = name
                break
        # show detailed samples
        # samples = ceilometer.sample_list(request, meter.name)
        res, unit = query_data(request,
                               date_from,
                               date_to,
                               date_options,
                               "project",
                               meter.name,
                               3600 * 24)
        for re in res:
            values = re.get_meter(meter.name.replace(".", "_"))
            if values:
                for value in values:
                    row = {"name": 'none',
                           "project": re.id,
                           "meter": meter.name,
                           "description": meter.description,
                           "service": service,
                           "time": value._apiresource.period_end,
                           "value": value._apiresource.avg}
                    if re.id not in project_rows:
                        project_rows[re.id] = [row]
                    else:
                        project_rows[re.id].append(row)
    return project_rows
