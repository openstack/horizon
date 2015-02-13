# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from horizon import forms
from openstack_dashboard import api
from openstack_dashboard.dashboards.settings.useremail import forms as useremail_forms


class EmailView(forms.ModalFormView):

    form_class = useremail_forms.EmailForm
    template_name = 'settings/useremail/change.html'

    def get_form_kwargs(self):
        kwargs = super(EmailView, self).get_form_kwargs()
        user_id = self.request.user.id
        user = api.keystone.user_get(self.request, user_id, admin=False)
        kwargs['initial']['email'] = getattr(user, 'email', '')
        return kwargs

