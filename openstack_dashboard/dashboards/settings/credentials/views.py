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

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from horizon import tables

from openstack_dashboard.dashboards.identity.credentials \
    import views as credential_views
from openstack_dashboard.dashboards.identity.users.tabs \
    import get_credentials
from openstack_dashboard.dashboards.settings.credentials \
    import forms as credential_forms
from openstack_dashboard.dashboards.settings.credentials \
    import tables as credential_tables


class CredentialsView(tables.DataTableView):
    table_class = credential_tables.CredentialsTable
    page_title = _("Credentials")
    policy_rules = (("identity", "identity:list_credentials"),)

    def get_data(self):
        user = self.request.user
        return get_credentials(self.request, user)


class UpdateView(credential_views.UpdateView):
    form_class = credential_forms.UpdateCredentialForm
    submit_url = "horizon:settings:credentials:update"
    success_url = reverse_lazy('horizon:settings:credentials:index')


class CreateView(credential_views.CreateView):
    form_class = credential_forms.CreateCredentialForm
    submit_url = reverse_lazy("horizon:settings:credentials:create")
    success_url = reverse_lazy('horizon:settings:credentials:index')
