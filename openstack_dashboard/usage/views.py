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
            self.usage.get_limits()
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
        context['charts'] = []

        # (Used key, Max key, Human Readable Name, text to display when
        # describing the quota by default it is 'Used')
        types = [("totalInstancesUsed", "maxTotalInstances", _("Instances")),
                 ("totalCoresUsed", "maxTotalCores", _("VCPUs")),
                 ("totalRAMUsed", "maxTotalRAMSize", _("RAM")),
                 ("totalFloatingIpsUsed", "maxTotalFloatingIps",
                  _("Floating IPs"), _("Allocated")),
                 ("totalSecurityGroupsUsed", "maxSecurityGroups",
                  _("Security Groups"))]
        # Check for volume usage
        if 'totalVolumesUsed' in self.usage.limits and self.usage.limits[
                'totalVolumesUsed'] >= 0:
            types.append(("totalVolumesUsed", "maxTotalVolumes",
                         _("Volumes")))
            types.append(("totalGigabytesUsed", "maxTotalVolumeGigabytes",
                         _("Volume Storage")))
        for t in types:
            if t[0] in self.usage.limits and t[1] in self.usage.limits:
                text = False
                if len(t) > 3:
                    text = t[3]
                context['charts'].append({
                    'name': t[2],
                    'used': self.usage.limits[t[0]],
                    'max': self.usage.limits[t[1]],
                    'text': text
                })

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
