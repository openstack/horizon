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


INDEX_URL = reverse('horizon:project:data_processing.job_binaries:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.job_binaries:details', args=['id'])


class DataProcessingJobBinaryTests(test.TestCase):
    @test.create_stubs({api.sahara: ('job_binary_list',)})
    def test_index(self):
        api.sahara.job_binary_list(IsA(http.HttpRequest)) \
            .AndReturn(self.job_binaries.list())
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(
            res, 'project/data_processing.job_binaries/job_binaries.html')
        self.assertContains(res, 'Job Binaries')
        self.assertContains(res, 'Name')
        self.assertContains(res, 'example.pig')

    @test.create_stubs({api.sahara: ('job_binary_get',)})
    def test_details(self):
        api.sahara.job_binary_get(IsA(http.HttpRequest), IsA(unicode)) \
            .AndReturn(self.job_binaries.list()[0])
        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(
            res, 'project/data_processing.job_binaries/details.html')
        self.assertContains(res, 'Job Binary Details')

    @test.create_stubs({api.sahara: ('job_binary_list',
                                     'job_binary_get',
                                     'job_binary_internal_delete',
                                     'job_binary_delete',)})
    def test_delete(self):
        jb_list = (api.sahara.job_binary_list(IsA(http.HttpRequest))
                   .AndReturn(self.job_binaries.list()))
        api.sahara.job_binary_get(IsA(http.HttpRequest), IsA(unicode)) \
            .AndReturn(self.job_binaries.list()[0])
        api.sahara.job_binary_delete(IsA(http.HttpRequest), jb_list[0].id)
        int_id = jb_list[0].url.split("//")[1]
        api.sahara.job_binary_internal_delete(IsA(http.HttpRequest), int_id)
        self.mox.ReplayAll()
        form_data = {"action": "job_binaries__delete__%s" % jb_list[0].id}
        res = self.client.post(INDEX_URL, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.sahara: ('job_binary_get',
                                     'job_binary_get_file')})
    def test_download(self):
        jb = api.sahara.job_binary_get(IsA(http.HttpRequest), IsA(unicode)) \
            .AndReturn(self.job_binaries.list()[0])
        api.sahara.job_binary_get_file(IsA(http.HttpRequest), jb.id) \
            .AndReturn("TEST FILE CONTENT")
        self.mox.ReplayAll()

        context = {'job_binary_id': jb.id}
        url = reverse('horizon:project:data_processing.job_binaries:download',
                      kwargs={'job_binary_id': jb.id})
        res = self.client.get(url, context)
        self.assertTrue(res.has_header('content-disposition'))

    @test.create_stubs({api.sahara: ('job_binary_get',
                                     'job_binary_get_file')})
    def test_download_with_spaces(self):
        jb = api.sahara.job_binary_get(IsA(http.HttpRequest), IsA(unicode)) \
            .AndReturn(self.job_binaries.list()[1])
        api.sahara.job_binary_get_file(IsA(http.HttpRequest), jb.id) \
            .AndReturn("MORE TEST FILE CONTENT")
        self.mox.ReplayAll()

        context = {'job_binary_id': jb.id}
        url = reverse('horizon:project:data_processing.job_binaries:download',
                      kwargs={'job_binary_id': jb.id})
        res = self.client.get(url, context)
        self.assertEqual(
            res.get('Content-Disposition'),
            'attachment; filename="%s"' % jb.name
        )
