# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
# Copyright 2013,  Big Switch Networks, Inc.
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

"""
Views for managing Neutron Routers.
"""

from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.utils import filters

from openstack_dashboard.dashboards.project.routers\
    import forms as project_forms
from openstack_dashboard.dashboards.project.routers import tables as rtables
from openstack_dashboard.dashboards.project.routers import tabs as rdtabs


class IndexView(tables.DataTableView):
    table_class = rtables.RoutersTable
    template_name = 'project/routers/index.html'
    page_title = _("Routers")

    def _get_routers(self, search_opts=None):
        try:
            tenant_id = self.request.user.tenant_id
            routers = api.neutron.router_list(self.request,
                                              tenant_id=tenant_id,
                                              search_opts=search_opts)
        except Exception:
            routers = []
            exceptions.handle(self.request,
                              _('Unable to retrieve router list.'))

        ext_net_dict = self._list_external_networks()

        for r in routers:
            r.name = r.name_or_id
            self._set_external_network(r, ext_net_dict)
        return routers

    def get_data(self):
        routers = self._get_routers()
        return routers

    def _list_external_networks(self):
        try:
            search_opts = {'router:external': True}
            ext_nets = api.neutron.network_list(self.request,
                                                **search_opts)
            ext_net_dict = OrderedDict((n['id'], n.name_or_id)
                                       for n in ext_nets)
        except Exception as e:
            msg = _('Unable to retrieve a list of external networks "%s".') % e
            exceptions.handle(self.request, msg)
            ext_net_dict = {}
        return ext_net_dict

    def _set_external_network(self, router, ext_net_dict):
        gateway_info = router.external_gateway_info
        if gateway_info:
            ext_net_id = gateway_info['network_id']
            if ext_net_id in ext_net_dict:
                gateway_info['network'] = ext_net_dict[ext_net_id]
            else:
                msg_params = {'ext_net_id': ext_net_id, 'router_id': router.id}
                msg = _('External network "%(ext_net_id)s" expected but not '
                        'found for router "%(router_id)s".') % msg_params
                messages.error(self.request, msg)
                # gateway_info['network'] is just the network name, so putting
                # in a smallish error message in the table is reasonable.
                gateway_info['network'] = pgettext_lazy(
                    'External network not found',
                    # Translators: The usage is "<UUID of ext_net> (Not Found)"
                    u'%s (Not Found)') % ext_net_id


class DetailView(tabs.TabbedTableView):
    tab_group_class = rdtabs.RouterDetailTabs
    template_name = 'horizon/common/_detail.html'
    failure_url = reverse_lazy('horizon:project:routers:index')
    network_url = 'horizon:project:networks:detail'
    page_title = "{{ router.name|default:router.id }}"

    @memoized.memoized_method
    def _get_data(self):
        try:
            router_id = self.kwargs['router_id']
            router = api.neutron.router_get(self.request, router_id)
            router.set_id_as_name_if_empty(length=0)
        except Exception:
            msg = _('Unable to retrieve details for router "%s".') \
                % router_id
            exceptions.handle(self.request, msg, redirect=self.failure_url)
        if router.external_gateway_info:
            ext_net_id = router.external_gateway_info['network_id']
            router.external_gateway_info['network_url'] = reverse(
                self.network_url, args=[ext_net_id])
            try:
                ext_net = api.neutron.network_get(self.request, ext_net_id,
                                                  expand_subnet=False)
                ext_net.set_id_as_name_if_empty(length=0)
                router.external_gateway_info['network'] = ext_net.name
            except Exception:
                msg = _('Unable to retrieve an external network "%s".') \
                    % ext_net_id
                exceptions.handle(self.request, msg)
                router.external_gateway_info['network'] = ext_net_id
        return router

    @memoized.memoized_method
    def _get_ports(self):
        try:
            ports = api.neutron.port_list(self.request,
                                          device_id=self.kwargs['router_id'])
        except Exception:
            ports = []
            msg = _('Unable to retrieve port details.')
            exceptions.handle(self.request, msg)
        return ports

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        router = self._get_data()
        table = rtables.RoutersTable(self.request)

        context["router"] = router
        context["url"] = self.failure_url
        context["actions"] = table.render_row_actions(router)
        context['dvr_supported'] = api.neutron.get_feature_permission(
            self.request, "dvr", "get")
        context['ha_supported'] = api.neutron.get_feature_permission(
            self.request, "l3-ha", "get")
        choices = table.STATUS_DISPLAY_CHOICES
        router.status_label = filters.get_display_label(choices, router.status)
        choices = table.ADMIN_STATE_DISPLAY_CHOICES
        router.admin_state_label = (
            filters.get_display_label(choices, router.admin_state))
        return context

    def get_tabs(self, request, *args, **kwargs):
        router = self._get_data()
        ports = self._get_ports()
        return self.tab_group_class(request, router=router,
                                    ports=ports, **kwargs)


class CreateView(forms.ModalFormView):
    form_class = project_forms.CreateForm
    form_id = "create_router_form"
    modal_header = _("Create Router")
    template_name = 'project/routers/create.html'
    success_url = reverse_lazy("horizon:project:routers:index")
    page_title = _("Create Router")
    submit_label = _("Create Router")
    submit_url = reverse_lazy("horizon:project:routers:create")


class UpdateView(forms.ModalFormView):
    form_class = project_forms.UpdateForm
    form_id = "update_router_form"
    modal_header = _("Edit Router")
    template_name = 'project/routers/update.html'
    success_url = reverse_lazy("horizon:project:routers:index")
    page_title = _("Update Router")
    submit_label = _("Save Changes")
    submit_url = "horizon:project:routers:update"

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        args = (self.kwargs['router_id'],)
        context["router_id"] = self.kwargs['router_id']
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def _get_object(self, *args, **kwargs):
        router_id = self.kwargs['router_id']
        try:
            return api.neutron.router_get(self.request, router_id)
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve router details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        router = self._get_object()
        initial = {'router_id': router['id'],
                   'tenant_id': router['tenant_id'],
                   'name': router['name'],
                   'admin_state': router['admin_state_up']}
        if hasattr(router, 'distributed'):
            initial['mode'] = ('distributed' if router.distributed
                               else 'centralized')
        if hasattr(router, 'ha'):
            initial['ha'] = router.ha
        return initial
