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

from mox3.mox import IgnoreArg  # noqa
from mox3.mox import IsA  # noqa
import six

from openstack_dashboard import api as dash_api
from openstack_dashboard.contrib.sahara import api
from openstack_dashboard.contrib.sahara.content.data_processing.utils \
    import workflow_helpers
from openstack_dashboard.contrib.sahara.content.data_processing.\
    nodegroup_templates.workflows import create as create_workflow
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
    def _setup_copy_test(self):
        ngt = self.nodegroup_templates.first()
        configs = self.plugins_configs.first()
        dash_api.cinder.extension_supported(IsA(http.HttpRequest),
                                            'AvailabilityZones') \
            .AndReturn(True)
        dash_api.cinder.availability_zone_list(IsA(http.HttpRequest))\
            .AndReturn(self.availability_zones.list())
        dash_api.cinder.volume_type_list(IsA(http.HttpRequest))\
            .AndReturn([])
        api.sahara.nodegroup_template_get(IsA(http.HttpRequest),
                                          ngt.id) \
            .AndReturn(ngt)
        api.sahara.plugin_get_version_details(IsA(http.HttpRequest),
                                              ngt.plugin_name,
                                              ngt.hadoop_version) \
            .MultipleTimes().AndReturn(configs)
        dash_api.network.floating_ip_pools_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        dash_api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn([])

        self.mox.ReplayAll()

        url = reverse(
            'horizon:project:data_processing.nodegroup_templates:copy',
            args=[ngt.id])
        res = self.client.get(url)

        return ngt, configs, res

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
                        dash_api.nova: ('flavor_get',)})
    def test_details(self):
        flavor = self.flavors.first()
        ngt = self.nodegroup_templates.first()
        dash_api.nova.flavor_get(IsA(http.HttpRequest), flavor.id) \
            .AndReturn(flavor)
        api.sahara.nodegroup_template_get(IsA(http.HttpRequest),
                                          IsA(six.text_type)) \
            .MultipleTimes().AndReturn(ngt)
        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertContains(res, 'sample-template')

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
                        dash_api.network: ('floating_ip_pools_list',
                                           'security_group_list'),
                        dash_api.cinder: ('extension_supported',
                                          'availability_zone_list',
                                          'volume_type_list')})
    def test_copy(self):
        ngt, configs, res = self._setup_copy_test()
        workflow = res.context['workflow']
        step = workflow.get_step("generalconfigaction")
        self.assertEqual(step.action['nodegroup_name'].field.initial,
                         ngt.name + "-copy")

    @test.create_stubs({api.sahara: ('client',
                                     'nodegroup_template_create',
                                     'plugin_get_version_details'),
                        dash_api.network: ('floating_ip_pools_list',
                                           'security_group_list'),
                        dash_api.nova: ('flavor_list',),
                        dash_api.cinder: ('extension_supported',
                                          'availability_zone_list',
                                          'volume_type_list')})
    def test_create(self):
        flavor = self.flavors.first()
        ngt = self.nodegroup_templates.first()
        configs = self.plugins_configs.first()
        new_name = ngt.name + '-new'
        self.mox.StubOutWithMock(
            workflow_helpers, 'parse_configs_from_context')

        dash_api.cinder.extension_supported(IsA(http.HttpRequest),
                                            'AvailabilityZones') \
            .AndReturn(True)
        dash_api.cinder.availability_zone_list(IsA(http.HttpRequest))\
            .AndReturn(self.availability_zones.list())
        dash_api.cinder.volume_type_list(IsA(http.HttpRequest))\
            .AndReturn([])
        dash_api.nova.flavor_list(IsA(http.HttpRequest)).AndReturn([flavor])
        api.sahara.plugin_get_version_details(IsA(http.HttpRequest),
                                              ngt.plugin_name,
                                              ngt.hadoop_version) \
            .MultipleTimes().AndReturn(configs)
        dash_api.network.floating_ip_pools_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        dash_api.network.security_group_list(IsA(http.HttpRequest)) \
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
               'volume_type': None,
               'volume_local_to_instance': False,
               'volumes_availability_zone': None,
               'node_processes': ['namenode'],
               'node_configs': {},
               'floating_ip_pool': None,
               'security_groups': [],
               'auto_security_group': True,
               'availability_zone': None,
               'is_proxy_gateway': False,
               'use_autoconfig': True}) \
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
             'volume_type': None,
             'volume_local_to_instance': False,
             'volumes_availability_zone': None,
             'floating_ip_pool': None,
             'security_autogroup': True,
             'processes': 'HDFS:namenode',
             'use_autoconfig': True})

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.sahara: ('client',
                                     'nodegroup_template_create',
                                     'nodegroup_template_update',
                                     'nodegroup_template_get',
                                     'plugin_get_version_details'),
                        dash_api.network: ('floating_ip_pools_list',
                                           'security_group_list'),
                        dash_api.nova: ('flavor_list',),
                        dash_api.cinder: ('extension_supported',
                                          'availability_zone_list',
                                          'volume_type_list')})
    def test_update(self):
        flavor = self.flavors.first()
        ngt = self.nodegroup_templates.first()
        configs = self.plugins_configs.first()
        new_name = ngt.name + '-updated'
        UPDATE_URL = reverse(
            'horizon:project:data_processing.nodegroup_templates:edit',
            kwargs={'template_id': ngt.id})
        self.mox.StubOutWithMock(
            workflow_helpers, 'parse_configs_from_context')

        dash_api.cinder.extension_supported(IsA(http.HttpRequest),
                                            'AvailabilityZones') \
            .AndReturn(True)
        dash_api.cinder.availability_zone_list(IsA(http.HttpRequest)) \
            .AndReturn(self.availability_zones.list())
        dash_api.cinder.volume_type_list(IsA(http.HttpRequest))\
            .AndReturn([])
        dash_api.nova.flavor_list(IsA(http.HttpRequest)).AndReturn([flavor])
        api.sahara.plugin_get_version_details(IsA(http.HttpRequest),
                                              ngt.plugin_name,
                                              ngt.hadoop_version) \
            .MultipleTimes().AndReturn(configs)
        dash_api.network.floating_ip_pools_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        dash_api.network.security_group_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        workflow_helpers.parse_configs_from_context(
            IgnoreArg(), IgnoreArg()).AndReturn({})
        api.sahara.nodegroup_template_get(IsA(http.HttpRequest),
                                          ngt.id) \
            .AndReturn(ngt)
        api.sahara.nodegroup_template_update(
            request=IsA(http.HttpRequest),
            ngt_id=ngt.id,
            name=new_name,
            plugin_name=ngt.plugin_name,
            hadoop_version=ngt.hadoop_version,
            flavor_id=flavor.id,
            description=ngt.description,
            volumes_per_node=None,
            volumes_size=None,
            volume_type=None,
            volume_local_to_instance=False,
            volumes_availability_zone=None,
            node_processes=['namenode'],
            node_configs={},
            floating_ip_pool=None,
            security_groups=[],
            auto_security_group=True,
            availability_zone=None,
            use_autoconfig=True,
            is_proxy_gateway=False).AndReturn(True)

        self.mox.ReplayAll()

        res = self.client.post(
            UPDATE_URL,
            {'ng_id': ngt.id,
             'nodegroup_name': new_name,
             'plugin_name': ngt.plugin_name,
             ngt.plugin_name + '_version': '1.2.1',
             'hadoop_version': ngt.hadoop_version,
             'description': ngt.description,
             'flavor': flavor.id,
             'availability_zone': None,
             'storage': 'ephemeral_drive',
             'volumes_per_node': 0,
             'volumes_size': 0,
             'volume_type': None,
             'volume_local_to_instance': False,
             'volumes_availability_zone': None,
             'floating_ip_pool': None,
             'is_proxy_gateway': False,
             'security_autogroup': True,
             'processes': 'HDFS:namenode',
             'use_autoconfig': True})

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.sahara: ('nodegroup_template_get',
                                     'plugin_get_version_details'),
                        dash_api.network: ('floating_ip_pools_list',
                                           'security_group_list'),
                        dash_api.cinder: ('extension_supported',
                                          'availability_zone_list',
                                          'volume_type_list')})
    def test_workflow_steps(self):
        # since the copy workflow is the child of create workflow
        # it's better to test create workflow through copy workflow
        ngt, configs, res = self._setup_copy_test()
        workflow = res.context['workflow']
        expected_instances = [
            create_workflow.GeneralConfig,
            create_workflow.SelectNodeProcesses,
            create_workflow.SecurityConfig
        ]
        for expected, observed in zip(expected_instances, workflow.steps):
            self.assertIsInstance(observed, expected)
