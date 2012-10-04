# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
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

from horizon.forms import ModalFormView

from openstack_dashboard.api import keystone
from .forms import DownloadOpenRCForm
from .tables import EndpointsTable


class OpenRCView(ModalFormView):
    form_class = DownloadOpenRCForm
    template_name = 'settings/project/settings.html'

    def get_data(self):
        services = []
        for i, service in enumerate(self.request.user.service_catalog):
            service['id'] = i
            services.append(keystone.Service(service))
        return services

    def get_context_data(self, **kwargs):
        context = super(OpenRCView, self).get_context_data(**kwargs)
        context["endpoints"] = EndpointsTable(self.request, self.get_data())
        return context

    def get_initial(self):
        return {'tenant': self.request.user.tenant_id}

    def form_valid(self, form):
        return form.handle(self.request, form.cleaned_data)
