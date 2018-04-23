# Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
#
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

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


IDPS_INDEX_URL = reverse('horizon:identity:identity_providers:index')
IDPS_REGISTER_URL = reverse('horizon:identity:identity_providers:register')
IDPS_UPDATE_URL = reverse('horizon:identity:identity_providers:update',
                          args=['idp_1'])
IDPS_DETAIL_URL = reverse('horizon:identity:identity_providers:detail',
                          args=['idp_1'])


class IdPsViewTests(test.BaseAdminViewTests):

    @test.create_mocks({api.keystone: ('identity_provider_list',)})
    def test_index(self):
        self.mock_identity_provider_list.return_value = \
            self.identity_providers.list()

        res = self.client.get(IDPS_INDEX_URL)

        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        self.assertItemsEqual(res.context['table'].data,
                              self.identity_providers.list())

        self.mock_identity_provider_list.assert_called_once_with(
            test.IsHttpRequest())

    @test.create_mocks({api.keystone: ('identity_provider_create', )})
    def test_create(self):
        idp = self.identity_providers.first()

        self.mock_identity_provider_create.return_value = idp

        formData = {'method': 'RegisterIdPForm',
                    'id': idp.id,
                    'description': idp.description,
                    'enabled': idp.enabled,
                    'remote_ids': ', '.join(idp.remote_ids)}
        res = self.client.post(IDPS_REGISTER_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

        self.mock_identity_provider_create.assert_called_once_with(
            test.IsHttpRequest(),
            idp.id,
            description=idp.description,
            enabled=idp.enabled,
            remote_ids=idp.remote_ids)

    @test.create_mocks({api.keystone: ('identity_provider_get',
                                       'identity_provider_update')})
    def test_update(self):
        idp = self.identity_providers.first()
        new_description = 'new_idp_desc'

        self.mock_identity_provider_get.return_value = idp
        self.mock_identity_provider_update.return_value = None

        formData = {'method': 'UpdateIdPForm',
                    'id': idp.id,
                    'description': new_description,
                    'enabled': idp.enabled,
                    'remote_ids': ', '.join(idp.remote_ids)}

        res = self.client.post(IDPS_UPDATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

        self.mock_identity_provider_get.assert_called_once_with(
            test.IsHttpRequest(), idp.id)
        self.mock_identity_provider_update.assert_called_once_with(
            test.IsHttpRequest(),
            idp.id,
            description=new_description,
            enabled=idp.enabled,
            remote_ids=idp.remote_ids)

    @test.create_mocks({api.keystone: ('identity_provider_list',
                                       'identity_provider_delete')})
    def test_delete(self):
        idp = self.identity_providers.first()

        self.mock_identity_provider_list.return_value = \
            self.identity_providers.list()
        self.mock_identity_provider_delete.return_value = None

        formData = {'action': 'identity_providers__delete__%s' % idp.id}
        res = self.client.post(IDPS_INDEX_URL, formData)

        self.assertNoFormErrors(res)

        self.mock_identity_provider_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_identity_provider_delete.assert_called_once_with(
            test.IsHttpRequest(), idp.id)

    @test.create_mocks({api.keystone: ('identity_provider_get',
                                       'protocol_list')})
    def test_detail(self):
        idp = self.identity_providers.first()

        self.mock_identity_provider_get.return_value = idp
        self.mock_protocol_list.return_value = self.idp_protocols.list()

        res = self.client.get(IDPS_DETAIL_URL)

        self.assertTemplateUsed(
            res, 'identity/identity_providers/_detail_overview.html')
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')

        self.mock_identity_provider_get.assert_called_once_with(
            test.IsHttpRequest(), idp.id)
        self.mock_protocol_list.assert_called_once_with(
            test.IsHttpRequest(), idp.id)

    @test.create_mocks({api.keystone: ('identity_provider_get',
                                       'protocol_list')})
    def test_detail_protocols(self):
        idp = self.identity_providers.first()

        self.mock_identity_provider_get.return_value = idp
        self.mock_protocol_list.return_value = self.idp_protocols.list()

        res = self.client.get(IDPS_DETAIL_URL + '?tab=idp_details__protocols')

        self.assertTemplateUsed(
            res, 'identity/identity_providers/_detail_overview.html')
        self.assertTemplateUsed(res, 'horizon/common/_detail_table.html')
        self.assertItemsEqual(res.context['idp_protocols_table'].data,
                              self.idp_protocols.list())

        self.mock_identity_provider_get.assert_called_once_with(
            test.IsHttpRequest(), idp.id)
        self.mock_protocol_list.assert_called_once_with(
            test.IsHttpRequest(), idp.id)
