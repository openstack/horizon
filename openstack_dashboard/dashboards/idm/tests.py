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

from openstack_dashboard.test import helpers as test
from openstack_dashboard.test.test_data import utils
from keystoneclient.v3.contrib.oauth2 import consumers

class BaseTestCase(test.TestCase):
    """TestCase class for all test in the IdM dashboard to inherit. Contains
    utility methods and some wrappers to horizon's stuff to give it our flavour.
    """

    def setUp(self):
        super(BaseTestCase, self).setUp()
        # TODO(garcianavalon) fix the application fixtures
        # load_application_data(self)

    def list_organizations(self):
        return self._initialize_projects()

    def get_organization(self):
        project = self._initialize_projects()[0]
        setattr(project, 'img', '')
        setattr(project, 'city', '')
        setattr(project, 'email', '')
        setattr(project, 'website', '')
        return project

    def _initialize_projects(self):
        organizations = self.tenants.list()
        # NOTE(garcianavalon) self.tenants.list() is giving me a lazy loaded
        # list, hack initializaes the elements. 
        # TODO(garcianavalon) Find a better way to do this...
        for org in organizations:
            try:
                getattr(org, 'is_default', False)
            except Exception:
                pass
        return organizations


def load_application_data(TEST):
        """Return a list of application fixtures."""
        # TODO(garcianavalon) for the future, restructure this part
        TEST.applications = utils.TestDataContainer()
        app1 = {
            'id': '1',
            'name': 'user_app',
            'description': 'a user-owned application',
            'url' : 'http://url.test',
            'redirect_uris': ['http://redirect.uri'],
            'owner': TEST.user.id,
            'img': '/an/image.png'
        }
        app2 = {
            'id': '2',
            'name': 'other_user_app',
            'description': 'an application owned by other user',
            'url' : 'http://url.test',
            'redirect_uris': ['http://redirect.uri'],
            'owner': 'someone',
            'img': '/an/image.png'
        }
        user_app = consumers.Consumer(consumers.ConsumerManager, app1)
        other_app = consumers.Consumer(consumers.ConsumerManager, app2)
        TEST.applications.add(user_app. other_app)