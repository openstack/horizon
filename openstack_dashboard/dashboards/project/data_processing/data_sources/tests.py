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


INDEX_URL = reverse('horizon:project:data_processing.data_sources:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.data_sources:details', args=['id'])


class DataProcessingDataSourceTests(test.TestCase):
    @test.create_stubs({api.sahara: ('data_source_list',)})
    def test_index(self):
        api.sahara.data_source_list(IsA(http.HttpRequest)) \
            .AndReturn(self.data_sources.list())
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(
            res, 'project/data_processing.data_sources/data_sources.html')
        self.assertContains(res, 'Data Sources')
        self.assertContains(res, 'Name')
        self.assertContains(res, 'sampleOutput')
        self.assertContains(res, 'sampleOutput2')

    @test.create_stubs({api.sahara: ('data_source_get',)})
    def test_details(self):
        api.sahara.data_source_get(IsA(http.HttpRequest), IsA(unicode)) \
            .AndReturn(self.data_sources.list()[0])
        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(
            res, 'project/data_processing.data_sources/details.html')
        self.assertContains(res, 'sampleOutput')
        self.assertContains(res, 'Data Source Details')

    @test.create_stubs({api.sahara: ('data_source_list',
                                     'data_source_delete')})
    def test_delete(self):
        data_source = self.data_sources.first()
        api.sahara.data_source_list(IsA(http.HttpRequest)) \
            .AndReturn(self.data_sources.list())
        api.sahara.data_source_delete(IsA(http.HttpRequest), data_source.id)
        self.mox.ReplayAll()

        form_data = {'action': 'data_sources__delete__%s' % data_source.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
