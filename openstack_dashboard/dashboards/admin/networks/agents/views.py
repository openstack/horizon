# Copyright 2014 Kylincloud
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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.networks.agents \
    import forms as project_forms


class AddView(forms.ModalFormView):
    form_class = project_forms.AddDHCPAgent
    form_id = "add_dhcp_agent_form"
    template_name = 'admin/networks/agents/add.html'
    success_url = 'horizon:admin:networks:detail'
    failure_url = 'horizon:admin:networks:detail'
    submit_url = "horizon:admin:networks:adddhcpagent"
    title_and_label = _("Add DHCP Agent")
    submit_label = modal_header = page_title = title_and_label

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['network_id'],))

    def get_context_data(self, **kwargs):
        context = super(AddView, self).get_context_data(**kwargs)
        context['network_id'] = self.kwargs['network_id']
        args = (self.kwargs['network_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        initial = super(AddView, self).get_initial()
        agents = self._get_agents()
        network_id = self.kwargs['network_id']
        try:
            network = api.neutron.network_get(self.request, network_id)
            initial.update({"network_id": network_id,
                            "network_name": network.name,
                            "agents": agents})
            return initial
        except Exception:
            redirect = reverse(self.failure_url,
                               args=(self.kwargs['network_id'],))
            msg = _("Unable to retrieve network.")
            exceptions.handle(self.request, msg, redirect=redirect)

    @memoized.memoized_method
    def _get_agents(self):
        try:
            return api.neutron.agent_list(self.request,
                                          agent_type='DHCP agent')
        except Exception:
            redirect = reverse(self.failure_url,
                               args=(self.kwargs['network_id'],))
            msg = _("Unable to retrieve agent list.")
            exceptions.handle(self.request, msg, redirect=redirect)
