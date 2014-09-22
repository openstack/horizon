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
import django
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required # noqa
from django.contrib.auth import views as django_auth_views
from django import shortcuts
from django.utils import functional
from django.utils import http
from django.views.decorators.cache import never_cache # noqa
from django.views.decorators.csrf import csrf_protect # noqa
from django.views.decorators.debug import sensitive_post_parameters # noqa
from keystoneclient import exceptions as keystone_exceptions
from keystoneclient.v2_0 import client as keystone_client_v2

from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from forms import RegistrationForm

from django.forms import ValidationError  # noqa
from django import http
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import validators

from openstack_dashboard import api

LOG = logging.getLogger(__name__)

class RegistrationView(FormView):
	"""Creates a new user in the backend. Then redirects to the log-in page.
	.. param:: login_url
	Once registered, defines the URL where to redirect for login
	"""
	form_class = RegistrationForm
	http_method_names = ['get', 'post', 'head', 'options', 'trace']
	success_url = '/' #TODO'
	template_name = 'auth/registration_form.html'

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
		return super(RegistrationView, self).get_form_class()
 	def get_success_url(self, request=None, user=None):
		# We need to be able to use the request and the new user when
		# constructing success_url.
		return super(RegistrationView, self).get_success_url()				
	def form_valid(self, request, form):
		new_user = self.register(request, **form.cleaned_data)
		success_url = self.get_success_url(request, new_user)

		# success_url may be a simple string, or a tuple providing the
		# full argument set for redirect(). Attempting to unpack it
		# tells us which one it is.
		try:
			#redirect to login page
		    to, args, kwargs = success_url
		    return redirect(to, *args, **kwargs)
		except ValueError:
		    return redirect(success_url)

	# We have to protect the entire "cleaned_data" dict because it contains the
    # password and confirm_password strings.
	
	def register(self, request, **cleaned_data):
		msg = 'Singup user "%(username)s".' % {'username': request.user.username}
		LOG.info(msg)
		#create the user
		domain = api.keystone.get_default_domain(self.request)
		try:
			LOG.info('Creating user with name "%s"' % cleaned_data['username'])
			if "email" in cleaned_data:
				cleaned_data['email'] = cleaned_data['email'] or None
			new_user = api.keystone.user_create(request,
												name=cleaned_data['username'],
												email=cleaned_data['email'],
												password=cleaned_data['password1'],
												project=None,
												enabled=True,
												domain=domain.id)
			messages.success(request,
				_('User "%s" was successfully created.') % cleaned_data['username'])
			return new_user
		except Exception:
			exceptions.handle(request, _('Unable to create user.'))
                

