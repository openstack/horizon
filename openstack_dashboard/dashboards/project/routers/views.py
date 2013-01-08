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

"""
Views for managing Quantum Routers.
"""

import logging

from django import shortcuts
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from openstack_dashboard import api
from .ports.tables import PortsTable
from .forms import CreateForm
from .tables import RoutersTable
from .tabs import RouterDetailTabs


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = RoutersTable
    template_name = 'project/routers/index.html'

    def _get_routers(self, search_opts=None):
        try:
            tenant_id = self.request.user.tenant_id
            routers = api.quantum.router_list(self.request,
                                              tenant_id=tenant_id,
                                              search_opts=search_opts)
        except:
            routers = []
            exceptions.handle(self.request,
                              _('Unable to retrieve router list.'))
        for r in routers:
            r.set_id_as_name_if_empty()
        return routers

    def get_data(self):
        routers = self._get_routers()
        return routers


class DetailView(tables.MultiTableView):
    table_classes = (PortsTable, )
    template_name = 'project/routers/detail.html'
    failure_url = reverse_lazy('horizon:project:routers:index')

    def _get_data(self):
        if not hasattr(self, "_router"):
            try:
                router_id = self.kwargs['router_id']
                router = api.quantum.router_get(self.request, router_id)
                router.set_id_as_name_if_empty(length=0)
            except:
                msg = _('Unable to retrieve details for router "%s".') \
                        % (router_id)
                exceptions.handle(self.request, msg, redirect=self.failure_url)
            self._router = router
        return self._router

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["router"] = self._get_data()
        return context

    def get_interfaces_data(self):
        try:
            device_id = self.kwargs['router_id']
            ports = api.quantum.port_list(self.request,
                                          device_id=device_id)
        except:
            ports = []
            msg = _('Port list can not be retrieved.')
            exceptions.handle(self.request, msg)
        for p in ports:
            p.set_id_as_name_if_empty()
        return ports


class CreateView(forms.ModalFormView):
    form_class = CreateForm
    template_name = 'project/routers/create.html'
    success_url = reverse_lazy("horizon:project:routers:index")
