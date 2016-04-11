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
from openstack_dashboard.utils import metering as metering_utils


class IndexView(tabs.TabbedTableView):
    tab_group_class = metering_tabs.CeilometerOverviewTabs
    template_name = 'admin/metering/index.html'
    page_title = _("Resources Usage Overview")


class CreateUsageReport(forms.ModalFormView):
    form_class = metering_forms.UsageReportForm
    template_name = 'admin/metering/daily.html'
    success_url = reverse_lazy('horizon:admin:metering:index')
    page_title = _("Modify Usage Report Parameters")
    submit_label = _("View Usage Report")


class SamplesView(django.views.generic.TemplateView):
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
            date_from, date_to = metering_utils.calc_date_args(date_from,
                                                               date_to,
                                                               date_options)
        except Exception:
            exceptions.handle(self.request, _('Dates cannot be recognized.'))

        if group_by == 'project':
            query = metering_utils.ProjectAggregatesQuery(request,
                                                          date_from,
                                                          date_to,
                                                          3600 * 24)
        else:
            query = metering_utils.MeterQuery(request, date_from,
                                              date_to, 3600 * 24)

        resources, unit = query.query(meter)
        series = metering_utils.series_for_meter(request, resources,
                                                 group_by, meter,
                                                 meter_name, stats_attr, unit)

        series = metering_utils.normalize_series_by_unit(series)
        ret = {'series': series, 'settings': {}}
        return HttpResponse(json.dumps(ret), content_type='application/json')


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
               _("Service"), _("Time"), _("Value (Avg)"), _("Unit")]

    def get_row_data(self):

        for p in self.context['usage'].values():
            for u in p:
                yield (u["project"],
                       u["meter"],
                       u["description"],
                       u["service"],
                       u["time"],
                       u["value"],
                       u["unit"])


def load_report_data(request):
    meters = ceilometer.Meters(request)
    services = {
        _('Nova'): meters.list_nova(),
        _('Neutron'): meters.list_neutron(),
        _('Glance'): meters.list_glance(),
        _('Cinder'): meters.list_cinder(),
        _('Swift_meters'): meters.list_swift(),
        _('Kwapi'): meters.list_kwapi(),
        _('IPMI'): meters.list_ipmi(),
    }
    project_rows = {}
    date_options = request.GET.get('date_options', 7)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    try:
        date_from, date_to = metering_utils.calc_date_args(date_from,
                                                           date_to,
                                                           date_options)
    except Exception:
        exceptions.handle(request, _('Dates cannot be recognized.'))
    try:
        project_aggregates = metering_utils.ProjectAggregatesQuery(request,
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
        for r in res:
            values = r.get_meter(meter.name.replace(".", "_"))
            if values:
                for value in values:
                    row = {"name": 'none',
                           "project": r.id,
                           "meter": meter.name,
                           "description": meter.description,
                           "service": service,
                           "time": value._apiresource.period_end,
                           "value": value._apiresource.avg,
                           "unit": meter.unit}
                    if r.id not in project_rows:
                        project_rows[r.id] = [row]
                    else:
                        project_rows[r.id].append(row)
    return project_rows
