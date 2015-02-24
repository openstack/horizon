# Copyright 2013 Centrin Data Systems Ltd.
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

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import forms

from openstack_dashboard.dashboards.settings.password \
    import forms as pass_forms


class PasswordView(forms.ModalFormView):
    form_class = pass_forms.PasswordForm
    form_id = "change_password_modal"
    modal_header = _("Change Password")
    modal_id = "change_password_modal"
    page_title = _("Change Password")
    submit_label = _("Change")
    submit_url = reverse_lazy("horizon:settings:password:index")
    template_name = 'settings/password/change.html'
