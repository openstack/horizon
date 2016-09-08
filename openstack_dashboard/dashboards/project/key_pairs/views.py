# Copyright 2016 Cisco Systems
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
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon.utils import memoized
from horizon import views
from openstack_dashboard.api import nova
from openstack_dashboard.dashboards.project.key_pairs \
    import forms as key_pairs_forms
from openstack_dashboard.dashboards.project.key_pairs \
    import tables as key_pairs_tables
from openstack_dashboard import policy


class IndexView(tables.DataTableView):
    table_class = key_pairs_tables.KeyPairsTable
    page_title = _("Key Pairs")

    def get_data(self):
        if not policy.check(
                (("compute", "os_compute_api:os-keypairs:index"),),
                self.request):
            msg = _("Insufficient privilege level to retrieve key pair list.")
            messages.info(self.request, msg)
            return []
        try:
            keypairs = nova.keypair_list(self.request)
        except Exception:
            keypairs = []
            exceptions.handle(self.request,
                              _('Unable to retrieve key pair list.'))
        return keypairs


class ImportView(forms.ModalFormView):
    form_class = key_pairs_forms.ImportKeypair
    template_name = 'project/key_pairs/import.html'
    submit_url = reverse_lazy(
        "horizon:project:key_pairs:import")
    success_url = reverse_lazy('horizon:project:key_pairs:index')
    submit_label = page_title = _("Import Key Pair")

    def get_object_id(self, keypair):
        return keypair.name


class DetailView(views.HorizonTemplateView):
    template_name = 'project/key_pairs/detail.html'
    page_title = _("Key Pair Details")

    @memoized.memoized_method
    def _get_data(self):
        try:
            keypair = nova.keypair_get(self.request,
                                       self.kwargs['keypair_name'])
        except Exception:
            redirect = reverse('horizon:project:key_pairs:index')
            msg = _('Unable to retrieve details for keypair "%s".')\
                % (self.kwargs['keypair_name'])
            exceptions.handle(self.request, msg,
                              redirect=redirect)
        return keypair

    def get_context_data(self, **kwargs):
        """Gets the context data for keypair."""
        context = super(DetailView, self).get_context_data(**kwargs)
        context['keypair'] = self._get_data()
        return context
