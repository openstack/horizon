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

from django import forms

from django_summernote.widgets import SummernoteWidget

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
# TODO(garcianavalon) centralize email sending
from openstack_dashboard.fiware_auth.views import TemplatedEmailMixin


LOG = logging.getLogger('idm_logger')

class EmailForm(forms.SelfHandlingForm, TemplatedEmailMixin):
    subject = forms.CharField(max_length=50,
                                label=("Subject"),
                                required=True)
    body = forms.CharField(widget=SummernoteWidget(),
                                label=("Body"),
                                required=True)

    def handle(self, request, data):
        try:
            to = [u.email for u in api.keystone.user_list(request)
                if hasattr(u, 'email')]
            self.send_html_email(
                to, 
                ' no-reply@account.lab.fi-ware.org', 
                data['subject'], 
                data['body'])
            messages.success(request, ('Message sent succesfully.'))
        except Exception:
            msg = ('Unable to send message. Please try again later.')
            LOG.warning(msg)
            exceptions.handle(request, msg)