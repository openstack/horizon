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

import json

from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse  # noqa
from django.utils.translation import ugettext_lazy as _
import django.views

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon.utils import csvbase

from openstack_dashboard.api import ceilometer

from openstack_dashboard.dashboards.admin.metering import forms as \
    metering_forms
from openstack_dashboard.dashboards.admin.metering import tabs as \
    metering_tabs
from openstack_dashboard.utils import metering as utils_metering


class IndexView(tabs.TabbedTableView):
    tab_group_class = metering_tabs.CeilometerOverviewTabs
    template_name = 'admin/metering/index.html'


class CreateUsageReport(forms.ModalFormView):
    form_class = metering_forms.UsageReportForm
    template_name = 'admin/metering/daily.html'
    success_url = reverse_lazy('horizon:admin:metering:index')


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

        try:
            date_from, date_to = utils_metering.calc_date_args(date_from,
                                                               date_to,
                                                               date_options)
        except Exception:
            exceptions.handle(self.request, _('Dates cannot be recognized.'))

        if group_by == 'project':
            query = utils_metering.ProjectAggregatesQuery(request,
                                                          date_from,
                                                          date_to,
                                                          3600 * 24)
        else:
            query = utils_metering.MeterQuery(request, date_from,
                                              date_to, 3600 * 24)

        resources, unit = query.query(meter_name)
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
    try:
        date_from, date_to = utils_metering.calc_date_args(date_from,
                                                           date_to,
                                                           date_options)
    except Exception:
        exceptions.handle(request, _('Dates cannot be recognised.'))
    try:
        project_aggregates = utils_metering.ProjectAggregatesQuery(request,
                                                                   date_from,
                                                                   date_to,
                                                                   3600 * 24)
    except Exception:
        exceptions.handle(request,
                          _('Unable to retrieve project list.'))
    for meter in meters._cached_meters.values():
        service = None
        for name, m_list in services.items():
            if meter in m_list:
                service = name
                break
        res, unit = project_aggregates.query(meter.name)
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
