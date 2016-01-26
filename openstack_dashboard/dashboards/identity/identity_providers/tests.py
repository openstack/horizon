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

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IgnoreArg  # noqa
from mox3.mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


IDPS_INDEX_URL = reverse('horizon:identity:identity_providers:index')
IDPS_REGISTER_URL = reverse('horizon:identity:identity_providers:register')
IDPS_UPDATE_URL = reverse('horizon:identity:identity_providers:update',
                          args=['idp_1'])


class IdPsViewTests(test.BaseAdminViewTests):
    @test.create_stubs({api.keystone: ('identity_provider_list',)})
    def test_index(self):
        api.keystone.identity_provider_list(IgnoreArg()). \
            AndReturn(self.identity_providers.list())

        self.mox.ReplayAll()

        res = self.client.get(IDPS_INDEX_URL)

        self.assertTemplateUsed(res, 'identity/identity_providers/index.html')
        self.assertItemsEqual(res.context['table'].data,
                              self.identity_providers.list())

    @test.create_stubs({api.keystone: ('identity_provider_create', )})
    def test_create(self):
        idp = self.identity_providers.first()

        api.keystone.identity_provider_create(IgnoreArg(),
                                              idp.id,
                                              description=idp.description,
                                              enabled=idp.enabled,
                                              remote_ids=idp.remote_ids). \
            AndReturn(idp)

        self.mox.ReplayAll()

        formData = {'method': 'RegisterIdPForm',
                    'id': idp.id,
                    'description': idp.description,
                    'enabled': idp.enabled,
                    'remote_ids': ', '.join(idp.remote_ids)}
        res = self.client.post(IDPS_REGISTER_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('identity_provider_get',
                                       'identity_provider_update')})
    def test_update(self):
        idp = self.identity_providers.first()
        new_description = 'new_idp_desc'

        api.keystone.identity_provider_get(IsA(http.HttpRequest), idp.id). \
            AndReturn(idp)
        api.keystone.identity_provider_update(IsA(http.HttpRequest),
                                              idp.id,
                                              description=new_description,
                                              enabled=idp.enabled,
                                              remote_ids=idp.remote_ids). \
            AndReturn(None)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateIdPForm',
                    'id': idp.id,
                    'description': new_description,
                    'enabled': idp.enabled,
                    'remote_ids': ', '.join(idp.remote_ids)}

        res = self.client.post(IDPS_UPDATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('identity_provider_list',
                                       'identity_provider_delete')})
    def test_delete(self):
        idp = self.identity_providers.first()

        api.keystone.identity_provider_list(IsA(http.HttpRequest)) \
            .AndReturn(self.identity_providers.list())
        api.keystone.identity_provider_delete(IsA(http.HttpRequest),
                                              idp.id).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'action': 'identity_providers__delete__%s' % idp.id}
        res = self.client.post(IDPS_INDEX_URL, formData)

        self.assertNoFormErrors(res)
