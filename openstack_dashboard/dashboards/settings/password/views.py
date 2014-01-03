# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from horizon import forms

from django.core.urlresolvers import reverse_lazy

from openstack_dashboard.dashboards.settings.password \
    import forms as pass_forms


class PasswordView(forms.ModalFormView):
    form_class = pass_forms.PasswordForm
    template_name = 'settings/password/change.html'
    success_url = reverse_lazy('logout')
