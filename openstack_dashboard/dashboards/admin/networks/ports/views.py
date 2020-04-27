# Copyright 2012 NEC Corporation
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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.dashboards.admin.networks.ports \
    import tables as ports_tables
from openstack_dashboard.dashboards.admin.networks.ports \
    import tabs as ports_tabs
from openstack_dashboard.dashboards.admin.networks.ports \
    import workflows as admin_workflows
from openstack_dashboard.dashboards.project.networks.ports \
    import views as project_views


class CreateView(project_views.CreateView):
    workflow_class = admin_workflows.CreatePort
    failure_url = 'horizon:admin:networks:detail'

    def get_initial(self):
        network = self.get_network()
        return {"network_id": self.kwargs['network_id'],
                "network_name": network.name,
                "target_tenant_id": network.tenant_id}


class DetailView(project_views.DetailView):
    tab_group_class = ports_tabs.PortDetailTabs

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        port = context["port"]
        network_url = "horizon:admin:networks:detail"
        subnet_url = "horizon:admin:networks:subnets:detail"
        port.network_url = reverse(network_url, args=[port.network_id])
        for ip in port.fixed_ips:
            ip['subnet_url'] = reverse(subnet_url, args=[ip['subnet_id']])
        table = ports_tables.PortsTable(self.request,
                                        network_id=port.network_id)
        # TODO(robcresswell) Add URL for "Ports" crumb after bug/1416838
        breadcrumb = [
            ((port.network_name or port.network_id), port.network_url),
            (_("Ports"), None)
        ]
        context["custom_breadcrumb"] = breadcrumb
        context["url"] = \
            reverse('horizon:admin:networks:ports_tab', args=[port.network_id])
        context["actions"] = table.render_row_actions(port)
        return context

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:admin:networks:index')


class UpdateView(project_views.UpdateView):
    workflow_class = admin_workflows.UpdatePort
    failure_url = 'horizon:admin:networks:detail'

    def get_initial(self):
        initial = super(UpdateView, self).get_initial()
        port = self._get_object()
        if 'binding__host_id' in port:
            initial['binding__host_id'] = port['binding__host_id']
        initial['device_id'] = port['device_id']
        initial['device_owner'] = port['device_owner']

        return initial
