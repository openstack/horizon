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

from django.core.urlresolvers import reverse
from django import http

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse(
    'horizon:project:data_processing.nodegroup_templates:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.nodegroup_templates:details',
    args=['id'])


class DataProcessingNodeGroupTests(test.TestCase):
    @test.create_stubs({api.sahara: ('nodegroup_template_list',)})
    def test_index(self):
        api.sahara.nodegroup_template_list(IsA(http.HttpRequest)) \
            .AndReturn(self.nodegroup_templates.list())
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res,
            'project/data_processing.nodegroup_templates/'
            'nodegroup_templates.html')
        self.assertContains(res, 'Node Group Templates')
        self.assertContains(res, 'Name')
        self.assertContains(res, 'Plugin')

    @test.create_stubs({api.sahara: ('nodegroup_template_get',),
                        api.nova: ('flavor_get',)})
    def test_details(self):
        flavor = self.flavors.first()
        ngt = self.nodegroup_templates.first()
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)
        api.sahara.nodegroup_template_get(IsA(http.HttpRequest),
                                          IsA(unicode)) \
            .MultipleTimes().AndReturn(ngt)
        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res,
                                'project/data_processing.nodegroup_templates/'
                                'details.html')
        self.assertContains(res, 'sample-template')
        self.assertContains(res, 'Template Overview')
