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

from mox import IgnoreArg
from mox import IsA  # noqa

from django import http
from django.contrib import auth as django_auth
from django.core.urlresolvers import reverse

from openstack_auth import exceptions as auth_exceptions
from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

CREATE_URL = reverse('horizon:idm:myApplications:create')


class ApplicationsTests(test.TestCase):

	def _get_application_info(self, application):
		extra = {"url": IsA(str),
				 "img": IsA(str),}

		application_info = {"name": unicode(application.name),
							"description": unicode(application.description),
							"redirect_uris": unicode(application.redirect_uris[0]),
							"extra": extra}
		return application_info

	# We have to create the application, 'self' does not include this field
	# @test.create_stubs({api.keystone: ('application_create',)})
	# def test_create_app(self):
	# 	application = 
	# 	application_details = self._get_application_info(application)

	# 	fiware_api.keystone.application_create(IsA(http.HttpRequest), **application_details) \
	# 	    .AndReturn(application)
	
	# 	self.mox.ReplayAll()

	# 	form_data = {
	# 		'method': 'CreateAppicationForm',
	# 		'name': application._info["name"],
	# 		'description': application._info["description"],
	# 		'redirect_uris': application._info["redirect_uris"],
	# 		'url': 'url'
 #        }

	# 	response = self.client.post(CREATE_URL, form_data)
	# 	self.assertNoFormErrors(response)
