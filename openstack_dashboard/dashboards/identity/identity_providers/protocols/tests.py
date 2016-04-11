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


IDPS_DETAIL_URL = reverse('horizon:identity:identity_providers:detail',
                          args=['idp_1'])
PROTOCOLS_CREATE_URL = reverse(
    'horizon:identity:identity_providers:protocols:create',
    args=['idp_1'])


class ProtocolsViewTests(test.BaseAdminViewTests):

    @test.create_stubs({api.keystone: ('mapping_list',
                                       'protocol_create', )})
    def test_create(self):
        idp = self.identity_providers.first()
        protocol = self.idp_protocols.first()

        api.keystone.mapping_list(IgnoreArg()). \
            AndReturn(self.idp_mappings.list())
        api.keystone.protocol_create(IgnoreArg(),
                                     protocol.id,
                                     idp.id,
                                     protocol.mapping_id). \
            AndReturn(protocol)

        self.mox.ReplayAll()

        formData = {'method': 'AddProtocolForm',
                    'id': protocol.id,
                    'idp_id': idp.id,
                    'mapping_id': protocol.mapping_id}
        res = self.client.post(PROTOCOLS_CREATE_URL, formData)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.keystone: ('identity_provider_get',
                                       'protocol_list',
                                       'protocol_delete')})
    def test_delete(self):
        idp = self.identity_providers.first()
        protocol = self.idp_protocols.first()

        api.keystone.identity_provider_get(IsA(http.HttpRequest), idp.id). \
            AndReturn(idp)
        api.keystone.protocol_list(IsA(http.HttpRequest), idp.id). \
            AndReturn(self.idp_protocols.list())
        api.keystone.protocol_delete(IsA(http.HttpRequest),
                                     idp.id,
                                     protocol.id).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'action': 'idp_protocols__delete__%s' % protocol.id}
        res = self.client.post(IDPS_DETAIL_URL, formData)

        self.assertNoFormErrors(res)
