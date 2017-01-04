# Copyright 2015, Alcatel-Lucent USA Inc.
# All Rights Reserved.
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

from horizon import forms

from openstack_dashboard.dashboards.project.networks.ports.extensions.\
    allowed_address_pairs import forms as addr_pairs_forms


class AddAllowedAddressPair(forms.ModalFormView):
    form_class = addr_pairs_forms.AddAllowedAddressPairForm
    form_id = "addallowedaddresspair_form"
    template_name = 'project/networks/ports/add_addresspair.html'
    context_object_name = 'port'
    submit_label = _("Submit")
    submit_url = "horizon:project:networks:ports:addallowedaddresspairs"
    success_url = 'horizon:project:networks:ports:detail'
    page_title = _("Add Allowed Address Pair")

    def get_success_url(self):
        return reverse(self.success_url, args=(self.kwargs['port_id'],))

    def get_context_data(self, **kwargs):
        context = super(AddAllowedAddressPair, self).get_context_data(**kwargs)
        context["port_id"] = self.kwargs['port_id']
        context['submit_url'] = reverse(self.submit_url,
                                        args=(self.kwargs['port_id'],))
        return context

    def get_initial(self):
        return {'port_id': self.kwargs['port_id']}
