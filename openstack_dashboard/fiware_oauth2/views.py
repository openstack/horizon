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

from django.core.urlresolvers import reverse_lazy, reverse
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
    application_credentials = {}
    application = None
    success_url = reverse_lazy('horizon:user_home')
    oauth_data = {}

    def dispatch(self, request, *args, **kwargs):     
        self.application_credentials = request.session.get('application_credentials', {})
        # save the credentials in case we have to redirect
        if not self.application_credentials:
            self._store_credentials(request)

        if request.user.is_authenticated():
            return super(AuthorizeView, self).dispatch(request, *args, **kwargs)
        else:
            # redirect to the login page but showing some info about the application
            context = {
                'next':reverse('fiware_oauth2_authorize'),
                'show_consumer_details':True,
                'application':'TODO(garcianvalon)',
            }
            return auth_views.login(request, 
                                extra_context=context, 
                                **kwargs)

    def _store_credentials(self, request):
        # TODO(garcianavalon) check it's set to code
        self.application_credentials = {     
            'response_type':request.GET.get('response_type'),
            'application_id':request.GET.get('client_id'),
            'redirect_uri':request.GET.get('redirect_uri'),
            'state':request.GET.get('state'),
        }
        request.session['application_credentials'] = self.application_credentials

    def _request_authorization(self, request, credentials):
        # forward the request to the keystone server to store the credentials
        try:
            # register consumer credentials
            self.oauth_data = fiware_api.keystone.request_authorization_for_application(
                                request,
                                credentials.get('application_id'),
                                credentials.get('redirect_uri'),
                                state=credentials.get('state', None))
        except Exception as e:
            # TODO(garcianavalon) finner exception handling
            self.oauth_data = {
                'error': e
            }

    def get(self, request, *args, **kwargs):
        """Show a form with info about the scopes and the application to the user"""
        if self.application_credentials:
            self._request_authorization(request, self.application_credentials)
            return super(AuthorizeView, self).get(request, *args, **kwargs)
        else:
            # there is no pending authorization request, redirect to index
            return redirect('horizon:user_home')

    def get_context_data(self, **kwargs):
        context = super(AuthorizeView, self).get_context_data(**kwargs)
        context['oauth_data'] = self.oauth_data
        context['application_credentials'] = self.application_credentials
        return context

    def post(self, request, *args, **kwargs):
        # Pass request to get_form
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            # Pass request to form_valid.
            return self.form_valid(request, form)
        else:
            return self.form_invalid(form)

    def form_valid(self, request, form):
        authorization_code = fiware_api.keystone.authorize_application(
             request,
            application=self.application_credentials['application_id'])
        # TODO(garcianavalon) logic to send the authorization code to the application
        
        return super(AuthorizeView, self).form_valid(form)

    def form_invalid(self, form):
        # NOTE(garcianavalon) there is no case right now where this form would be
        # invalid, because is an empty form. In the future we might use a more complex
        # form (multiple choice scopes for example)
        pass
        

def cancel_authorize(request, **kwargs):
    # make sure we clear the session variables
    request.session['application_credentials'] = None
    return redirect('horizon:user_home')