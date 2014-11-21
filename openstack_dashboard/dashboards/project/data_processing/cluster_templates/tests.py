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


INDEX_URL = reverse('horizon:project:data_processing.cluster_templates:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.cluster_templates:details', args=['id'])


class DataProcessingClusterTemplateTests(test.TestCase):
    @test.create_stubs({api.sahara: ('cluster_template_list',)})
    def test_index(self):
        api.sahara.cluster_template_list(IsA(http.HttpRequest), {}) \
            .AndReturn(self.cluster_templates.list())
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res,
                                'project/data_processing.cluster_templates/'
                                'cluster_templates.html')
        self.assertContains(res, 'Cluster Templates')
        self.assertContains(res, 'Name')

    @test.create_stubs({api.sahara: ('cluster_template_get',),
                        api.nova: ('flavor_get',)})
    def test_details(self):
        flavor = self.flavors.first()
        ct = self.cluster_templates.first()
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id) \
            .MultipleTimes().AndReturn(flavor)
        api.sahara.cluster_template_get(IsA(http.HttpRequest),
                                        IsA(unicode)) \
            .MultipleTimes().AndReturn(ct)
        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res,
                                'project/data_processing.cluster_templates/'
                                'details.html')

    @test.create_stubs({api.sahara: ('cluster_template_get',
                                     'plugin_get_version_details',
                                     'nodegroup_template_find')})
    def test_copy(self):
        ct = self.cluster_templates.first()
        ngts = self.nodegroup_templates.list()
        configs = self.plugins_configs.first()
        api.sahara.cluster_template_get(IsA(http.HttpRequest),
                                        ct.id) \
            .AndReturn(ct)
        api.sahara.plugin_get_version_details(IsA(http.HttpRequest),
                                              ct.plugin_name,
                                              ct.hadoop_version) \
            .MultipleTimes().AndReturn(configs)
        api.sahara.nodegroup_template_find(IsA(http.HttpRequest),
                                           plugin_name=ct.plugin_name,
                                           hadoop_version=ct.hadoop_version) \
            .MultipleTimes().AndReturn(ngts)
        self.mox.ReplayAll()

        url = reverse('horizon:project:data_processing.cluster_templates:copy',
                      args=[ct.id])
        res = self.client.get(url)
        workflow = res.context['workflow']
        step = workflow.get_step("generalconfigaction")
        self.assertEqual(step.action['cluster_template_name'].field.initial,
                         ct.name + "-copy")

    @test.create_stubs({api.sahara: ('cluster_template_list',
                                     'cluster_template_delete')})
    def test_delete(self):
        ct = self.cluster_templates.first()
        api.sahara.cluster_template_list(IsA(http.HttpRequest), {}) \
            .AndReturn(self.cluster_templates.list())
        api.sahara.cluster_template_delete(IsA(http.HttpRequest), ct.id)
        self.mox.ReplayAll()

        form_data = {'action': 'cluster_templates__delete__%s' % ct.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
