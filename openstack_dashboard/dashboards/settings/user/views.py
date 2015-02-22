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

from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon.utils import functions as utils
from openstack_dashboard.dashboards.settings.user import forms as user_forms


class UserSettingsView(forms.ModalFormView):
    form_class = user_forms.UserSettingsForm
    form_id = "user_settings_modal"
    modal_header = _("User Settings")
    modal_id = "user_settings_modal"
    page_title = _("User Settings")
    submit_label = _("Save")
    submit_url = reverse_lazy("horizon:settings:user:index")
    template_name = 'settings/user/settings.html'

    def get_initial(self):
        return {
            'language': self.request.session.get(
                settings.LANGUAGE_COOKIE_NAME,
                self.request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME,
                                         self.request.LANGUAGE_CODE)),
            'timezone': self.request.session.get(
                'django_timezone',
                self.request.COOKIES.get('django_timezone', 'UTC')),
            'pagesize': utils.get_page_size(self.request),
            'instance_log_length': utils.get_log_length(self.request)}

    def form_valid(self, form):
        return form.handle(self.request, form.cleaned_data)
