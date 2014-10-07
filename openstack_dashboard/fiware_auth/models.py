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

import hashlib
import logging

from django.core.mail import send_mail
from django.db import models
from django.utils.translation import ugettext_lazy as _

from horizon import messages
from horizon import exceptions
from openstack_dashboard import api

LOG = logging.getLogger(__name__)

class RegistrationManager(models.Manager):

    def activate_user(self,request,activation_key):
        try:
            profile = self.get(activation_key=activation_key)
        except self.model.DoesNotExist:
            return False
        if not profile.activation_key_expired():
            user_id = profile.user_id
            #enable the user in the keystone backend
            user = api.keystone.user_get(request,user_id=user_id)
            api.keystone.user_update_enabled(request,user,enabled=True)
            api.keystone.tenant_update(request,user.project,enabled=True)
            profile.activation_key = self.model.ACTIVATED
            profile.save()
            messages.success(request,_('User "%s" was successfully activated.') % user.name)
            return user

	def create_profile(self, user):
		username = user.name
		if isinstance(username, unicode):
		    username = username.encode('utf-8')
		activation_key = hashlib.sha1(username).hexdigest()
		return self.create(user_id=user.id,
							user_name=username,
							user_email=user.email,
		                   activation_key=activation_key)

    def create_inactive_user(self,request,**cleaned_data):
        domain = api.keystone.get_default_domain(request)
        try:
            LOG.info('Creating user with name "%s"' % cleaned_data['username'])
            #if "email" in cleaned_data:
                #cleaned_data['email'] = cleaned_data['email'] or None
            default_tenant = api.keystone.tenant_create(name=cleaned_data['username'],
                                                        enabled=False)
            new_user = api.keystone.user_create(request,
                                                name=cleaned_data['username'],
                                                email=cleaned_data['email'],
                                                password=cleaned_data['password1'],
                                                project=default_tenant,
                                                enabled=False,
                                                domain=domain.id)

            messages.success(request,
                _('User "%s" was successfully created.') % cleaned_data['username'])

            registration_profile = self.create_profile(new_user)

            registration_profile.send_activation_email()

            return new_user
        except Exception:
            exceptions.handle(request, _('Unable to create user.'))

class RegistrationProfile(models.Model):
    """
    A simple profile which stores an activation key for use during
    user account registration. 
    """
    ACTIVATED = u"ALREADY_ACTIVATED"

    user_name = models.CharField(_('user name'),max_length=20)
    user_id = models.CharField(_('user id'),max_length=20)
    user_email = models.CharField(_('user email'), max_length=40)
    activation_key = models.CharField(_('activation key'), max_length=40)
    
    objects = RegistrationManager()
    
    def __unicode__(self):
        return u"Registration information for %s" % self.user_name
    
    def activation_key_expired(self):
    	#TODO
        return False

    def send_activation_email(self):
        subject = 'Welcome to FIWARE'
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        #TODO(garcianavalon) message...
        message = 'New user created at FIWARE :D/n Go to http://localhost:8000/activate/%s to activate' %self.activation_key
        #send a mail for activation
        send_mail(subject, message, 'admin@fiware-idm-test.dit.upm.es',
        	[self.user_email], fail_silently=False)