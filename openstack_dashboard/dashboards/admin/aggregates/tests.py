# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 B1 Systems GmbH
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

from django.core.urlresolvers import reverse
from django import http
from mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class AggregateViewTest(test.BaseAdminViewTests):
    @test.create_stubs({api.nova: ('aggregate_list',)})
    def test_index(self):
        aggregates = self.aggregates.list()
        api.nova.aggregate_list(IsA(http.HttpRequest)).AndReturn(aggregates)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:admin:aggregates:index'))
        self.assertTemplateUsed(res, 'admin/aggregates/index.html')
        self.assertItemsEqual(res.context['table'].data, aggregates)
