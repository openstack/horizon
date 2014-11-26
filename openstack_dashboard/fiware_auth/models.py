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

import datetime
import logging
import uuid

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from horizon import messages
from horizon import exceptions

from openstack_dashboard import fiware_api


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


class ModelWithTimeStamps(models.Model):
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        return super(ModelWithTimeStamps, self).save(*args, **kwargs)


class RegistrationManager(models.Manager):

    def activate_user(self, request, activation_key):
        try:
            profile = self.get(activation_key=activation_key)
        except self.model.DoesNotExist:
            LOG.debug('The activation key {0} doesn\'t exist'.format(activation_key))
            return False
        if not profile.activation_key_expired():
            
            #enable the user in the keystone backend
            user = fiware_api.keystone.activate_user(profile.user_id)
            if user:
                profile.activation_key = self.model.ACTIVATED
                profile.save()
                LOG.debug('User {0} was successfully activated.'.format(user.name))
                #messages.success(request, _('User "%s" was successfully activated.') %user.name)
                return user

    def create_profile(self, user):
        activation_key = uuid.uuid4().get_hex()
        return self.create(user_id=user.id,
                           user_name=user.name,
                           user_email=user.email,
                           activation_key=activation_key)

    def create_inactive_user(self, request, **cleaned_data):
        try:
            # We use the keystoneclient directly here because the keystone api
            # reuses the request (and therefor the session). We make the normal rest-api
            # calls, using our own user for our portal
            
            new_user = fiware_api.keystone.register_user(
                                        name=cleaned_data['username'],
                                        email=cleaned_data['email'],
                                        password=cleaned_data['password1'])
            registration_profile = self.create_profile(new_user)
            registration_profile.send_activation_email()
            LOG.debug('User {0} was successfully created.'.format(cleaned_data['username']))
            return new_user

        except Exception:
            msg = _('Unable to create user.')
            LOG.warning(msg)
            exceptions.handle(request, msg)

    def resend_email(self, request, email):
        try:
            profile = self.get(user_email=email)
        except self.model.DoesNotExist:
            LOG.debug('The email address {0} is not registered'.format(email))
            msg = _('Sorry. You have specified an email address that is not registered \
                 to any our our user accounts. If your problem persits, please contact: \
                 fiware-lab-help@lists.fi-ware.org')
            messages.error(request, msg)
            return False

        if profile.activation_key == self.model.ACTIVATED:
            msg = _('Email was already confirmed, please try signing in')
            LOG.debug('The email address {0} was already confirmed'.format(email))
            messages.error(request, msg)
            return False

        # generate a new key and send
        profile.activation_key = uuid.uuid4().get_hex()
        profile.save()

        profile.send_activation_email()

        msg = _('Resended confirmation instructions to %s') %email
        messages.success(request, msg)
        return True


class RegistrationProfile(ModelWithTimeStamps, TemplatedEmailMixin):
    """
    A simple profile which stores an activation key for use during
    user account registration. 
    """
    ACTIVATED = u"ALREADY_ACTIVATED"

    user_name = models.CharField(_('user name'), max_length=20)
    user_id = models.CharField(_('user id'), max_length=20)
    user_email = models.CharField(_('user email'), max_length=40)
    activation_key = models.CharField(_('activation key'), max_length=40)
    
    objects = RegistrationManager()
    
    def __unicode__(self):
        return u"Registration information for %s" % self.user_name
    
    def activation_key_expired(self):
        if self.activation_key == self.ACTIVATED:
            return True
        base_date = max([self.created, self.updated]) 
    	expiration_date = datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return base_date + expiration_date <= timezone.now()

    def send_activation_email(self):
        # TODO(garcianavalon) subject, message and from_email as settings/files
        subject = 'Welcome to FIWARE'
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        content = 'New user created at FIWARE :D/n Go to http://localhost:8000/activate/?activation_key=%s to activate' %self.activation_key
        #send a mail for activation
        self.send_html_email(to=[self.user_email], 
                            from_email='admin@fiware-idm-test.dit.upm.es',
                            subject=subject, 
                            content=content)


class ResetPasswordManager(models.Manager):

    def create_profile(self, email):
        reset_password_token = uuid.uuid4().get_hex()
        return self.create(reset_password_token=reset_password_token,
                            user_email=email)

    def create_reset_password_token(self, request, email):

        registration_profile = self.create_profile(email)
        registration_profile.send_reset_email(email)

        messages.success(request, _('Reset mail send to %s') % email)

    def reset_password(self, request, token, new_password):
        try:
            profile = self.get(reset_password_token=token)
        except self.model.DoesNotExist:
            LOG.debug('Reset password token {0} is invalid'.format(token))
            messages.error(request, _('Reset password token is invalid'))
            return None

        if not profile.reset_password_token_expired():
            user_email = profile.user_email
            #change the user password in the keystone backend
            user = fiware_api.keystone.change_password(user_email, new_password)
            if user:
                profile.reset_password_token = self.model.USED
                profile.save()
                messages.success(request, _('password successfully changed.'))
                return user


class ResetPasswordProfile(ModelWithTimeStamps, TemplatedEmailMixin):
    """Holds the key to reset the user password"""

    reset_password_token = models.CharField(_('reset password token'), max_length=40)
    user_email = models.CharField(_('user email'), max_length=40)
    USED = u"ALREADY_USED"

    objects = ResetPasswordManager()

    def send_reset_email(self, email):
        # TODO(garcianavalon) subject, message and from_email as settings/files
        subject = 'Reset password instructions - FIWARE'
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        content = 'Hello! Go to http://localhost:8000/password/reset/?reset_password_token=%s to reset it!' %self.reset_password_token
        #send a mail for activation
        self.send_html_email(to=[email], 
                            from_email='admin@fiware-idm-test.dit.upm.es',
                            subject=subject, 
                            content=content)

    def reset_password_token_expired(self):
        if self.reset_password_token == self.USED:
            return True
        base_date = max([self.created, self.updated]) 
        expiration_date = datetime.timedelta(days=settings.RESET_PASSWORD_DAYS)
        return base_date + expiration_date <= timezone.now()