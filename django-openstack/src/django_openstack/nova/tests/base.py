# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Base classes for view based unit tests.
"""

import mox
import nova_adminclient as adminclient

from django import test
from django.conf import settings
from django.contrib.auth import models as auth_models
from django_openstack.nova import manager
from django_openstack.nova import shortcuts


TEST_PROJECT = 'test'
TEST_USER = 'test'
TEST_REGION = 'test'


class BaseViewTests(test.TestCase):
    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def assertRedirectsNoFollow(self, response, expected_url):
        self.assertEqual(response._headers['location'],
                         ('Location', settings.TESTSERVER + expected_url))
        self.assertEqual(response.status_code, 302)

    def authenticateTestUser(self):
        user = auth_models.User.objects.create_user(TEST_USER,
                                                         'test@test.com',
                                                         password='test')
        login = self.client.login(username=TEST_USER, password='test')
        self.failUnless(login, 'Unable to login')
        return user


class BaseProjectViewTests(BaseViewTests):
    def setUp(self):
        super(BaseProjectViewTests, self).setUp()

        project = adminclient.ProjectInfo()
        project.projectname = TEST_PROJECT
        project.projectManagerId = TEST_USER

        self.user = self.authenticateTestUser()
        self.region = adminclient.RegionInfo(name=TEST_REGION,
                                             endpoint='http://test:8773/')
        self.project = manager.ProjectManager(self.user.username,
                                              project,
                                              self.region)
        self.mox.StubOutWithMock(shortcuts, 'get_project_or_404')
        shortcuts.get_project_or_404(mox.IgnoreArg(),
                                     'test').AndReturn(self.project)

    def create_key_pair_choices(self, key_names):
        return [(k, k) for k in key_names]

    def create_instance_type_choices(self):
        return [('m1.medium', 'm1.medium'),
                ('m1.large', 'm1.large')]

    def create_instance_choices(self, instance_ids):
        return [(id, id) for id in instance_ids]

    def create_available_volume_choices(self, volumes):
        return [(v.id, '%s %s - %dGB' % (v.id, v.displayName, v.size)) \
                for v in volumes]
