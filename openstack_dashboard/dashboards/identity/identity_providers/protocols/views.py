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
from django.utils.translation import ugettext_lazy as _

from horizon import forms

from openstack_dashboard.dashboards.identity.identity_providers.protocols \
    import forms as protocol_forms


class AddProtocolView(forms.ModalFormView):
    template_name = 'identity/identity_providers/protocols/create.html'
    modal_header = _("Create Protocol")
    form_id = "create_protocol_form"
    form_class = protocol_forms.AddProtocolForm
    submit_label = _("Create Protocol")
    success_url = "horizon:identity:identity_providers:protocols_tab"
    page_title = _("Create Protocol")

    def __init__(self):
        super(AddProtocolView, self).__init__()

    def get_success_url(self):
        return reverse(self.success_url,
                       args=(self.kwargs['identity_provider_id'],))

    def get_context_data(self, **kwargs):
        context = super(AddProtocolView, self).get_context_data(**kwargs)
        context["submit_url"] = reverse(
            "horizon:identity:identity_providers:protocols:create",
            args=(self.kwargs['identity_provider_id'],))
        return context

    def get_initial(self):
        return {"idp_id": self.kwargs['identity_provider_id']}
