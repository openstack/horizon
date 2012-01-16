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
from mox import IsA

from horizon import api
from horizon import context_processors
from horizon import middleware
from horizon import test


class ContextProcessorTests(test.TestCase):
    def setUp(self):
        super(ContextProcessorTests, self).setUp()
        self._prev_catalog = self.request.user.service_catalog
        context_processors.horizon = self._real_horizon_context_processor

    def tearDown(self):
        super(ContextProcessorTests, self).tearDown()
        self.request.user.service_catalog = self._prev_catalog

    def test_authorized_tenants(self):
        tenant_list = self.TEST_CONTEXT['authorized_tenants']
        self.request.user.authorized_tenants = None  # Reset from setUp
        self.mox.StubOutWithMock(api, 'tenant_list_for_token')
        api.tenant_list_for_token(IsA(http.HttpRequest),
                                  self.TEST_TOKEN,
                                  endpoint_type='internalURL') \
                                  .AndReturn(tenant_list)
        self.mox.ReplayAll()

        middleware.HorizonMiddleware().process_request(self.request)
        context = context_processors.horizon(self.request)
        self.assertEqual(len(context['authorized_tenants']), 1)
        tenant = context['authorized_tenants'].pop()
        self.assertEqual(tenant['id'], self.TEST_TENANT)

    def test_object_store(self):
        # Returns the object store service data when it's in the catalog
        context = context_processors.horizon(self.request)
        self.assertNotEqual(None, context['object_store_configured'])

        # Returns None when the object store is not in the catalog
        new_catalog = [service for service in self.request.user.service_catalog
                            if service['type'] != 'object-store']
        self.request.user.service_catalog = new_catalog
        context = context_processors.horizon(self.request)
        self.assertEqual(None, context['object_store_configured'])
