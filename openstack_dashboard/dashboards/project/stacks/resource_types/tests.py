# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class ResourceTypesTests(test.TestCase):

    @test.create_stubs({api.heat: ('resource_types_list',)})
    def test_index(self):
        filters = {}
        api.heat.resource_types_list(
            IsA(http.HttpRequest), filters=filters).AndReturn(
            self.resource_types.list())
        self.mox.ReplayAll()

        res = self.client.get(
            reverse('horizon:project:stacks.resource_types:index'))
        self.assertTemplateUsed(
            res, 'horizon/common/_data_table_view.html')
        self.assertContains(res, 'AWS::CloudFormation::Stack')

    @test.create_stubs({api.heat: ('resource_type_get',)})
    def test_detail_view(self):
        rt = self.api_resource_types.first()

        api.heat.resource_type_get(
            IsA(http.HttpRequest), rt['resource_type']).AndReturn(rt)
        self.mox.ReplayAll()

        url = reverse('horizon:project:stacks.resource_types:details',
                      args=[rt['resource_type']])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertNoMessages()
