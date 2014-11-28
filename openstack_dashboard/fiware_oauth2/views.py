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

import logging

from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from openstack_dashboard import fiware_api

LOG = logging.getLogger('idm_logger')

class AuthorizeView(TemplateView):
    """ Shows the user info about the application requesting authorization. If its the first
    time (the user has never authorized this application before)
    """
    template_name = 'oauth2/authorize.html'
    
    def get(self, request, *args, **kwargs):
        # TODO(garcianavalon) check is set to code
        response_type = request.GET.get('response_type')
        # forward the request to the keystone server to store the credentials
        self.form_data = fiware_api.keystone.request_authorization_for_application(
                                request,
                                request.GET.get('client_id'),
                                request.GET.get('redirect_uri'),
                                state=request.GET.get('state'))
        