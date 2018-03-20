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

import six

from openstack_dashboard.test import helpers as test
from openstack_dashboard import views


class DashboardViewsTest(test.TestCase):
    def test_get_url_with_pagination(self):
        req = self.request
        url_string = 'horizon:project:instances:index'
        url = views.get_url_with_pagination(req, None, None, url_string, None)
        self.assertEqual(six.text_type('/project/instances/'), url)

    def test_get_url_with_pagination_with_if(self):
        req = self.request
        url_string = 'horizon:project:instances:detail'
        url = views.get_url_with_pagination(req, None, None, url_string, 'id')
        self.assertEqual(six.text_type('/project/instances/id/'), url)

    def test_get_url_with_pagination_next(self):
        req = self.request
        url_string = 'horizon:project:instances:index'
        req.GET.update({'next': 'id'})
        url = views.get_url_with_pagination(
            req, 'next', None, url_string, None)
        self.assertEqual(six.text_type('/project/instances/?next=id'), url)

    def test_get_url_with_pagination_prev(self):
        req = self.request
        url_string = 'horizon:project:instances:index'
        req.GET.update({'prev': 'id'})
        url = views.get_url_with_pagination(
            req, None, 'prev', url_string, None)
        self.assertEqual(six.text_type('/project/instances/?prev=id'), url)

    def test_urls_ngdetails(self):
        resp = self.client.get("/ngdetails/")
        self.assertEqual(200, resp.status_code)
        resp = self.client.get("/ngdetails/OS::Glance::Image/xxxxx-xxx")
        self.assertEqual(200, resp.status_code)
