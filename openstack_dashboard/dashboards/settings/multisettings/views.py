# Copyright (C) 2014 Universidad Politecnica de Madrid
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

import logging

from horizon import views

from openstack_dashboard import api
from openstack_dashboard.dashboards.settings.cancelaccount import forms \
                                                            as cancelaccount_forms
from openstack_dashboard.dashboards.settings.password import forms as password_forms
from openstack_dashboard.dashboards.settings.useremail import forms as useremail_forms


LOG = logging.getLogger('idm_logger')

class MultiFormView(views.APIView):
    template_name = 'settings/multisettings/index.html'
    
    def get_context_data(self, **kwargs):
        context = super(MultiFormView, self).get_context_data(**kwargs)

        # Initial data
        user_id = self.request.user.id
        user = api.keystone.user_get(self.request, user_id, admin=False)
        email = getattr(user, 'name', '') 
        initial_email = {
            'email': email
        }
        
        #Create forms
        cancel = cancelaccount_forms.BasicCancelForm(self.request)
        password = password_forms.PasswordForm(self.request)
        email = useremail_forms.EmailForm(self.request, initial=initial_email)

        #Actions and titles
        # TODO(garcianavalon) quizas es mejor meterlo en el __init__ del form
        email.action = 'useremail/'
        password.action = "password/"
        cancel.action = "cancelaccount/"
        email.description = ('Change your email')
        password.description = ('Change your password')
        cancel.description = ('Cancel account')

        context['forms'] = [password, email, cancel]
        return context
