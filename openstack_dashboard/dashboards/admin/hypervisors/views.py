# Copyright 2013 B1 Systems GmbH
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.hypervisors \
    import tables as project_tables
from openstack_dashboard.dashboards.admin.hypervisors \
    import tabs as project_tabs
from django.conf import settings
from horizon import views as hz_views
import ipaddress, socket



class AdminIndexView(tabs.TabbedTableView):
    tab_group_class = project_tabs.HypervisorHostTabs
    template_name = 'admin/hypervisors/index.html'
    page_title = _("All Hypervisors")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["stats"] = api.nova.hypervisor_stats(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve hypervisor statistics.'))
        try:
            context["providers"] = api.placement.get_providers(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve providers statistics.'))
        return context


class AdminDetailView(tables.DataTableView):
    table_class = project_tables.AdminHypervisorInstancesTable
    template_name = 'admin/hypervisors/detail.html'
    page_title = _("Servers")

    def get_data(self):
        instances = []
        try:
            id, name = self.kwargs['hypervisor'].split('_', 1)
            result = api.nova.hypervisor_search(self.request,
                                                name)
            for hypervisor in result:
                if str(hypervisor.id) == id:
                    try:
                        instances += hypervisor.servers
                    except AttributeError:
                        pass
        except Exception:
            exceptions.handle(
                self.request,
                _('Unable to retrieve hypervisor instances list.'))
        return instances

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hypervisor_name = self.kwargs['hypervisor'].split('_', 1)[1]
        breadcrumb = [(hypervisor_name, None)]
        context['custom_breadcrumb'] = breadcrumb
        return context
    
class OpenHostAppView(hz_views.HorizonTemplateView):
    template_name = "admin/hypervisors/_host_app_modal.html"

    def _looks_like_ip(self, s):
        try:
            ipaddress.ip_address(s); return True
        except Exception:
            return False

    def _resolve_host(self, request, host):
        # 1) If already an IP, keep it
        if self._looks_like_ip(host):
            return host
        # 2) try nova hypervisor search for host_ip
        try:
            hypers = api.nova.hypervisor_search(request, host)
            for h in hypers or []:
                ip = getattr(h, "host_ip", None)
                if ip:
                    return ip
            # hypervisor_hostname might itself be an IP
            if hypers:
                hh = getattr(hypers[0], "hypervisor_hostname", None)
                if hh and self._looks_like_ip(hh):
                    return hh
        except Exception:
            pass
        # 3) DNS fallback
        try:
            return socket.gethostbyname(host)
        except Exception:
            return host  # last resort

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        raw_host = kwargs.get("host", "")
        host = self._resolve_host(self.request, raw_host)

        scheme = getattr(settings, "OPEN_LOCAL_APP_SCHEME", "https")  # you said HTTPS
        port   = getattr(settings, "OPEN_LOCAL_APP_PORT", 10000)
        path   = getattr(settings, "OPEN_LOCAL_APP_PATH", "/")

        ctx.update({
            "host_display": raw_host,
            "target_url": f"{scheme}://{host}:{port}{path}",
        })
        return ctx

