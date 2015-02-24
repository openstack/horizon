# Copyright (C) 2014 Universidad Politecnica de Madrid
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.core import urlresolvers
from horizon import tables

class ClickableRow(tables.Row):
	"""This row handles the logic to make items clickables. 
	Usually link to item details.
	"""
	clickable = True
	base_url = ''

	def get_url(self):
		return self.base_url

class OrganizationClickableRow(ClickableRow):
	base_url = 'horizon:idm:organizations:detail'

	def get_url(self):
		return urlresolvers.reverse(self.base_url,
			                 		kwargs={'organization_id':self.datum.id})

class ApplicationClickableRow(ClickableRow):
	base_url = 'horizon:idm:myApplications:detail'

	def get_url(self):
		return urlresolvers.reverse(self.base_url,
			                 		kwargs={'application_id':self.datum.id})

class UserClickableRow(ClickableRow):
	base_url = 'horizon:idm:users:detail'

	def get_url(self):
		return urlresolvers.reverse(self.base_url,
			                 		kwargs={'user_id':self.datum.id})