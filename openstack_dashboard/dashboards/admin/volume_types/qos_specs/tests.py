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

from django.urls import reverse

import mock

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.volume_types.qos_specs \
    import views
from openstack_dashboard.test import helpers as test


class QosSpecsTests(test.BaseAdminViewTests):
    @test.create_mocks({api.cinder: ('qos_spec_get',)})
    def test_manage_qos_spec(self):
        qos_spec = self.cinder_qos_specs.first()
        index_url = reverse(
            'horizon:admin:volume_types:qos_specs:index',
            args=[qos_spec.id])

        self.mock_qos_spec_get.return_value = qos_spec

        res = self.client.get(index_url)

        self.assertTemplateUsed(
            res, 'admin/volume_types/qos_specs/index.html')
        rows = res.context['table'].get_rows()
        specs = self.cinder_qos_specs.first().specs
        for row in rows:
            key = row.cells['key'].data
            self.assertIn(key, specs)
            self.assertEqual(row.cells['value'].data,
                             specs.get(key))

        self.mock_qos_spec_get.assert_has_calls(
            [mock.call(test.IsHttpRequest(), qos_spec.id)] * 2)
        self.assertEqual(2, self.mock_qos_spec_get.call_count)

    @test.create_mocks({api.cinder: ('qos_spec_create',)})
    def test_create_qos_spec(self):
        formData = {'name': 'qos-spec-1',
                    'consumer': 'back-end'}
        self.mock_qos_spec_create.return_value = self.cinder_qos_specs.first()

        res = self.client.post(
            reverse('horizon:admin:volume_types:create_qos_spec'),
            formData)

        redirect = reverse('horizon:admin:volume_types:index')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, redirect)
        self.assertMessageCount(success=1)

        self.mock_qos_spec_create.assert_called_once_with(
            test.IsHttpRequest(),
            formData['name'],
            {'consumer': formData['consumer']})

    @test.create_mocks({api.cinder: ('volume_type_list_with_qos_associations',
                                     'volume_encryption_type_list',
                                     'qos_spec_list',
                                     'qos_spec_delete')})
    def test_delete_qos_spec(self):
        qos_spec = self.cinder_qos_specs.first()
        formData = {'action': 'qos_specs__delete__%s' % qos_spec.id}

        self.mock_volume_type_list_with_qos_associations.return_value = \
            self.cinder_volume_types.list()
        self.mock_volume_encryption_type_list.return_value = \
            self.cinder_volume_encryption_types.list()[0:1]
        self.mock_qos_spec_list.return_value = self.cinder_qos_specs.list()
        self.mock_qos_spec_delete.return_value = None

        res = self.client.post(
            reverse('horizon:admin:volume_types:index'),
            formData)

        redirect = reverse('horizon:admin:volume_types:index')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, redirect)
        self.assertMessageCount(success=1)

        self.mock_volume_type_list_with_qos_associations(test.IsHttpRequest())
        self.mock_volume_encryption_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_qos_spec_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_qos_spec_delete.assert_called_once_with(test.IsHttpRequest(),
                                                          str(qos_spec.id))

    @test.create_mocks({api.cinder: ('qos_spec_get',
                                     'qos_spec_get_keys',
                                     'qos_spec_set_keys')})
    def test_spec_edit(self):
        qos_spec = self.cinder_qos_specs.first()
        key = 'minIOPS'
        edit_url = reverse('horizon:admin:volume_types:qos_specs:edit',
                           args=[qos_spec.id, key])
        index_url = reverse('horizon:admin:volume_types:index')

        data = {'value': '9999'}
        qos_spec.specs[key] = data['value']

        self.mock_qos_spec_get.return_value = qos_spec
        self.mock_qos_spec_get_keys.return_value = qos_spec
        self.mock_qos_spec_set_keys.return_value = None

        resp = self.client.post(edit_url, data)
        self.assertEqual('admin/volume_types/qos_specs/edit.html',
                         views.EditKeyValuePairView.template_name)
        self.assertEqual('horizon:admin:volume_types:qos_specs:edit',
                         views.EditKeyValuePairView.submit_url)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, index_url)

        self.mock_qos_spec_get.assert_called_once_with(test.IsHttpRequest(),
                                                       qos_spec.id)
        self.mock_qos_spec_get_keys.assert_called_once_with(
            test.IsHttpRequest(), qos_spec.id, raw=True)
        self.mock_qos_spec_set_keys.assert_called_once_with(
            test.IsHttpRequest(), qos_spec.id, qos_spec.specs)

    @test.create_mocks({api.cinder: ('qos_spec_get',
                                     'qos_spec_set_keys')})
    def test_edit_consumer(self):
        qos_spec = self.cinder_qos_specs.first()

        # modify consumer to 'front-end'
        formData = {'consumer_choice': 'front-end'}

        edit_url = reverse(
            'horizon:admin:volume_types:edit_qos_spec_consumer',
            args=[qos_spec.id])

        self.mock_qos_spec_get.return_value = qos_spec
        self.mock_qos_spec_set_keys.return_value = None

        resp = self.client.post(edit_url, formData)
        redirect = reverse('horizon:admin:volume_types:index')
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, redirect)

        self.mock_qos_spec_get.assert_called_once_with(test.IsHttpRequest(),
                                                       qos_spec.id)
        self.mock_qos_spec_set_keys.assert_called_once_with(
            test.IsHttpRequest(), qos_spec.id,
            {'consumer': formData['consumer_choice']})

    @test.create_mocks({api.cinder: ('qos_spec_list',
                                     'qos_spec_get',
                                     'qos_spec_get_associations',
                                     'volume_type_get',
                                     'qos_spec_associate',
                                     'qos_spec_disassociate')})
    def test_associate_qos_spec(self):
        volume_type = self.cinder_volume_types.first()
        volume_types = self.cinder_volume_types.list()
        qos_specs = self.cinder_qos_specs.list()

        # associate qos spec with volume type
        formData = {'qos_spec_choice': qos_specs[0].id}

        edit_url = reverse(
            'horizon:admin:volume_types:manage_qos_spec_association',
            args=[volume_type.id])

        # for maximum code coverage, this test swaps the QoS association
        # on one volume type moving the QoS assigned from 1 to 0
        self.mock_volume_type_get.return_value = volume_type
        self.mock_qos_spec_list.return_value = qos_specs
        self.mock_qos_spec_get_associations.side_effect = [[], volume_types]
        self.mock_qos_spec_get.side_effect = [qos_specs[1], qos_specs[0]]
        self.mock_qos_spec_disassociate.return_value = None
        self.mock_qos_spec_associate.return_value = None

        resp = self.client.post(edit_url, formData)
        redirect = reverse('horizon:admin:volume_types:index')
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, redirect)

        self.mock_volume_type_get.assert_called_once_with(test.IsHttpRequest(),
                                                          volume_type.id)
        self.mock_qos_spec_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_qos_spec_get_associations.assert_has_calls([
            mock.call(test.IsHttpRequest(), qos_specs[0].id),
            mock.call(test.IsHttpRequest(), qos_specs[1].id),
        ])
        self.mock_qos_spec_get.assert_has_calls([
            mock.call(test.IsHttpRequest(), qos_specs[1].id),
            mock.call(test.IsHttpRequest(), qos_specs[0].id),
        ])
        self.mock_qos_spec_disassociate.assert_called_once_with(
            test.IsHttpRequest(), qos_specs[1], volume_type.id)
        self.mock_qos_spec_associate.assert_called_once_with(
            test.IsHttpRequest(), qos_specs[0], volume_type.id)
