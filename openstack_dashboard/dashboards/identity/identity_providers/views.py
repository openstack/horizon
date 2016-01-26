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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard import policy

from openstack_dashboard.dashboards.identity.identity_providers \
    import forms as idp_forms
from openstack_dashboard.dashboards.identity.identity_providers \
    import tables as idp_tables


class IndexView(tables.DataTableView):
    table_class = idp_tables.IdentityProvidersTable
    template_name = 'identity/identity_providers/index.html'
    page_title = _("Identity Providers")

    def get_data(self):
        idps = []
        if policy.check((("identity", "identity:list_identity_providers"),),
                        self.request):
            try:
                idps = api.keystone.identity_provider_list(self.request)
            except Exception:
                exceptions.handle(
                    self.request,
                    _('Unable to retrieve identity provider list.'))
        else:
            msg = _("Insufficient privilege level to view identity provider "
                    "information.")
            messages.info(self.request, msg)
        return idps


class UpdateView(forms.ModalFormView):
    template_name = 'identity/identity_providers/update.html'
    modal_header = _("Update Identity Provider")
    form_id = "update_identity_providers_form"
    form_class = idp_forms.UpdateIdPForm
    submit_label = _("Update Identity Provider")
    submit_url = "horizon:identity:identity_providers:update"
    success_url = reverse_lazy('horizon:identity:identity_providers:index')
    page_title = _("Update Identity Provider")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.keystone.identity_provider_get(
                self.request,
                self.kwargs['identity_provider_id'])
        except Exception:
            redirect = reverse("horizon:identity:identity_providers:index")
            exceptions.handle(self.request,
                              _('Unable to update identity provider.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        args = (self.get_object().id,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        idp = self.get_object()
        remote_ids = ', '.join(idp.remote_ids)
        return {'id': idp.id,
                'description': idp.description,
                'enabled': idp.enabled,
                'remote_ids': remote_ids}


class RegisterView(forms.ModalFormView):
    template_name = 'identity/identity_providers/register.html'
    modal_header = _("Register Identity Provider")
    form_id = "register_identity_provider_form"
    form_class = idp_forms.RegisterIdPForm
    submit_label = _("Register Identity Provider")
    submit_url = reverse_lazy("horizon:identity:identity_providers:register")
    success_url = reverse_lazy('horizon:identity:identity_providers:index')
    page_title = _("Register Identity Provider")
