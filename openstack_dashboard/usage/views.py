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

import collections

from django.contrib.humanize.templatetags import humanize as humanize_filters
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon.templatetags import sizeformat
from openstack_dashboard import api
from openstack_dashboard.usage import base


class UsageView(tables.DataTableView):
    usage_class = None
    show_deleted = True
    csv_template_name = None
    page_title = _("Overview")

    def __init__(self, *args, **kwargs):
        super(UsageView, self).__init__(*args, **kwargs)
        if not issubclass(self.usage_class, base.BaseUsage):
            raise AttributeError("You must specify a usage_class attribute "
                                 "which is a subclass of BaseUsage.")

    def get_template_names(self):
        if self.request.GET.get('format', 'html') == 'csv':
            return (self.csv_template_name or
                    ".".join((self.template_name.rsplit('.', 1)[0], 'csv')))
        return self.template_name

    def get_content_type(self):
        if self.request.GET.get('format', 'html') == 'csv':
            return "text/csv"
        return "text/html"

    def get_data(self):
        try:
            project_id = self.kwargs.get('project_id',
                                         self.request.user.tenant_id)
            self.usage = self.usage_class(self.request, project_id)
            self.usage.summarize(*self.usage.get_date_range())
            self.kwargs['usage'] = self.usage
            return self.usage.usage_list
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve usage information.'))
            return []

    def get_context_data(self, **kwargs):
        context = super(UsageView, self).get_context_data(**kwargs)
        context['table'].kwargs['usage'] = self.usage
        context['form'] = self.usage.form
        context['usage'] = self.usage

        try:
            context['simple_tenant_usage_enabled'] = \
                api.nova.extension_supported('SimpleTenantUsage', self.request)
        except Exception:
            context['simple_tenant_usage_enabled'] = True
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('format', 'html') == 'csv':
            render_class = self.csv_response_class
            response_kwargs.setdefault("filename", "usage.csv")
        else:
            render_class = self.response_class
        context = self.render_context_with_title(context)
        resp = render_class(request=self.request,
                            template=self.get_template_names(),
                            context=context,
                            content_type=self.get_content_type(),
                            **response_kwargs)
        return resp


def _check_network_allowed(request):
    return api.neutron.is_quotas_extension_supported(request)


ChartDef = collections.namedtuple(
    'ChartDef',
    ('quota_key', 'label', 'used_phrase', 'filters'))
# Each ChartDef should contains the following fields:
# - quota key:
#   The key must be included in a response of tenant_quota_usages().
# - Human Readable Name:
# - text to display when describing the quota.
#   If None is specified, the default value 'Used' will be used.
# - filters to be applied to the value
#   If None is specified, the default filter 'intcomma' will be applied.
#   if you want to apply no filters, specify an empty tuple or list.
# - allowed:
#   An optional argument used to determine if the chart section should be
#   displayed. Can be a static value or a function, which is called dynamically
#   with the request as it's first parameter.
CHART_DEFS = [
    {
        'title': _("Compute"),
        'charts': [
            ChartDef("instances", _("Instances"), None, None),
            ChartDef("cores", _("VCPUs"), None, None),
            ChartDef("ram", _("RAM"), None, (sizeformat.mb_float_format,)),
        ],
    },
    {
        'title': _("Volume"),
        'charts': [
            ChartDef("volumes", _("Volumes"), None, None),
            ChartDef("snapshots", _("Volume Snapshots"), None, None),
            ChartDef("gigabytes", _("Volume Storage"), None,
                     (sizeformat.diskgbformat,)),
        ],
    },
    {
        'title': _("Network"),
        'charts': [
            ChartDef("floatingip", _("Floating IPs"),
                     pgettext_lazy('Label in the limit summary', "Allocated"),
                     None),
            ChartDef("security_group", _("Security Groups"), None, None),
            ChartDef("security_group_rule", _("Security Group Rules"),
                     None, None),
            ChartDef("network", _("Networks"), None, None),
            ChartDef("port", _("Ports"), None, None),
            ChartDef("router", _("Routers"), None, None),
        ],
        'allowed': _check_network_allowed,
    },
]


def _apply_filters(value, filters):
    if not filters:
        return value
    for f in filters:
        value = f(value)
    return value


class ProjectUsageView(UsageView):

    def _get_charts_data(self):
        chart_sections = []
        for section in CHART_DEFS:
            if self._check_chart_allowed(section):
                chart_data = self._process_chart_section(section['charts'])
                chart_sections.append({
                    'title': section['title'],
                    'charts': chart_data
                })
        return chart_sections

    def _check_chart_allowed(self, chart_def):
        result = True
        if 'allowed' in chart_def:
            allowed = chart_def['allowed']
            result = allowed(self.request) if callable(allowed) else allowed
        return result

    def _process_chart_section(self, chart_defs):
        charts = []
        for t in chart_defs:
            if t.quota_key not in self.usage.limits:
                continue
            key = t.quota_key
            used = self.usage.limits[key]['used']
            quota = self.usage.limits[key]['quota']
            text = t.used_phrase
            if text is None:
                text = pgettext_lazy('Label in the limit summary', 'Used')

            filters = t.filters
            if filters is None:
                filters = (humanize_filters.intcomma,)
            used_display = _apply_filters(used, filters)
            # When quota is float('inf'), we don't show quota
            # so filtering is unnecessary.
            quota_display = None
            if quota != float('inf'):
                quota_display = _apply_filters(quota, filters)
            else:
                quota_display = quota

            charts.append({
                'type': key,
                'name': t.label,
                'used': used,
                'quota': quota,
                'used_display': used_display,
                'quota_display': quota_display,
                'text': text
            })
        return charts

    def get_context_data(self, **kwargs):
        context = super(ProjectUsageView, self).get_context_data(**kwargs)
        context['charts'] = self._get_charts_data()
        return context

    def get_data(self):
        data = super(ProjectUsageView, self).get_data()
        try:
            self.usage.get_limits()
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve limits information.'))
        return data
