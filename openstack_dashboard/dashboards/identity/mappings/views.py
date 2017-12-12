# Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard import policy

from openstack_dashboard.dashboards.identity.mappings \
    import forms as mapping_forms
from openstack_dashboard.dashboards.identity.mappings \
    import tables as mapping_tables


class IndexView(tables.DataTableView):
    table_class = mapping_tables.MappingsTable
    page_title = _("Mappings")

    def get_data(self):
        mappings = []
        if policy.check((("identity", "identity:list_mappings"),),
                        self.request):
            try:
                mappings = api.keystone.mapping_list(self.request)
            except Exception:
                exceptions.handle(
                    self.request,
                    _('Unable to retrieve mapping list.'))
        else:
            msg = _("Insufficient privilege level to view mapping "
                    "information.")
            messages.info(self.request, msg)
        return mappings


class UpdateView(forms.ModalFormView):
    template_name = 'identity/mappings/update.html'
    form_id = "update_mapping_form"
    form_class = mapping_forms.UpdateMappingForm
    submit_label = _("Update Mapping")
    submit_url = "horizon:identity:mappings:update"
    success_url = reverse_lazy('horizon:identity:mappings:index')
    page_title = _("Update Mapping")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.keystone.mapping_get(
                self.request,
                self.kwargs['mapping_id'])
        except Exception:
            redirect = reverse("horizon:identity:mappings:index")
            exceptions.handle(self.request,
                              _('Unable to update mapping.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        args = (self.get_object().id,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        mapping = self.get_object()
        rules = json.dumps(mapping.rules, indent=4)
        return {'id': mapping.id,
                'rules': rules}


class CreateView(forms.ModalFormView):
    template_name = 'identity/mappings/create.html'
    form_id = "create_mapping_form"
    form_class = mapping_forms.CreateMappingForm
    submit_label = _("Create Mapping")
    submit_url = reverse_lazy("horizon:identity:mappings:create")
    success_url = reverse_lazy('horizon:identity:mappings:index')
    page_title = _("Create Mapping")
