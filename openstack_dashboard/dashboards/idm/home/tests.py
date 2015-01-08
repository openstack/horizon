# Copyright (C) 2014 Universidad Politecnica de Madrid
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

from mox import IgnoreArg
from mox import IsA  # noqa

from django import http
from django.core.urlresolvers import reverse

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.test import helpers as test
from openstack_dashboard.dashboards.idm import tests as idm_tests


INDEX_URL = reverse('horizon:idm:home:index')

class HomeTests(idm_tests.BaseTestCase):

    @test.create_stubs({
        api.keystone: (
            'tenant_list',
        ),
        fiware_api.keystone: ( 
            'application_list',
        ),
    })
    def test_index(self):
        organizations = self.list_organizations()
        applications = self.applications.list()

        api.keystone.tenant_list(IsA(http.HttpRequest),
                                user=self.user.id,
                                admin=False).AndReturn((organizations, False))
        fiware_api.keystone.application_list(IsA(http.HttpRequest)
                                            ).AndReturn(applications)
        self.mox.ReplayAll()

        response = self.client.get(INDEX_URL)
        self.assertTemplateUsed(response, 'idm/organizations/index.html')
        self.assertItemsEqual(response.context['organizations_table'].data, 
                                    organizations)
        self.assertItemsEqual(response.context['applications_table'].data, 
                                    applications)
        self.assertNoMessages()
