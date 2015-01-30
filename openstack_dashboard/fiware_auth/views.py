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
import datetime

from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from horizon import messages
from horizon import exceptions

from openstack_dashboard import fiware_api
from openstack_dashboard.fiware_auth import forms as fiware_forms
from openstack_dashboard.fiware_auth import models as fiware_models


LOG = logging.getLogger('idm_logger')

class _RequestPassingFormView(FormView):
    """
    A version of FormView which passes extra arguments to certain
    methods, notably passing the HTTP request nearly everywhere, to
    enable finer-grained processing.
    
    """

    def post(self, request, *args, **kwargs):
        # Pass request to get_form_class and get_form for per-request
        # form control.
        form_class = self.get_form_class(request)
        form = self.get_form(form_class)
        if form.is_valid():
            # Pass request to form_valid.
            return self.form_valid(request, form)
        else:
            return self.form_invalid(form)

    def get_form_class(self, request=None):
        return super(_RequestPassingFormView, self).get_form_class()

    def get_form_kwargs(self, request=None, form_class=None):
        return super(_RequestPassingFormView, self).get_form_kwargs()

    def get_initial(self, request=None):
        return super(_RequestPassingFormView, self).get_initial()

    def get_success_url(self, request=None, user=None):
        # We need to be able to use the request and the new user when
        # constructing success_url.
        return super(_RequestPassingFormView, self).get_success_url()

    def form_valid(self, form, request=None):
        return super(_RequestPassingFormView, self).form_valid(form)

    def form_invalid(self, form, request=None):
        return super(_RequestPassingFormView, self).form_invalid(form)


class RegistrationView(_RequestPassingFormView):
    """Creates a new user in the backend. Then redirects to the log-in page.
    Once registered, defines the URL where to redirect for activation
    """
    form_class = fiware_forms.RegistrationForm
    http_method_names = ['get', 'post', 'head', 'options', 'trace']
    success_url = reverse_lazy('login')
    template_name = 'auth/registration/registration.html'
    # TODO(garcianavalon) as settings
    EMAIL_HTML_TEMPLATE = 'email/base_email.html'
    EMAIL_TEXT_TEMPLATE = 'email/base_email.txt'

    def form_valid(self, request, form):
        new_user = self.register(request, **form.cleaned_data)
        if new_user:
            success_url = self.get_success_url(request, new_user)
            # success_url must be a simple string, no tuples
            return redirect(success_url)

    # We have to protect the entire "cleaned_data" dict because it contains the
    # password and confirm_password strings.
    def register(self, request, **cleaned_data):
        LOG.info('Singup user {0}.'.format(cleaned_data['username']))
        #delegate to the manager to create all the stuff
        try:
            # We use the keystoneclient directly here because the keystone api
            # reuses the request (and therefor the session). We make the normal rest-api
            # calls, using our own user for our portal
            new_user = fiware_api.keystone.register_user(
                name=cleaned_data['username'],
                email=cleaned_data['email'],
                password=cleaned_data['password1'])
            LOG.debug('User {0} was successfully created.'.format(cleaned_data['username']))
            self.send_activation_email(new_user)
            return new_user

        except Exception:
            msg = _('Unable to create user.')
            LOG.warning(msg)
            exceptions.handle(request, msg)

    def send_activation_email(self, user):
        # TODO(garcianavalon) subject, message and from_email as settings/files
        subject = 'Welcome to FIWARE'
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        content = 'New user created at FIWARE :D/n Go to http://localhost:8000/activate/?activation_key={0}&user={1} to activate'.format(user.activation_key, user.id)
        #send a mail for activation
        self.send_html_email(to=[user.email],
                             from_email='admin@fiware-idm-test.dit.upm.es',
                             subject=subject,
                             content=content)

    def send_html_email(self, to, from_email, subject, content):
        # TODO(garcianavalon) pass the context dict as param is better or use kwargs
        LOG.debug('Sending email to {0} with subject {1}'.format(to, subject))
        context = {
            'content':content
        }
        text_content = render_to_string(self.EMAIL_TEXT_TEMPLATE, context)
        html_content = render_to_string(self.EMAIL_HTML_TEMPLATE, context)
        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

class ActivationView(TemplateView):

    http_method_names = ['get']
    template_name = 'auth/activation/activate.html'
    success_url = reverse_lazy('login')
    ACTIVATED = u"ALREADY_ACTIVATED"

    def get(self, request, *args, **kwargs):
        activated_user = self.activate(request, *args, **kwargs)
        if activated_user:
            return redirect(self.success_url)
        return super(ActivationView, self).get(request, *args, **kwargs)

    def activate(self, request):
        activation_key = request.GET.get('activation_key')
        user = request.GET.get('user')
        LOG.info('Requested activation for key {0}.'.format(activation_key))
        try:
            activated_user = fiware_api.keystone.activate_user(user, activation_key)
            LOG.debug('User {0} was successfully activated.'.format(user.name))
            messages.success(request, _('User "%s" was successfully activated.') %user.name)
            return activated_user
        except Exception:
            msg = _('Unable to activate user.')
            LOG.warning(msg)
            exceptions.handle(request, msg)

class RequestPasswordResetView(_RequestPassingFormView):
    form_class = fiware_forms.EmailForm
    template_name = 'auth/password/request.html'
    success_url = reverse_lazy('login')

    def form_valid(self, request, form):
        self._create_reset_password_token(request, form.cleaned_data['email'])
        return super(RequestPasswordResetView, self).form_valid(form)

    def _create_reset_password_token(self, request, email):
        LOG.info('Creating reset token for {0}.'.format(email))
        #delegate to the manager
        fiware_models.ResetPasswordProfile.objects.create_reset_password_token(request, email)


class ResetPasswordView(_RequestPassingFormView):
    form_class = fiware_forms.ChangePasswordForm
    template_name = 'auth/password/reset.html'
    success_url = reverse_lazy('login')

    def get(self, request, *args, **kwargs):
        self.token = request.GET.get('reset_password_token')
        return super(ResetPasswordView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ResetPasswordView, self).get_context_data(**kwargs)
        context['token'] = self.token
        return context

    def form_valid(self, request, form):
        password = form.cleaned_data['password1']
        token = request.GET.get('reset_password_token')
        user = self._reset_password(request, token, password)
        if user:
            return super(ResetPasswordView, self).form_valid(form)
        return self.get(request) # redirect to itself

    def _reset_password(self, request, token, new_password):
        LOG.info('Reseting password for token {0}.'.format(token))
        #delegate to the manager
        user = fiware_models.ResetPasswordProfile.objects.reset_password(request, token, new_password)
        return user
    
class ResendConfirmationInstructionsView(_RequestPassingFormView):
    form_class = fiware_forms.EmailForm
    template_name = 'auth/registration/confirmation.html'
    success_url = reverse_lazy('login')

    def form_valid(self, request, form):
        self._resend_confirmation_email(request, form.cleaned_data['email'])
        return super(ResendConfirmationInstructionsView, self).form_valid(form)

    def _resend_confirmation_email(self, request, email):
        LOG.info('Resending confirmation instructions to {0}.'.format(email))
        #delegate to the manager
        fiware_models.RegistrationProfile.objects.resend_email(request, email)