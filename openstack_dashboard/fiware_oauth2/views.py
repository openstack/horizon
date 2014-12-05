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

from django.contrib import auth
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.views.generic.edit import FormView

from openstack_auth import views as auth_views
from openstack_dashboard import fiware_api
from openstack_dashboard.fiware_oauth2 import forms


LOG = logging.getLogger('idm_logger')

class AuthorizeView(FormView):
    """ Shows the user info about the application requesting authorization. If its the first
    time (the user has never authorized this application before)
    """
    template_name = 'oauth2/authorize.html'
    form_class = forms.AuthorizeForm
    application_credentials = {}
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
            LOG.debug('OAUTH2: Login page with consumer details')
            # redirect to the login page but showing some info about the application
            context = {
                'next':reverse('fiware_oauth2_authorize'),
                'redirect_field_name': auth.REDIRECT_FIELD_NAME,
                'show_application_details':True,
                'application':fiware_api.keystone.application_get(request,
                                    self.application_credentials['application_id'],
                                    use_idm_account=True),
            }
            return auth_views.login(request, 
                                extra_context=context, 
                                **kwargs)

    def _store_credentials(self, request):
        LOG.debug('OAUTH2: Storing credentials in session')
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
            LOG.warning('OAUTH2: exception when requesting authorization {0}'.format(e))
            # TODO(garcianavalon) finner exception handling
            self.oauth_data = {
                'error': e
            }

    def _already_authorized(self, request, credentials):
        # check if the user already authorized the app for that redirect uri
        # FIXME(garcianvalon) the api and keystoneclient layers are not ready yet
        return False
        try:
            fiware_api.keystone.check_authorization_for_application(request,
                                                credentials.get('application_id'),
                                                credentials.get('redirect_uri'))
        except Exception as e:
             LOG.warning('OAUTH2: exception when checking if already authorized {0}'.format(e))
            # TODO(garcianavalon) finner exception handling

    def get(self, request, *args, **kwargs):
        """Show a form with info about the scopes and the application to the user"""
        if self.application_credentials:
            # check if user already authorized this app
            if self._already_authorized(request, self.application_credentials):
                return redirect()
            # if not, request authorization
            self._request_authorization(request, self.application_credentials)
            return super(AuthorizeView, self).get(request, *args, **kwargs)
        else:
            LOG.debug('OAUTH2: there is no pending authorization request, redirect to index')
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
        authorization_code = fiware_api.keystone.authorize_application(request,
                        application=self.application_credentials['application_id'])
        LOG.debug('OAUTH2: Authorization Code obtained {0}'.format(authorization_code.code))
        # redirect resource owner to client with the authorization code
        LOG.debug('OAUTH2: Redirecting user back to {0}'.format(authorization_code.redirect_uri))
        return redirect(authorization_code.redirect_uri, permanent=True)

    def form_invalid(self, form):
        # NOTE(garcianavalon) there is no case right now where this form would be
        # invalid, because is an empty form. In the future we might use a more complex
        # form (multiple choice scopes for example)
        pass
        

def cancel_authorize(request, **kwargs):
    # make sure we clear the session variables
    LOG.debug('OAUTH2: authorization request dennied, clear variables and redirect to home')
    request.session['application_credentials'] = None
    return redirect('horizon:user_home')


class AccessTokenView(View):
    """ Handles the access token request form the clients (applications). Forwards the 
    request to the Keystone backend.
    """
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(AccessTokenView, self).dispatch(request, *args, **kwargs)
   
    def post(self, request, *args, **kwargs):
        # NOTE(garcianavalon) Instead of using the client we simply redirect the request 
        # because is simpler than extracting all the data to make the exact same request 
        # again from it
        LOG.debug('OAUTH2: forwading the access_token request')
        response = fiware_api.keystone.forward_access_token_request(request)
        return HttpResponse(content=response.content, 
                            content_type=response.headers['content-type'], 
                            status=response.status_code, 
                            reason=response.reason)

class UserInfoView(View):
    """ Forwards to the Keystone backend the validate token request (access the user info).
    """

    def get(self, request, *args, **kwargs):
        # NOTE(garcianavalon) Instead of using the client we simply redirect the request 
        # because is simpler than extracting all the data to make the exact same request 
        # again from it
        LOG.debug('OAUTH2: forwading the user info (validate token) request')
        response = fiware_api.keystone.forward_validate_token_request(request)
        return HttpResponse(content=response.content, 
                            content_type=response.headers['content-type'], 
                            status=response.status_code, 
                            reason=response.reason)