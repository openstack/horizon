# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

from keystoneclient.v2_0 import client as keystone_client
from novaclient.v1_1 import client as nova_client

from horizon import api
from horizon import test


TEST_CONSOLE_TYPE = 'novnc'
TEST_EMAIL = 'test@test.com'
TEST_HOSTNAME = 'hostname'
TEST_INSTANCE_ID = '2'
TEST_PASSWORD = '12345'
TEST_PORT = 8000
TEST_RETURN = 'retValue'
TEST_TENANT_DESCRIPTION = 'tenantDescription'
TEST_TENANT_ID = '1234'
TEST_TENANT_NAME = 'foo'
TEST_TOKEN = 'aToken'
TEST_TOKEN_ID = 'userId'
TEST_URL = 'http://%s:%s/something/v1.0' % (TEST_HOSTNAME, TEST_PORT)
TEST_USERNAME = 'testUser'


class APIResource(api.APIResourceWrapper):
    """ Simple APIResource for testing """
    _attrs = ['foo', 'bar', 'baz']

    @staticmethod
    def get_instance(innerObject=None):
        if innerObject is None:

            class InnerAPIResource(object):
                pass

            innerObject = InnerAPIResource()
            innerObject.foo = 'foo'
            innerObject.bar = 'bar'
        return APIResource(innerObject)


class APIDict(api.APIDictWrapper):
    """ Simple APIDict for testing """
    _attrs = ['foo', 'bar', 'baz']

    @staticmethod
    def get_instance(innerDict=None):
        if innerDict is None:
            innerDict = {'foo': 'foo',
                         'bar': 'bar'}
        return APIDict(innerDict)


class APITestCase(test.TestCase):
    def setUp(self):
        def fake_keystoneclient(request, username=None, password=None,
                                tenant_id=None, token_id=None, endpoint=None):
            return self.stub_keystoneclient()
        super(APITestCase, self).setUp()
        self._original_keystoneclient = api.keystone.keystoneclient
        self._original_novaclient = api.nova.novaclient
        api.keystone.keystoneclient = fake_keystoneclient
        api.nova.novaclient = lambda request: self.stub_novaclient()

    def stub_novaclient(self):
        if not hasattr(self, "novaclient"):
            self.mox.StubOutWithMock(nova_client, 'Client')
            self.novaclient = self.mox.CreateMock(nova_client.Client)
        return self.novaclient

    def stub_keystoneclient(self):
        if not hasattr(self, "keystoneclient"):
            self.mox.StubOutWithMock(keystone_client, 'Client')
            self.keystoneclient = self.mox.CreateMock(keystone_client.Client)
        return self.keystoneclient

    def tearDown(self):
        super(APITestCase, self).tearDown()
        api.nova.novaclient = self._original_novaclient
        api.keystone.keystoneclient = self._original_keystoneclient
