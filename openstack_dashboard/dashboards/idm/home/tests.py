# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mox import IgnoreArg
from mox import IsA  # noqa

from django import http
from django.contrib import auth as django_auth
from django.core.urlresolvers import reverse

from openstack_auth import exceptions as auth_exceptions
from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:idm:home:index')


class HomeTests(test.TestCase):
    # Unit tests for home.
    @test.create_stubs({api.keystone: ('tenant_list', 'application_list')})

    def test_index(self):
    	# api.keystone.tenant_list(IsA(http.HttpRequest),
     #                         domain=None,
     #                         paginate=True,
     #                         marker=None) \
     #    .AndReturn([self.tenants.list(), False])

     #    api.keystone.application_list(IsA(http.HttpRequest)) \
     #    .AndReturn([self.applications.list(), False])

     #    self.mox.ReplayAll()

     #    res = self.client.get(INDEX_URL)
     #    self.assertTemplateUsed(res, 'idm/home/index.html')
        # self.assertItemsEqual(res.context['table'].data, self.tenants.list())
