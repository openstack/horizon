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


from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tabs

from openstack_dashboard.api import ceilometer

from openstack_dashboard.dashboards.admin.metering import \
    tables as metering_tables

from openstack_dashboard.utils import metering


class GlobalStatsTab(tabs.TableTab):
    name = _("Stats")
    slug = "stats"
    template_name = "admin/metering/stats.html"
    preload = False
    table_classes = (metering_tables.UsageTable,)

    def get_context_data(self, request):
        meters = ceilometer.Meters(request)
        if not meters._ceilometer_meter_list:
            msg = _("There are no meters defined yet.")
            messages.warning(request, msg)

        context = {
            'nova_meters': meters.list_nova(),
            'neutron_meters': meters.list_neutron(),
            'glance_meters': meters.list_glance(),
            'cinder_meters': meters.list_cinder(),
            'swift_meters': meters.list_swift(),
            'kwapi_meters': meters.list_kwapi(),
            'ipmi_meters': meters.list_ipmi(),
        }

        return context


class UsageReportTab(tabs.TableTab):
    name = _("Usage Report")
    slug = "usage_report"
    template_name = "horizon/common/_detail_table.html"
    table_classes = (metering_tables.ReportTable,)

    def get_report_table_data(self):
        meters = ceilometer.Meters(self.request)
        services = {
            _('Nova'): meters.list_nova(),
            _('Neutron'): meters.list_neutron(),
            _('Glance'): meters.list_glance(),
            _('Cinder'): meters.list_cinder(),
            _('Swift_meters'): meters.list_swift(),
            _('Kwapi'): meters.list_kwapi(),
            _('IPMI'): meters.list_ipmi(),
        }
        report_rows = []

        date_options = self.request.session.get('period', 1)
        date_from = self.request.session.get('date_from', '')
        date_to = self.request.session.get('date_to', '')

        try:
            date_from, date_to = metering.calc_date_args(date_from,
                                                         date_to,
                                                         date_options)
        except Exception:
            exceptions.handle(self.request, _('Dates cannot be recognized.'))
        try:
            project_aggregates = metering.ProjectAggregatesQuery(self.request,
                                                                 date_from,
                                                                 date_to,
                                                                 3600 * 24)
        except Exception:
            exceptions.handle(self.request,
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
                               "value": value._apiresource.avg,
                               "unit": meter.unit}
                        report_rows.append(row)
        return report_rows


class CeilometerOverviewTabs(tabs.TabGroup):
    slug = "ceilometer_overview"
    tabs = (UsageReportTab, GlobalStatsTab,)
    sticky = True
