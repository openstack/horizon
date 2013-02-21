# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging

from django.core.urlresolvers import reverse

from horizon import tabs
from horizon import forms
from horizon import exceptions
from openstack_dashboard import api
from .tabs import PortDetailTabs
from .forms import (AddInterface, SetGatewayForm)


LOG = logging.getLogger(__name__)


class AddInterfaceView(forms.ModalFormView):
    form_class = AddInterface
    template_name = 'project/routers/ports/create.html'
    success_url = 'horizon:project:routers:detail'
    failure_url = 'horizon:project:routers:detail'

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['router_id'],))

    def get_object(self):
        if not hasattr(self, "_object"):
            try:
                router_id = self.kwargs["router_id"]
                self._object = api.quantum.router_get(self.request,
                                                      router_id)
            except:
                redirect = reverse(self.failure_url, args=[router_id])
                msg = _("Unable to retrieve router.")
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(AddInterfaceView, self).get_context_data(**kwargs)
        context['router'] = self.get_object()
        return context

    def get_initial(self):
        router = self.get_object()
        return {"router_id": self.kwargs['router_id'],
                "router_name": router.name}


class SetGatewayView(forms.ModalFormView):
    form_class = SetGatewayForm
    template_name = 'project/routers/ports/setgateway.html'
    success_url = 'horizon:project:routers:index'
    failure_url = 'horizon:project:routers:index'

    def get_success_url(self):
        return reverse(self.success_url)

    def get_object(self):
        if not hasattr(self, "_object"):
            try:
                router_id = self.kwargs["router_id"]
                self._object = api.quantum.router_get(self.request,
                                                      router_id)
            except:
                redirect = reverse(self.failure_url)
                msg = _("Unable to set gateway.")
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(SetGatewayView, self).get_context_data(**kwargs)
        context['router'] = self.get_object()
        return context

    def get_initial(self):
        router = self.get_object()
        return {"router_id": self.kwargs['router_id'],
                "router_name": router.name}


class DetailView(tabs.TabView):
    tab_group_class = PortDetailTabs
    template_name = 'project/networks/ports/detail.html'
