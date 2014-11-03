# Copyright (C) 2014 Universidad Politecnica de Madrid
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

from mox import IsA  # noqa

from django import http
from django.core.urlresolvers import reverse

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:settings:cancelaccount:index')

class CancelaccountTests(test.TestCase):

    @test.create_stubs({
        api.keystone: ('user_update_enabled',
                    'keystone_can_edit_user',)
    })
    def test_account_cancel(self):
        user = self.user
        api.keystone.keystone_can_edit_user().AndReturn(True)
        api.keystone.user_update_enabled(
                                IsA(http.HttpRequest),
                                user.id,
                                enabled=False).AndReturn(None)
        self.mox.ReplayAll()

        form_data = {
            'method': 'BasicCancelForm',
        }

        response = self.client.post(INDEX_URL, form_data)
        self.assertNoFormErrors(response)
        # don't pass response to assertMessageCount because it's a redirect,
        # leave it default (None) to check the internal request object
        self.assertMessageCount(success=1)