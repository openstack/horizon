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


class FlavorExtrasTests(test.BaseAdminViewTests):

    @test.create_stubs({api.nova: ('flavor_get_extras',
                                   'flavor_get'), })
    def test_list_extras_when_none_exists(self):
        flavor = self.flavors.first()
        extras = [api.nova.FlavorExtraSpec(flavor.id, 'k1', 'v1')]

        # GET -- to determine correctness of output
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)
        api.nova.flavor_get_extras(IsA(http.HttpRequest),
                                 flavor.id).AndReturn(extras)
        self.mox.ReplayAll()
        url = reverse('horizon:admin:flavors:extras:index', args=[flavor.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "admin/flavors/extras/index.html")

    @test.create_stubs({api.nova: ('flavor_extra_set', ), })
    def _generic_extra_create_post(self, key_name):
        flavor = self.flavors.first()
        create_url = reverse('horizon:admin:flavors:extras:create',
                             args=[flavor.id])
        index_url = reverse('horizon:admin:flavors:extras:index',
                            args=[flavor.id])

        # GET to display the flavor_name
        api.nova.flavor_extra_set(IsA(http.HttpRequest),
                                  flavor.id,
                                  {key_name: 'v1'})
        self.mox.ReplayAll()

        data = {'flavor_id': flavor.id,
                'keys': 'custom',
                'key': key_name,
                'value': 'v1'}
        resp = self.client.post(create_url, data)
        self.assertNoFormErrors(resp)
        self.assertRedirectsNoFollow(resp, index_url)
        self.mox.UnsetStubs()

    @test.create_stubs({api.nova: ('flavor_extra_set', ), })
    def test_extra_create_with_template(self):
        flavor = self.flavors.first()
        create_url = reverse('horizon:admin:flavors:extras:create',
                             args=[flavor.id])
        index_url = reverse('horizon:admin:flavors:extras:index',
                            args=[flavor.id])

        # GET to display the flavor_name
        api.nova.flavor_extra_set(IsA(http.HttpRequest),
                                  flavor.id,
                                  {'quota:read_bytes_sec': '1000'})
        self.mox.ReplayAll()

        data = {'flavor_id': flavor.id,
                'keys': 'quota:read_bytes_sec',
                'value': '1000'}
        resp = self.client.post(create_url, data)
        self.assertNoFormErrors(resp)
        self.assertRedirectsNoFollow(resp, index_url)

    @test.create_stubs({api.nova: ('flavor_get', ), })
    def test_extra_create_get(self):
        flavor = self.flavors.first()
        create_url = reverse('horizon:admin:flavors:extras:create',
                             args=[flavor.id])

        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)
        self.mox.ReplayAll()

        resp = self.client.get(create_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp,
                                'admin/flavors/extras/create.html')

    @test.create_stubs({api.nova: ('flavor_get', ), })
    def _generic_extra_create_names_format_fail(self, key_name):
        flavor = self.flavors.first()
        create_url = reverse('horizon:admin:flavors:extras:create',
                             args=[flavor.id])
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)

        self.mox.ReplayAll()

        data = {'flavor_id': flavor.id,
                'keys': 'custom',
                'key': key_name,
                'value': 'v1'}

        resp = self.client.post(create_url, data)
        msg = ('Name may only contain letters, numbers, underscores, periods, '
              'colons, spaces and hyphens.')

        self.assertFormErrors(resp, 1, msg)
        self.mox.UnsetStubs()

    def test_create_extra_key_names_valid_formats(self):
        valid_keys = ("key1", "month.price", "I-Am:AK-ey. 22-")
        for x in valid_keys:
            self._generic_extra_create_post(key_name=x)

    def test_create_extra_key_names_invalid_formats(self):
        invalid_keys = ("key1/", "<key>", "$$akey$", "!akey")
        for x in invalid_keys:
            self._generic_extra_create_names_format_fail(key_name=x)
