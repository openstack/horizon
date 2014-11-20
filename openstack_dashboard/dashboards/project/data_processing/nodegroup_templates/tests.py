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

from mox import IgnoreArg  # noqa
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.data_processing.utils \
    import workflow_helpers
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse(
    'horizon:project:data_processing.nodegroup_templates:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.nodegroup_templates:details',
    args=['id'])
CREATE_URL = reverse(
    'horizon:project:data_processing.nodegroup_templates:' +
    'configure-nodegroup-template')


class DataProcessingNodeGroupTests(test.TestCase):
    @test.create_stubs({api.sahara: ('nodegroup_template_list',)})
    def test_index(self):
        api.sahara.nodegroup_template_list(IsA(http.HttpRequest), {}) \
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

    @test.create_stubs({api.sahara: ('nodegroup_template_list',
                                     'nodegroup_template_delete')})
    def test_delete(self):
        ngt = self.nodegroup_templates.first()
        api.sahara.nodegroup_template_list(IsA(http.HttpRequest), {}) \
            .AndReturn(self.nodegroup_templates.list())
        api.sahara.nodegroup_template_delete(IsA(http.HttpRequest), ngt.id)
        self.mox.ReplayAll()

        form_data = {'action': 'nodegroup_templates__delete__%s' % ngt.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.sahara: ('nodegroup_template_get',
                                     'plugin_get_version_details'),
                        api.network: ('floating_ip_pools_list',
                                      'security_group_list'),
                        api.cinder: ('extension_supported',
                                     'availability_zone_list')})
    def test_copy(self):
        ngt = self.nodegroup_templates.first()
        configs = self.plugins_configs.first()
        api.cinder.extension_supported(IsA(http.HttpRequest),
                                       'AvailabilityZones') \
            .AndReturn(True)
        api.cinder.availability_zone_list(IsA(http.HttpRequest))\
            .AndReturn(self.availability_zones.list())
        api.sahara.nodegroup_template_get(IsA(http.HttpRequest),
                                          ngt.id) \
            .AndReturn(ngt)
        api.sahara.plugin_get_version_details(IsA(http.HttpRequest),
                                              ngt.plugin_name,
                                              ngt.hadoop_version) \
            .MultipleTimes().AndReturn(configs)
        api.network.floating_ip_pools_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn([])

        self.mox.ReplayAll()

        url = reverse(
            'horizon:project:data_processing.nodegroup_templates:copy',
            args=[ngt.id])
        res = self.client.get(url)
        workflow = res.context['workflow']
        step = workflow.get_step("generalconfigaction")
        self.assertEqual(step.action['nodegroup_name'].field.initial,
                         ngt.name + "-copy")

    @test.create_stubs({api.sahara: ('client',
                                     'nodegroup_template_create',
                                     'plugin_get_version_details'),
                        api.network: ('floating_ip_pools_list',
                                      'security_group_list'),
                        api.nova: ('flavor_list',),
                        api.cinder: ('extension_supported',
                                     'availability_zone_list')})
    def test_create(self):
        flavor = self.flavors.first()
        ngt = self.nodegroup_templates.first()
        configs = self.plugins_configs.first()
        new_name = ngt.name + '-new'
        self.mox.StubOutWithMock(
            workflow_helpers, 'parse_configs_from_context')

        api.cinder.extension_supported(IsA(http.HttpRequest),
                                       'AvailabilityZones') \
            .AndReturn(True)
        api.cinder.availability_zone_list(IsA(http.HttpRequest))\
            .AndReturn(self.availability_zones.list())
        api.nova.flavor_list(IsA(http.HttpRequest)).AndReturn([flavor])
        api.sahara.plugin_get_version_details(IsA(http.HttpRequest),
                                              ngt.plugin_name,
                                              ngt.hadoop_version) \
            .MultipleTimes().AndReturn(configs)
        api.network.floating_ip_pools_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        workflow_helpers.parse_configs_from_context(
            IgnoreArg(), IgnoreArg()).AndReturn({})
        api.sahara.nodegroup_template_create(
            IsA(http.HttpRequest),
            **{'name': new_name,
               'plugin_name': ngt.plugin_name,
               'hadoop_version': ngt.hadoop_version,
               'description': ngt.description,
               'flavor_id': flavor.id,
               'volumes_per_node': None,
               'volumes_size': None,
               'volumes_availability_zone': None,
               'node_processes': ['namenode'],
               'node_configs': {},
               'floating_ip_pool': None,
               'security_groups': [],
               'auto_security_group': True,
               'availability_zone': None,
               'is_proxy_gateway': False}) \
            .AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.post(
            CREATE_URL,
            {'nodegroup_name': new_name,
             'plugin_name': ngt.plugin_name,
             ngt.plugin_name + '_version': '1.2.1',
             'hadoop_version': ngt.hadoop_version,
             'description': ngt.description,
             'flavor': flavor.id,
             'availability_zone': None,
             'storage': 'ephemeral_drive',
             'volumes_per_node': 0,
             'volumes_size': 0,
             'volumes_availability_zone': None,
             'floating_ip_pool': None,
             'security_autogroup': True,
             'processes': 'HDFS:namenode'})

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
