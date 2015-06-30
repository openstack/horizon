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

from saharaclient import client as sahara_client

from openstack_dashboard.test import helpers

from openstack_dashboard.contrib.sahara import api


class SaharaAPITestCase(helpers.APITestCase):

    def setUp(self):
        super(SaharaAPITestCase, self).setUp()

        self._original_saharaclient = api.sahara.client
        api.sahara.client = lambda request: self.stub_saharaclient()

    def tearDown(self):
        super(SaharaAPITestCase, self).tearDown()

        api.sahara.client = self._original_saharaclient

    def stub_saharaclient(self):
        if not hasattr(self, "saharaclient"):
            self.mox.StubOutWithMock(sahara_client, 'Client')
            self.saharaclient = self.mox.CreateMock(sahara_client.Client)
        return self.saharaclient
