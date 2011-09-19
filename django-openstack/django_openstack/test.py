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

from django import http
from django import test
import mox

from django_openstack.middleware import keystone


class TestCase(test.TestCase):
    TEST_STAFF_USER = 'staffUser'
    TEST_TENANT = 'aTenant'
    TEST_TOKEN = 'aToken'
    TEST_USER = 'test'

    TEST_SERVICE_CATALOG = \
        {'cdn':
             [{'adminURL': 'http://cdn.admin-nets.local/v1.1/1234',
               'region': 'RegionOne',
               'internalURL': 'http://127.0.0.1:7777/v1.1/1234',
               'publicURL': 'http://cdn.publicinternets.com/v1.1/1234'}],
         'nova_compat':
             [{'adminURL': 'http://127.0.0.1:8774/v1.0',
               'region': 'RegionOne',
               'internalURL': 'http://localhost:8774/v1.0',
               'publicURL': 'http://nova.publicinternets.com/v1.0/'}],
         'nova':
             [{'adminURL': 'http://nova/novapi/admin',
               'region':'RegionOne',
               'internalURL': 'http://nova/novapi/internal',
               'publicURL': 'http://nova/novapi/public'}],
         'keystone':
             [{'adminURL': 'http://127.0.0.1:8081/v2.0',
               'region': 'RegionOne',
               'internalURL': 'http://127.0.0.1:8080/v2.0',
               'publicURL': 'http://keystone.publicinternets.com/v2.0'}],
         'glance':
             [{'adminURL': 'http://glance/glanceapi/admin',
               'region':'RegionOne',
               'internalURL': 'http://glance/glanceapi/internal',
               'publicURL': 'http://glance/glanceapi/public'}],
         'swift':
             [{'adminURL': 'http://swift.admin-nets.local:8080/',
               'region': 'RegionOne',
               'internalURL': 'http://127.0.0.1:8080/v1/AUTH_1234',
               'publicURL': 'http://swift.publicinternets.com/v1/AUTH_1234'}],
         'quantum':
             [{'adminURL': 'http://127.0.0.1:9696/v0.1',
               'internalURL': 'http://127.0.0.1:9696/v0.1'}],
        }

    def setUp(self):
        self.mox = mox.Mox()

        self._real_get_user_from_request = keystone.get_user_from_request
        self.setActiveUser(self.TEST_TOKEN, self.TEST_USER, self.TEST_TENANT,
                           True, self.TEST_SERVICE_CATALOG)
        self.request = http.HttpRequest()
        keystone.AuthenticationMiddleware().process_request(self.request)

    def tearDown(self):
        self.mox.UnsetStubs()
        keystone.get_user_from_request = self._real_get_user_from_request

    def setActiveUser(self, token, username,
                      tenant, is_admin, service_catalog):
        keystone.get_user_from_request = \
                lambda x: keystone.User(token, username, tenant,
                                        is_admin, service_catalog)
