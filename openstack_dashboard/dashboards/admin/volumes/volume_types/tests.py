# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
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
from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone
from openstack_dashboard.test import helpers as test


class VolumeTypeTests(test.BaseAdminViewTests):
    @test.create_stubs({cinder: ('volume_type_create',)})
    def test_create_volume_type(self):
        formData = {'name': 'volume type 1'}
        cinder.volume_type_create(IsA(http.HttpRequest),
                                  formData['name']).\
                                  AndReturn(self.volume_types.first())
        self.mox.ReplayAll()

        res = self.client.post(
            reverse('horizon:admin:volumes:volume_types:create_type'),
            formData)

        redirect = reverse('horizon:admin:volumes:volume_types_tab')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, redirect)

    @test.create_stubs({api.nova: ('server_list',),
                        cinder: ('volume_list',
                                 'volume_type_list_with_qos_associations',
                                 'qos_spec_list',
                                 'volume_type_delete',),
                        keystone: ('tenant_list',)})
    def test_delete_volume_type(self):
        volume_type = self.volume_types.first()
        formData = {'action': 'volume_types__delete__%s' % volume_type.id}

        cinder.volume_type_list_with_qos_associations(
            IsA(http.HttpRequest)).\
            AndReturn(self.volume_types.list())
        cinder.qos_spec_list(IsA(http.HttpRequest)).\
                             AndReturn(self.cinder_qos_specs.list())
        cinder.volume_type_delete(IsA(http.HttpRequest),
                                  str(volume_type.id))
        self.mox.ReplayAll()

        res = self.client.post(
            reverse('horizon:admin:volumes:volumes_tab'),
            formData)

        redirect = reverse('horizon:admin:volumes:volumes_tab')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, redirect)
