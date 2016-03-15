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
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.networks.ports \
    import forms as project_forms
from openstack_dashboard.dashboards.project.networks.ports \
    import tables as project_tables
from openstack_dashboard.dashboards.project.networks.ports \
    import tabs as project_tabs

STATE_DICT = dict(project_tables.DISPLAY_CHOICES)
STATUS_DICT = dict(project_tables.STATUS_DISPLAY_CHOICES)
VNIC_TYPES = dict(project_forms.VNIC_TYPES)


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.PortDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ port.name|default:port.id }}"

    @memoized.memoized_method
    def get_data(self):
        port_id = self.kwargs['port_id']

        try:
            port = api.neutron.port_get(self.request, port_id)
            port.admin_state_label = STATE_DICT.get(port.admin_state,
                                                    port.admin_state)
            port.status_label = STATUS_DICT.get(port.status,
                                                port.status)
            if port.get('binding__vnic_type'):
                port.binding__vnic_type = VNIC_TYPES.get(
                    port.binding__vnic_type, port.binding__vnic_type)
        except Exception:
            port = []
            redirect = self.get_redirect_url()
            msg = _('Unable to retrieve port details.')
            exceptions.handle(self.request, msg, redirect=redirect)

        if (api.neutron.is_extension_supported(self.request, 'mac-learning')
                and not hasattr(port, 'mac_state')):
            port.mac_state = api.neutron.OFF_STATE

        return port

    @memoized.memoized_method
    def get_network(self, network_id):
        try:
            network = api.neutron.network_get(self.request, network_id)
        except Exception:
            network = {}
            msg = _('Unable to retrieve network details.')
            exceptions.handle(self.request, msg)

        return network

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        port = self.get_data()
        network_url = "horizon:project:networks:detail"
        subnet_url = "horizon:project:networks:subnets:detail"
        network = self.get_network(port.network_id)
        port.network_name = network.get('name')
        port.network_url = reverse(network_url, args=[port.network_id])
        for ip in port.fixed_ips:
            ip['subnet_url'] = reverse(subnet_url, args=[ip['subnet_id']])
        table = project_tables.PortsTable(self.request,
                                          network_id=port.network_id)
        # TODO(robcresswell) Add URL for "Ports" crumb after bug/1416838
        breadcrumb = [
            (_("Networks"), self.get_redirect_url()),
            ((port.network_name or port.network_id), port.network_url),
            (_("Ports"),), ]
        context["custom_breadcrumb"] = breadcrumb
        context["port"] = port
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(port)
        return context

    def get_tabs(self, request, *args, **kwargs):
        port = self.get_data()
        return self.tab_group_class(request, port=port, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:networks:index')


class UpdateView(forms.ModalFormView):
    form_class = project_forms.UpdatePort
    form_id = "update_port_form"
    modal_header = _("Edit Port")
    template_name = 'project/networks/ports/update.html'
    context_object_name = 'port'
    submit_label = _("Save Changes")
    submit_url = "horizon:project:networks:editport"
    success_url = 'horizon:project:networks:detail'
    page_title = _("Update Port")

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['network_id'],))

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        port_id = self.kwargs['port_id']
        try:
            return api.neutron.port_get(self.request, port_id)
        except Exception:
            redirect = self.get_success_url()
            msg = _('Unable to retrieve port details')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        port = self._get_object()
        context['port_id'] = port['id']
        context['network_id'] = port['network_id']
        args = (self.kwargs['network_id'], self.kwargs['port_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        context['cancel_url'] = reverse(self.success_url,
                                        args=(self.kwargs['network_id'],))
        return context

    def get_initial(self):
        port = self._get_object()
        initial = {'port_id': port['id'],
                   'network_id': port['network_id'],
                   'tenant_id': port['tenant_id'],
                   'name': port['name'],
                   'admin_state': port['admin_state_up']}
        if port.get('binding__vnic_type'):
            initial['binding__vnic_type'] = port['binding__vnic_type']
        try:
            initial['mac_state'] = port['mac_learning_enabled']
        except Exception:
            # MAC Learning is not set
            pass
        return initial
