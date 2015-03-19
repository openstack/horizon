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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.networks.ports \
    import forms as ports_forms
from openstack_dashboard.dashboards.admin.networks.ports \
    import tables as ports_tables
from openstack_dashboard.dashboards.admin.networks.ports \
    import tabs as ports_tabs
from openstack_dashboard.dashboards.project.networks.ports \
    import views as project_views


class CreateView(forms.ModalFormView):
    form_class = ports_forms.CreatePort
    form_id = "create_port_form"
    modal_header = _("Create Port")
    submit_label = _("Create Port")
    submit_url = "horizon:admin:networks:addport"
    page_title = _("Create Port")
    template_name = 'admin/networks/ports/create.html'
    url = 'horizon:admin:networks:detail'

    def get_success_url(self):
        return reverse(self.url,
                       args=(self.kwargs['network_id'],))

    @memoized.memoized_method
    def get_object(self):
        try:
            network_id = self.kwargs["network_id"]
            return api.neutron.network_get(self.request, network_id)
        except Exception:
            redirect = reverse(self.url,
                               args=(self.kwargs['network_id'],))
            msg = _("Unable to retrieve network.")
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['network'] = self.get_object()
        args = (self.kwargs['network_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        network = self.get_object()
        return {"network_id": self.kwargs['network_id'],
                "network_name": network.name}


class DetailView(project_views.DetailView):
    tab_group_class = ports_tabs.PortDetailTabs

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        port = context["port"]
        table = ports_tables.PortsTable(self.request,
                                        network_id=port.network_id)
        context["url"] = reverse('horizon:admin:networks:index')
        context["actions"] = table.render_row_actions(port)
        return context

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:admin:networks:index')


class UpdateView(project_views.UpdateView):
    form_class = ports_forms.UpdatePort
    template_name = 'admin/networks/ports/update.html'
    context_object_name = 'port'
    submit_url = "horizon:admin:networks:editport"
    success_url = 'horizon:admin:networks:detail'

    def get_initial(self):
        initial = super(UpdateView, self).get_initial()
        port = self._get_object()
        initial['binding__host_id'] = port['binding__host_id']
        return initial
