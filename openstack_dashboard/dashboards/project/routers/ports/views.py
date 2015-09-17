# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
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

from openstack_dashboard.dashboards.project.routers.ports \
    import forms as project_forms
from openstack_dashboard.dashboards.project.routers.ports \
    import tabs as project_tabs


class AddInterfaceView(forms.ModalFormView):
    form_class = project_forms.AddInterface
    template_name = 'project/routers/ports/create.html'
    success_url = 'horizon:project:routers:detail'
    failure_url = 'horizon:project:routers:detail'
    page_title = _("Add Interface")

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['router_id'],))

    @memoized.memoized_method
    def get_object(self):
        try:
            router_id = self.kwargs["router_id"]
            return api.neutron.router_get(self.request, router_id)
        except Exception:
            redirect = reverse(self.failure_url, args=[router_id])
            msg = _("Unable to retrieve router.")
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(AddInterfaceView, self).get_context_data(**kwargs)
        context['router'] = self.get_object()
        context['form_url'] = 'horizon:project:routers:addinterface'
        return context

    def get_initial(self):
        router = self.get_object()
        return {"router_id": self.kwargs['router_id'],
                "router_name": router.name_or_id}


class SetGatewayView(forms.ModalFormView):
    form_class = project_forms.SetGatewayForm
    template_name = 'project/routers/ports/setgateway.html'
    success_url = 'horizon:project:routers:index'
    failure_url = 'horizon:project:routers:index'
    page_title = _("Set Gateway")

    def get_success_url(self):
        return reverse(self.success_url)

    @memoized.memoized_method
    def get_object(self):
        try:
            router_id = self.kwargs["router_id"]
            return api.neutron.router_get(self.request, router_id)
        except Exception:
            redirect = reverse(self.failure_url)
            msg = _("Unable to set gateway.")
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(SetGatewayView, self).get_context_data(**kwargs)
        context['router'] = self.get_object()
        return context

    def get_initial(self):
        router = self.get_object()
        return {"router_id": self.kwargs['router_id'],
                "router_name": router.name_or_id}


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.PortDetailTabs
    template_name = 'project/networks/ports/detail.html'
