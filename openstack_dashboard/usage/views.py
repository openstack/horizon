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

from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
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


ChartDef = collections.namedtuple(
    'ChartDef',
    ('quota_key', 'label', 'used_phrase'))
# (quota key, Human Readable Name, text to display when
# describing the quota by default it is 'Used')
CHART_DEFS = [
    ChartDef("instances", _("Instances"), None),
    ChartDef("cores", _("VCPUs"), None),
    ChartDef("ram", _("RAM"), None),
    ChartDef("floatingip", _("Floating IPs"),
             pgettext_lazy('Label in the limit summary', "Allocated")),
    ChartDef("security_group", _("Security Groups"), None),
    ChartDef("volumes", _("Volumes"), None),
    ChartDef("gigabytes", _("Volume Storage"), None),
]


class ProjectUsageView(UsageView):

    def _get_charts_data(self):
        charts = []
        for t in CHART_DEFS:
            if t.quota_key not in self.usage.limits:
                continue
            key = t.quota_key
            used = self.usage.limits[key]['used']
            quota = self.usage.limits[key]['quota']
            text = t.used_phrase
            if text is None:
                text = pgettext_lazy('Label in the limit summary', 'Used')
            charts.append({
                'type': key,
                'name': t.label,
                'used': used,
                'max': quota,
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
