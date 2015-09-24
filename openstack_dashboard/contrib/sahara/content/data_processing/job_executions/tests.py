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
import six

from openstack_dashboard.contrib.sahara import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:data_processing.job_executions:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.job_executions:details', args=['id'])


class DataProcessingJobExecutionTests(test.TestCase):
    @test.create_stubs({api.sahara: ('job_execution_list',)})
    def test_index(self):
        api.sahara.job_execution_list(IsA(http.HttpRequest), {}) \
            .AndReturn(self.job_executions.list())
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertEqual(
            "cluster-1",
            res.context_data["job_executions_table"].data[0].cluster_name)
        self.assertEqual(
            "job-1",
            res.context_data["job_executions_table"].data[0].job_name)
        self.assertTemplateUsed(
            res, 'project/data_processing.job_executions/job_executions.html')
        self.assertContains(res, 'Jobs')

    @test.create_stubs({api.sahara: ('job_execution_get',)})
    def test_details(self):
        api.sahara.job_execution_get(IsA(http.HttpRequest), IsA(six.text_type)) \
            .MultipleTimes().AndReturn(self.job_executions.first())
        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertContains(res, 'RUNNING')

    @test.create_stubs({api.sahara: ('job_execution_list',
                                     'job_execution_delete')})
    def test_delete(self):
        job_exec = self.job_executions.first()
        api.sahara.job_execution_list(IsA(http.HttpRequest), {}) \
            .AndReturn(self.job_executions.list())
        api.sahara.job_execution_delete(IsA(http.HttpRequest), job_exec.id)
        self.mox.ReplayAll()

        form_data = {'action': 'job_executions__delete__%s' % job_exec.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
