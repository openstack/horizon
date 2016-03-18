# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class TemplateVersionsTests(test.TestCase):
    INDEX_URL = reverse('horizon:project:stacks.template_versions:index')

    @test.create_stubs({api.heat: ('template_version_list',)})
    def test_index(self):
        api.heat.template_version_list(
            IsA(http.HttpRequest)).AndReturn(self.template_versions.list())
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)
        self.assertTemplateUsed(
            res, 'project/stacks.template_versions/index.html')
        self.assertContains(res, 'HeatTemplateFormatVersion.2012-12-12')

    @test.create_stubs({api.heat: ('template_version_list',)})
    def test_index_exception(self):
        api.heat.template_version_list(
            IsA(http.HttpRequest)).AndRaise(self.exceptions.heat)
        self.mox.ReplayAll()

        res = self.client.get(self.INDEX_URL)
        self.assertTemplateUsed(
            res, 'project/stacks.template_versions/index.html')
        self.assertEqual(len(res.context['table'].data), 0)
        self.assertMessageCount(res, error=1)

    @test.create_stubs({api.heat: ('template_function_list',)})
    def test_detail_view(self):
        t_version = self.template_versions.first().version
        t_functions = self.template_functions.list()

        api.heat.template_function_list(
            IsA(http.HttpRequest), t_version).AndReturn(t_functions)
        self.mox.ReplayAll()

        url = reverse('horizon:project:stacks.template_versions:details',
                      args=[t_version])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertNoMessages()

    @test.create_stubs({api.heat: ('template_function_list',)})
    def test_detail_view_with_exception(self):
        t_version = self.template_versions.first().version

        api.heat.template_function_list(
            IsA(http.HttpRequest), t_version).AndRaise(self.exceptions.heat)
        self.mox.ReplayAll()

        url = reverse('horizon:project:stacks.template_versions:details',
                      args=[t_version])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(len(res.context['table'].data), 0)
        self.assertMessageCount(res, error=1)
