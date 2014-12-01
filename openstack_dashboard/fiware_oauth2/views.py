# Copyright (C) 2014 Universidad Politecnica de Madrid
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

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic.edit import FormView

from openstack_auth import views as auth_views
from openstack_dashboard import fiware_api
from openstack_dashboard.fiware_oauth2 import forms

LOG = logging.getLogger('idm_logger')

# HPCM
# Client ID
# b5652024cfe54a41909692892dfca345
# Client Secret
# b0ab404b1314411293911a68661c49d8
# authorize/?response_type=code&client_id=b5652024cfe54a41909692892dfca345&state=xyz&redirect_uri=https%3A%2F%2Flocalhost%2Flogin
# LOCALHOST
# Client ID
# 009e60a5d785415fbd3cef3a3b7b2d35
# Client Secret
# 0508b01b7d0748b19f306f72ca25c42e
# authorize/?response_type=code&client_id=009e60a5d785415fbd3cef3a3b7b2d35&state=xyz&redirect_uri=https%3A%2F%2Flocalhost%2Flogin
class AuthorizeView(FormView):
    """ Shows the user info about the application requesting authorization. If its the first
    time (the user has never authorized this application before)
    """
    template_name = 'oauth2/authorize.html'
    form_class = forms.AuthorizeForm
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if not request.session.get('requesting_application', None):
                self._request_authorization(request)
            return super(AuthorizeView, self).dispatch(request, *args, **kwargs)
        else:
            # login logic
            context = self._request_authorization(request)
            return auth_views.login(request, 
                                extra_context=context, 
                                **kwargs)

    def _request_authorization(self, request):
        # TODO(garcianavalon) check it's set to code
        response_type = request.GET.get('response_type')
        # forward the request to the keystone server to store the credentials
        try:
            # register consumer credentials
            self.oauth_data = fiware_api.keystone.request_authorization_for_application(
                                request,
                                request.GET.get('client_id'),
                                request.GET.get('redirect_uri'),
                                state=request.GET.get('state'))
            request.session['requesting_application'] = self.oauth_data['data']['consumer']['id']
        except Exception as e:
            # TODO(garcianavalon) finner exception handling
            self.oauth_data = {
                'error': e
            }
        context = {
            'data':self.oauth_data.get('data'),
            'error':self.oauth_data.get('error'),
            'next':reverse('fiware_oauth2_authorize'),
            'show_consumer_details':True,
        }
        return context

    def get(self, request, *args, **kwargs):
        application_id = request.session.get('requesting_application', None)
        if application_id:
            self.consumer = fiware_api.keystone.application_get(request, application_id)
            return super(AuthorizeView, self).get(request, *args, **kwargs)
        else:
            # there is no pending authorization request, redirect to index
            return redirect('horizon:user_home')

    def get_context_data(self, **kwargs):
        context = super(AuthorizeView, self).get_context_data(**kwargs)
        context['consumer'] = getattr(self, 'consumer', None)
        return context

    def post(self, request, *args, **kwargs):
        # Pass request to get_form for per-request
        # form control.
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            # Pass request to form_valid.
            return self.form_valid(request, form)
        else:
            return self.form_invalid(form)

    def form_valid(self, request, form):
        import pdb; pdb.set_trace()
        authorization_code = fiware_api.keystone.authorize_application(
            request,
            application=request.session.pop('requesting_application'))
        # TODO(garcianavalon) logic to send the authorization code to the application
        import pdb; pdb.set_trace()
        

def cancel_authorize(request, **kwargs):
    # make sure we clear the session variable
    request.session['requesting_application'] = None
    return redirect('horizon:user_home')

