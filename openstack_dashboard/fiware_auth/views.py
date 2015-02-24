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

from django import http
from django.conf import settings
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from horizon import messages
from horizon import exceptions

from openstack_dashboard import fiware_api
from openstack_dashboard.fiware_auth import forms as fiware_forms

from keystoneclient import base

LOG = logging.getLogger('idm_logger')

class TemplatedEmailMixin(object):
    # TODO(garcianavalon) as settings
    EMAIL_HTML_TEMPLATE = 'email/base_email.html'
    EMAIL_TEXT_TEMPLATE = 'email/base_email.txt'
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

class _RequestPassingFormView(FormView, TemplatedEmailMixin):
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

    def dispatch(self, request, *args, **kwargs):
        if request.user.username:
            return redirect("/idm/")
        return super(RegistrationView, self).dispatch(request, *args, **kwargs)
    
    def form_valid(self, request, form):
        new_user = self.register(request, **form.cleaned_data)
        if new_user:
            success_url = self.get_success_url(request, new_user)
            # success_url must be a simple string, no tuples
            return redirect(success_url)
        # TODO(garcianavalon) do something if new_user is None like
        # redirect to login or to sign_up

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
                name=cleaned_data['email'],
                password=cleaned_data['password1'],
                username=cleaned_data['username'])
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
        self.send_html_email(to=[user.name],
                             from_email='admin@fiware-idm-test.dit.upm.es',
                             subject=subject,
                             content=content)

class ActivationView(TemplateView):

    http_method_names = ['get']
    template_name = 'auth/activation/activate.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.username:
            return redirect("/idm/")
        return super(ActivationView, self).dispatch(request, *args, **kwargs)

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
            LOG.debug('User {0} was successfully activated.'.format(activated_user.username))
            messages.success(request, _('User "%s" was successfully activated.') %activated_user.username)
            return activated_user
        except Exception:
            msg = _('Unable to activate user.')
            LOG.warning(msg)
            exceptions.handle(request, msg)

class RequestPasswordResetView(_RequestPassingFormView):
    form_class = fiware_forms.EmailForm
    template_name = 'auth/password/request.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.username:
            return redirect("/idm/")
        return super(RequestPasswordResetView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, request, form):
        self._create_reset_password_token(request, form.cleaned_data['email'])
        return super(RequestPasswordResetView, self).form_valid(form)

    def _create_reset_password_token(self, request, email):
        LOG.info('Creating reset token for {0}.'.format(email))
        user = fiware_api.keystone.check_email(email)
        if user:
            reset_password_token = fiware_api.keystone.get_reset_token(user)
            token = base.getid(reset_password_token)
            self.send_reset_email(email, token)
            messages.success(request, _('Reset mail send to %s') % email)
        else:
            messages.error(request, _('No email %s registered') % email)

    def send_reset_email(self, email, token):
        # TODO(garcianavalon) subject, message and from_email as settings/files
        subject = 'Reset password instructions - FIWARE'
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        content = 'Hello! Go to http://localhost:8000/password/reset/?token={0}&email={1} to reset it!'.format(token, email)
        #send a mail for activation
        self.send_html_email(to=[email], 
                            from_email='admin@fiware-idm-test.dit.upm.es',
                            subject=subject, 
                            content=content)


class ResetPasswordView(_RequestPassingFormView):
    form_class = fiware_forms.ChangePasswordForm
    template_name = 'auth/password/reset.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.username:
            return redirect("/idm/")
        self.token = request.GET.get('token')
        self.email = request.GET.get('email')
        return super(ResetPasswordView, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(ResetPasswordView, self).get_context_data(**kwargs)
        context['token'] = self.token
        context['email'] = self.email
        return context

    def form_valid(self, request, form):
        password = form.cleaned_data['password1']
        token = self.token
        user = self._reset_password(request, token, password)
        if user:
            return super(ResetPasswordView, self).form_valid(form)
        return self.get(request) # redirect to itself

    def _reset_password(self, request, token, password):
        LOG.info('Reseting password for token {0}.'.format(token))
        user_email = self.email
        user = fiware_api.keystone.check_email(user_email)
        try:
            user = fiware_api.keystone.reset_password(user, token, password)
            if user:
                messages.success(request, _('password successfully changed.'))
                return user
        except Exception:
            msg = _('Unable to change password.')
            LOG.warning(msg)
            exceptions.handle(request, msg)

class ResendConfirmationInstructionsView(_RequestPassingFormView):
    form_class = fiware_forms.EmailForm
    template_name = 'auth/registration/confirmation.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.username:
            return redirect("/idm/")
        return super(ResendConfirmationInstructionsView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, request, form):
        self._resend_confirmation_email(request, form.cleaned_data['email'])
        return super(ResendConfirmationInstructionsView, self).form_valid(form)

    def _resend_confirmation_email(self, request, email):
        user = fiware_api.keystone.check_email(email)
        if not user:
            LOG.debug('The email address {0} is not registered'.format(email))
            msg = _('Sorry. You have specified an email address that is not registered \
                 to any our our user accounts. If your problem persits, please contact: \
                 fiware-lab-help@lists.fi-ware.org')
            messages.error(request, msg)
            return False

        if user.enabled:
            msg = _('Email was already confirmed, please try signing in')
            LOG.debug('The email address {0} was already confirmed'.format(email))
            messages.error(request, msg)
            return False

        activation_key = fiware_api.keystone.new_activation_key(user)

        self.send_reactivation_email(user, activation_key)
        msg = _('Resended confirmation instructions to %s') %email
        messages.success(request, msg)
        return True

    def send_reactivation_email(self, user, activation_key):
        # TODO(garcianavalon) subject, message and from_email as settings/files
        subject = 'Welcome to FIWARE'
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        content = 'New user created at FIWARE :D/n Go to http://localhost:8000/activate/?activation_key={0}&user={1} to activate'.format(base.getid(activation_key), user.id)
        #send a mail for activation
        self.send_html_email(to=[user.name],
                             from_email='admin@fiware-idm-test.dit.upm.es',
                             subject=subject,
                             content=content)