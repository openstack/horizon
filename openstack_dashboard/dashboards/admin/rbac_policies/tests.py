# Copyright 2019 vmware, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from django.urls import reverse
import mock

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'
INDEX_URL = reverse('horizon:admin:rbac_policies:index')


class RBACPolicyTests(test.BaseAdminViewTests):

    @test.create_mocks({api.neutron: ('rbac_policy_list',
                                      'network_list',
                                      'policy_list',
                                      'is_extension_supported',),
                       api.keystone: ('tenant_list',)})
    def test_index(self):
        tenants = self.tenants.list()

        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = self.networks.list()
        self.mock_policy_list.return_value = self.qos_policies.list()
        self.mock_rbac_policy_list.return_value = self.rbac_policies.list()
        self.mock_is_extension_supported.return_value = True

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        rbac_policies = res.context['table'].data
        self.assertItemsEqual(rbac_policies, self.rbac_policies.list())
        self.mock_network_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_policy_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), extension_alias='qos')
        self.mock_rbac_policy_list.assert_called_once_with(
            test.IsHttpRequest())

    @test.create_mocks({api.neutron: ('network_list',
                                      'rbac_policy_create',
                                      'is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    def test_rbac_create_post_with_network_type(self):
        network = self.networks.first()
        tenants = self.tenants.list()
        rbac_policy = self.rbac_policies.first()

        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = self.networks.list()
        self.mock_is_extension_supported.return_value = False
        self.mock_rbac_policy_create.return_value = rbac_policy

        form_data = {'target_tenant': rbac_policy.target_tenant,
                     'action_object_type': 'external_network',
                     'network_id': network.id}
        url = reverse('horizon:admin:rbac_policies:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_network_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), extension_alias='qos')
        params = {'target_tenant': rbac_policy.target_tenant,
                  'action': 'access_as_external',
                  'object_type': 'network',
                  'object_id': network.id}
        self.mock_rbac_policy_create.assert_called_once_with(
            test.IsHttpRequest(), **params)

    @test.create_mocks({api.neutron: ('network_list',
                                      'policy_list',
                                      'rbac_policy_create',
                                      'is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    def test_rbac_create_post_with_qos_policy_type(self):
        qos_policy = self.qos_policies.first()
        tenants = self.tenants.list()
        rbac_policy = self.rbac_policies.filter(object_type="qos_policy")[0]

        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = self.networks.list()
        self.mock_policy_list.return_value = self.qos_policies.list()
        self.mock_is_extension_supported.return_value = True
        self.mock_rbac_policy_create.return_value = rbac_policy

        form_data = {'target_tenant': rbac_policy.target_tenant,
                     'action_object_type': 'shared_qos_policy',
                     'qos_policy_id': qos_policy.id}
        url = reverse('horizon:admin:rbac_policies:create')
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_network_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_policy_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_is_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), extension_alias='qos')
        params = {'target_tenant': rbac_policy.target_tenant,
                  'action': 'access_as_shared',
                  'object_type': 'qos_policy',
                  'object_id': qos_policy.id}
        self.mock_rbac_policy_create.assert_called_once_with(
            test.IsHttpRequest(), **params)

    @test.create_mocks({api.neutron: ('network_list',
                                      'is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    def test_rbac_create_post_with_network_type_and_no_network_id(self):
        tenants = self.tenants.list()
        rbac_policy = self.rbac_policies.first()

        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = self.networks.list()
        self.mock_is_extension_supported.return_value = False

        # note that 'network_id' is not included
        form_data = {'target_tenant': rbac_policy.target_tenant,
                     'action_object_type': 'external_network'}
        url = reverse('horizon:admin:rbac_policies:create')
        res = self.client.post(url, form_data)

        self.assertFormErrors(res, 1)
        self.assertContains(res, "This field is required.")

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_list, 2, mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_list, 2, mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_extension_supported, 2,
            mock.call(test.IsHttpRequest(), extension_alias='qos'))

    @test.create_mocks({api.neutron: ('network_list',
                                      'policy_list',
                                      'is_extension_supported',),
                        api.keystone: ('tenant_list',)})
    def test_rbac_create_post_with_qos_policy_type_and_no_qos_policy_id(self):
        tenants = self.tenants.list()
        rbac_policy = self.rbac_policies.filter(object_type="qos_policy")[0]

        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_network_list.return_value = self.networks.list()
        self.mock_policy_list.return_value = self.qos_policies.list()
        self.mock_is_extension_supported.return_value = True

        # note that 'qos_policy_id' is not included
        form_data = {'target_tenant': rbac_policy.target_tenant,
                     'action_object_type': 'shared_qos_policy'}
        url = reverse('horizon:admin:rbac_policies:create')
        res = self.client.post(url, form_data)

        self.assertFormErrors(res, 1)
        self.assertContains(res, "This field is required.")

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_list, 2, mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_network_list, 2, mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_policy_list, 2, mock.call(test.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_extension_supported, 2,
            mock.call(test.IsHttpRequest(), extension_alias='qos'))
