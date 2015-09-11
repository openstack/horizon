# Copyright 2015, Telles Nobrega
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from openstack_dashboard.contrib.sahara import api
from openstack_dashboard.contrib.sahara.test import helpers as test


class SaharaApiTest(test.SaharaAPITestCase):
    #
    # Cluster
    #
    def test_cluster_create_count(self):
        saharaclient = self.stub_saharaclient()
        saharaclient.clusters = self.mox.CreateMockAnything()
        saharaclient.clusters.create(anti_affinity=None,
                                     cluster_configs=None,
                                     cluster_template_id=None,
                                     count=2,
                                     use_autoconfig=None,
                                     default_image_id=None,
                                     description=None,
                                     hadoop_version='1.0.0',
                                     is_transient=None,
                                     name='name',
                                     net_id=None,
                                     node_groups=None,
                                     plugin_name='fake_plugin',
                                     user_keypair_id=None) \
            .AndReturn({"Clusters": ['cluster1', 'cluster2']})
        self.mox.ReplayAll()
        ret_val = api.sahara.cluster_create(self.request,
                                            'name',
                                            'fake_plugin',
                                            '1.0.0',
                                            count=2)

        self.assertEqual(2, len(ret_val['Clusters']))
