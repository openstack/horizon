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

from django.utils.translation import gettext_lazy as _

from horizon import forms

from openstack_dashboard.dashboards.identity.credentials \
    import forms as credentials_forms


class CreateCredentialForm(credentials_forms.CreateCredentialForm):
    user_name = forms.CharField(label=_("User"), widget=forms.HiddenInput)
    failure_url = 'horizon:settings:credentials:index'

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        self.fields['user_name'].initial = request.user


class UpdateCredentialForm(credentials_forms.UpdateCredentialForm):
    user_name = forms.CharField(label=_("User"), widget=forms.HiddenInput)
    failure_url = 'horizon:settings:credentials:index'
