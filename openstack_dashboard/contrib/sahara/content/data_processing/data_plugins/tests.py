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


INDEX_URL = reverse(
    'horizon:project:data_processing.data_plugins:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.data_plugins:details', args=['id'])


class DataProcessingPluginsTests(test.TestCase):
    @test.create_stubs({api.sahara: ('plugin_list',)})
    def test_index(self):
        api.sahara.plugin_list(IsA(http.HttpRequest)) \
            .AndReturn(self.plugins.list())
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(
            res, 'project/data_processing.data_plugins/plugins.html')
        self.assertContains(res, 'vanilla')
        self.assertContains(res, 'plugin')

    @test.create_stubs({api.sahara: ('plugin_get',)})
    def test_details(self):
        api.sahara.plugin_get(IsA(http.HttpRequest), IsA(six.text_type)) \
            .AndReturn(self.plugins.list()[0])
        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(
            res, 'project/data_processing.data_plugins/details.html')
        self.assertContains(res, 'vanilla')
        self.assertContains(res, 'plugin')
        self.assertContains(res, 'Plugin Overview')
