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

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IgnoreArg  # noqa
from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


MAPPINGS_INDEX_URL = reverse('horizon:identity:mappings:index')
MAPPINGS_CREATE_URL = reverse('horizon:identity:mappings:create')
MAPPINGS_UPDATE_URL = reverse('horizon:identity:mappings:update',
                              args=['mapping_1'])


class MappingsViewTests(test.BaseAdminViewTests):
    @test.create_stubs({api.keystone: ('mapping_list',)})
    def test_index(self):
        api.keystone.mapping_list(IgnoreArg()). \
            AndReturn(self.idp_mappings.list())

        self.mox.ReplayAll()

        res = self.client.get(MAPPINGS_INDEX_URL)

        self.assertTemplateUsed(res, 'identity/mappings/index.html')
        self.assertItemsEqual(res.context['table'].data,
                              self.idp_mappings.list())

    @test.create_stubs({api.keystone: ('mapping_create', )})
    def test_create(self):
        mapping = self.idp_mappings.first()

        api.keystone.mapping_create(IgnoreArg(),
                                    mapping.id,
                                    rules=mapping.rules). \
            AndReturn(mapping)

        self.mox.ReplayAll()

        formData = {'method': 'CreateMappingForm',
                    'id': mapping.id,
                    'rules': json.dumps(mapping.rules)}
        res = self.client.post(MAPPINGS_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('mapping_get',
                                       'mapping_update')})
    def test_update(self):
        mapping = self.idp_mappings.first()
        new_rules = [{"local": [], "remote": []}]

        api.keystone.mapping_get(IsA(http.HttpRequest),
                                 mapping.id). \
            AndReturn(mapping)
        api.keystone.mapping_update(IsA(http.HttpRequest),
                                    mapping.id,
                                    rules=new_rules). \
            AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateMappingForm',
                    'id': mapping.id,
                    'rules': json.dumps(new_rules)}

        res = self.client.post(MAPPINGS_UPDATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('mapping_list',
                                       'mapping_delete')})
    def test_delete(self):
        mapping = self.idp_mappings.first()

        api.keystone.mapping_list(IsA(http.HttpRequest)) \
            .AndReturn(self.idp_mappings.list())
        api.keystone.mapping_delete(IsA(http.HttpRequest),
                                    mapping.id) \
            .AndReturn(None)

        self.mox.ReplayAll()

        formData = {'action': 'idp_mappings__delete__%s' % mapping.id}
        res = self.client.post(MAPPINGS_INDEX_URL, formData)

        self.assertNoFormErrors(res)
