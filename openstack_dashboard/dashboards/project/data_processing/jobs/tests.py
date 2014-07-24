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


INDEX_URL = reverse('horizon:project:data_processing.jobs:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.jobs:details', args=['id'])


class DataProcessingJobTests(test.TestCase):
    @test.create_stubs({api.sahara: ('job_list',)})
    def test_index(self):
        api.sahara.job_list(IsA(http.HttpRequest)) \
            .AndReturn(self.jobs.list())
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res,
            'project/data_processing.jobs/jobs.html')
        self.assertContains(res, 'Jobs')
        self.assertContains(res, 'Name')

    @test.create_stubs({api.sahara: ('job_get',)})
    def test_details(self):
        api.sahara.job_get(IsA(http.HttpRequest), IsA(unicode)) \
            .AndReturn(self.jobs.list()[0])
        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res,
            'project/data_processing.jobs/details.html')
        self.assertContains(res, 'pigjob')
