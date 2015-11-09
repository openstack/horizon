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

from mox3.mox import IsA  # noqa
from oslo_serialization import jsonutils

from openstack_dashboard.contrib.sahara import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:data_processing.clusters:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.clusters:details', args=['id'])


class DataProcessingClusterTests(test.TestCase):
    @test.create_stubs({api.sahara: ('cluster_list',)})
    def test_index(self):
        api.sahara.cluster_list(IsA(http.HttpRequest), {}) \
            .AndReturn(self.clusters.list())
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(
            res, 'project/data_processing.clusters/clusters.html')
        self.assertContains(res, 'Clusters')
        self.assertContains(res, 'Name')

    @test.create_stubs({api.sahara: ('cluster_template_list', 'image_list')})
    def test_launch_cluster_get_nodata(self):
        api.sahara.cluster_template_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        api.sahara.image_list(IsA(http.HttpRequest)) \
            .AndReturn([])
        self.mox.ReplayAll()
        url = reverse(
            'horizon:project:data_processing.clusters:configure-cluster')
        res = self.client.get("%s?plugin_name=shoes&hadoop_version=1.1" % url)
        self.assertContains(res, "No Images Available")
        self.assertContains(res, "No Templates Available")

    @test.create_stubs({api.sahara: ('cluster_get',)})
    def test_event_log_tab(self):
        cluster = self.clusters.list()[-1]
        api.sahara.cluster_get(IsA(http.HttpRequest),
                               "cl2", show_progress=True).AndReturn(cluster)
        self.mox.ReplayAll()

        url = reverse(
            'horizon:project:data_processing.clusters:events', args=["cl2"])
        res = self.client.get(url)
        data = jsonutils.loads(res.content)

        self.assertIn("provision_steps", data)
        self.assertEqual(data["need_update"], False)

        step_0 = data["provision_steps"][0]
        self.assertEqual(2, step_0["completed"])
        self.assertEqual(2, len(step_0["events"]))
        for evt in step_0["events"]:
            self.assertEqual(True, evt["successful"])

        step_1 = data["provision_steps"][1]
        self.assertEqual(3, step_1["completed"])
        self.assertEqual(0, len(step_1["events"]))

    @test.create_stubs({api.sahara: ('cluster_list',
                                     'cluster_delete')})
    def test_delete(self):
        cluster = self.clusters.first()
        api.sahara.cluster_list(IsA(http.HttpRequest), {}) \
            .AndReturn(self.clusters.list())
        api.sahara.cluster_delete(IsA(http.HttpRequest), cluster.id)
        self.mox.ReplayAll()

        form_data = {'action': 'clusters__delete__%s' % cluster.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
