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

from openstack_auth import utils
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from forms import RegistrationForm

try:
	is_safe_url = http.is_safe_url
except AttributeError:
	is_safe_url = utils.is_safe_url

LOG = logging.getLogger(__name__)

class RegistrationView(FormView):
	"""Creates a new user in the backend. Then redirects to the log-in page.
	.. param:: login_url
	Once registered, defines the URL where to redirect for login
	"""
	form_class = RegistrationForm
	http_method_names = ['get', 'post', 'head', 'options', 'trace']
	success_url = None
	template_name = 'registration/registration_form.html'

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

	def register(self, request, **cleaned_data):

		msg = 'Singup user "%(username)s".' % {'username': request.user.username}
		LOG.info(msg)
		#Load the form data
		username, email, password = cleaned_data['username'], cleaned_data['email'], cleaned_data['password1']
		#Load keystone stuff
		endpoint = request.session.get('region_endpoint')
		token = request.session.get('token')
		#create the user
		#User.objects.create_user(username, email, password)
		new_user = authenticate(username=username, password=password)
		#login(request, new_user)

		signals.user_registered.send(sender=self.__class__,
		                             user=new_user,
		                             request=request)
		return new_user

                

