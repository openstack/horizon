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

import logging

from horizon import forms

from openstack_dashboard.dashboards.idm_admin.notify \
    import forms as notify_forms

LOG = logging.getLogger('idm_logger')

class NotifyEmailView(forms.ModalFormView):
    form_class = notify_forms.EmailForm
    template_name = 'idm_admin/notify/index.html'