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

import json

from django.urls import reverse

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


MAPPINGS_INDEX_URL = reverse('horizon:identity:mappings:index')
MAPPINGS_CREATE_URL = reverse('horizon:identity:mappings:create')
MAPPINGS_UPDATE_URL = reverse('horizon:identity:mappings:update',
                              args=['mapping_1'])


class MappingsViewTests(test.BaseAdminViewTests):

    @test.create_mocks({api.keystone: ('mapping_list',)})
    def test_index(self):
        self.mock_mapping_list.return_value = self.idp_mappings.list()

        res = self.client.get(MAPPINGS_INDEX_URL)

        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')
        self.assertItemsEqual(res.context['table'].data,
                              self.idp_mappings.list())
        self.mock_mapping_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.keystone: ('mapping_create', )})
    def test_create(self):
        mapping = self.idp_mappings.first()

        self.mock_mapping_create.return_value = mapping

        formData = {'method': 'CreateMappingForm',
                    'id': mapping.id,
                    'rules': json.dumps(mapping.rules)}
        res = self.client.post(MAPPINGS_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

        self.mock_mapping_create.assert_called_once_with(test.IsHttpRequest(),
                                                         mapping.id,
                                                         rules=mapping.rules)

    @test.create_mocks({api.keystone: ('mapping_get',
                                       'mapping_update')})
    def test_update(self):
        mapping = self.idp_mappings.first()
        new_rules = [{"local": [], "remote": []}]

        self.mock_mapping_get.return_value = mapping
        self.mock_mapping_update.return_value = None

        formData = {'method': 'UpdateMappingForm',
                    'id': mapping.id,
                    'rules': json.dumps(new_rules)}

        res = self.client.post(MAPPINGS_UPDATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

        self.mock_mapping_get.assert_called_once_with(test.IsHttpRequest(),
                                                      mapping.id)
        self.mock_mapping_update.assert_called_once_with(test.IsHttpRequest(),
                                                         mapping.id,
                                                         rules=new_rules)

    @test.create_mocks({api.keystone: ('mapping_list',
                                       'mapping_delete')})
    def test_delete(self):
        mapping = self.idp_mappings.first()

        self.mock_mapping_list.return_value = self.idp_mappings.list()
        self.mock_mapping_delete.return_value = None

        formData = {'action': 'idp_mappings__delete__%s' % mapping.id}
        res = self.client.post(MAPPINGS_INDEX_URL, formData)

        self.assertNoFormErrors(res)

        self.mock_mapping_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_mapping_delete.assert_called_once_with(test.IsHttpRequest(),
                                                         mapping.id)
