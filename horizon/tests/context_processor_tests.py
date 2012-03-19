# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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
from horizon import Dashboard


class ContextProcessorTests(test.TestCase):
    def setUp(self):
        super(ContextProcessorTests, self).setUp()
        self._prev_catalog = self.request.user.service_catalog
        context_processors.horizon = self._real_horizon_context_processor

    def tearDown(self):
        super(ContextProcessorTests, self).tearDown()
        self.request.user.service_catalog = self._prev_catalog

    def test_authorized_tenants(self):
        tenant_list = self.context['authorized_tenants']
        self.request.user.authorized_tenants = None  # Reset from setUp
        self.mox.StubOutWithMock(api, 'tenant_list_for_token')
        api.tenant_list_for_token(IsA(http.HttpRequest), self.token.id) \
                                  .AndReturn(tenant_list)
        self.mox.ReplayAll()

        middleware.HorizonMiddleware().process_request(self.request)
        # Without dashboard that has "supports_tenants = True"
        context = context_processors.horizon(self.request)
        self.assertEqual(len(context['authorized_tenants']), 0)

        # With dashboard that has "supports_tenants = True"
        class ProjectDash(Dashboard):
            supports_tenants = True

        self.request.horizon['dashboard'] = ProjectDash
        self.assertTrue(self.request.user.is_authenticated())
        context = context_processors.horizon(self.request)
        self.assertItemsEqual(context['authorized_tenants'], tenant_list)
