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


class QosSpecsTests(test.BaseAdminViewTests):
    @test.create_stubs({api.cinder: ('qos_spec_get',), })
    def test_manage_qos_spec(self):
        qos_spec = self.cinder_qos_specs.first()
        index_url = reverse(
            'horizon:admin:volumes:volume_types:qos_specs:index',
            args=[qos_spec.id])

        api.cinder.qos_spec_get(IsA(http.HttpRequest),
                                qos_spec.id)\
            .AndReturn(qos_spec)

        self.mox.ReplayAll()

        res = self.client.get(index_url)

        self.assertTemplateUsed(res,
            'admin/volumes/volume_types/qos_specs/index.html')
        rows = res.context['table'].get_rows()
        specs = self.cinder_qos_specs.first().specs
        for row in rows:
            key = row.cells['key'].data
            self.assertTrue(key in specs)
            self.assertEqual(row.cells['value'].data,
                             specs.get(key))

    @test.create_stubs({api.cinder: ('qos_spec_create',)})
    def test_create_qos_spec(self):
        formData = {'name': 'qos-spec-1'}
        api.cinder.qos_spec_create(IsA(http.HttpRequest),
                               formData['name'],
                               {'consumer': 'back-end'}).\
                               AndReturn(self.cinder_qos_specs.first())
        self.mox.ReplayAll()

        res = self.client.post(
            reverse('horizon:admin:volumes:volume_types:create_qos_spec'),
            formData)

        redirect = reverse('horizon:admin:volumes:volume_types_tab')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, redirect)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.cinder: ('volume_type_list',
                                     'qos_spec_list',
                                     'qos_spec_delete',)})
    def test_delete_qos_spec(self):
        qos_spec = self.cinder_qos_specs.first()
        formData = {'action': 'qos_specs__delete__%s' % qos_spec.id}

        api.cinder.volume_type_list(IsA(http.HttpRequest)).\
                                    AndReturn(self.volume_types.list())
        api.cinder.qos_spec_list(IsA(http.HttpRequest)).\
                                 AndReturn(self.cinder_qos_specs.list())
        api.cinder.qos_spec_delete(IsA(http.HttpRequest),
                                  str(qos_spec.id))
        self.mox.ReplayAll()

        res = self.client.post(
            reverse('horizon:admin:volumes:volume_types_tab'),
            formData)

        redirect = reverse('horizon:admin:volumes:volume_types_tab')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, redirect)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.cinder: ('qos_spec_get',
                                     'qos_spec_get_keys',
                                     'qos_spec_set_keys',), })
    def test_spec_edit(self):
        qos_spec = self.cinder_qos_specs.first()
        key = 'minIOPS'
        edit_url = reverse('horizon:admin:volumes:volume_types:qos_specs:edit',
                            args=[qos_spec.id, key])
        index_url = reverse(
            'horizon:admin:volumes:volume_types:qos_specs:index',
            args=[qos_spec.id])

        data = {'value': '9999'}
        qos_spec.specs[key] = data['value']

        api.cinder.qos_spec_get(IsA(http.HttpRequest),
                                     qos_spec.id)\
            .AndReturn(qos_spec)
        api.cinder.qos_spec_get_keys(IsA(http.HttpRequest),
                                     qos_spec.id, raw=True)\
            .AndReturn(qos_spec)
        api.cinder.qos_spec_set_keys(IsA(http.HttpRequest),
                                     qos_spec.id,
                                     qos_spec.specs)

        self.mox.ReplayAll()

        resp = self.client.post(edit_url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, index_url)
