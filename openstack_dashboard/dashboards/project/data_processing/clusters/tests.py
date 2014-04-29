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


INDEX_URL = reverse('horizon:project:data_processing.clusters:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.clusters:details', args=['id'])


class DataProcessingClusterTests(test.TestCase):
    @test.create_stubs({api.sahara: ('cluster_list',)})
    def test_index(self):
        api.sahara.cluster_list(IsA(http.HttpRequest)) \
            .AndReturn(self.clusters.list())
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res,
            'project/data_processing.clusters/clusters.html')
        self.assertContains(res, 'Clusters')
        self.assertContains(res, 'Name')
