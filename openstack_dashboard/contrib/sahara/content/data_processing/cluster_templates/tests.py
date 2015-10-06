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

import base64
import copy

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IsA  # noqa
from oslo_serialization import jsonutils
import six

from openstack_dashboard import api as dash_api
from openstack_dashboard.contrib.sahara import api
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
                        dash_api.nova: ('flavor_get',)})
    def test_details(self):
        flavor = self.flavors.first()
        ct = self.cluster_templates.first()
        dash_api.nova.flavor_get(IsA(http.HttpRequest), flavor.id) \
            .MultipleTimes().AndReturn(flavor)
        api.sahara.cluster_template_get(IsA(http.HttpRequest),
                                        IsA(six.text_type)) \
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

    @test.create_stubs({api.sahara: ('cluster_template_get',
                                     'cluster_template_update',
                                     'plugin_get_version_details',
                                     'nodegroup_template_find')})
    def test_update(self):
        ct = self.cluster_templates.first()
        ngts = self.nodegroup_templates.list()
        configs = self.plugins_configs.first()
        new_name = "UpdatedName"
        new_ct = copy.copy(ct)
        new_ct.name = new_name

        api.sahara.cluster_template_get(IsA(http.HttpRequest), ct.id) \
            .AndReturn(ct)
        api.sahara.plugin_get_version_details(IsA(http.HttpRequest),
                                              ct.plugin_name,
                                              ct.hadoop_version) \
            .MultipleTimes().AndReturn(configs)
        api.sahara.nodegroup_template_find(IsA(http.HttpRequest),
                                           plugin_name=ct.plugin_name,
                                           hadoop_version=ct.hadoop_version) \
            .MultipleTimes().AndReturn(ngts)
        api.sahara.cluster_template_update(request=IsA(http.HttpRequest),
                                           ct_id=ct.id,
                                           name=new_name,
                                           plugin_name=ct.plugin_name,
                                           hadoop_version=ct.hadoop_version,
                                           description=ct.description,
                                           cluster_configs=ct.cluster_configs,
                                           node_groups=ct.node_groups,
                                           anti_affinity=ct.anti_affinity,
                                           use_autoconfig=False)\
            .AndReturn(new_ct)
        self.mox.ReplayAll()

        url = reverse('horizon:project:data_processing.cluster_templates:edit',
                      args=[ct.id])

        def serialize(obj):
            return base64.urlsafe_b64encode(jsonutils.dump_as_bytes(obj))

        res = self.client.post(
            url,
            {'ct_id': ct.id,
             'cluster_template_name': new_name,
             'plugin_name': ct.plugin_name,
             'hadoop_version': ct.hadoop_version,
             'description': ct.description,
             'hidden_configure_field': "",
             'template_id_0': ct.node_groups[0]['node_group_template_id'],
             'group_name_0': ct.node_groups[0]['name'],
             'count_0': 1,
             'serialized_0': serialize(ct.node_groups[0]),
             'template_id_1': ct.node_groups[1]['node_group_template_id'],
             'group_name_1': ct.node_groups[1]['name'],
             'count_1': 2,
             'serialized_1': serialize(ct.node_groups[1]),
             'forms_ids': "[0,1]",
             'anti-affinity': ct.anti_affinity,
             })

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
