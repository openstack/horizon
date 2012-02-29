# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from django import http
from django.core.urlresolvers import reverse
from mox import IsA
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import test


class InstancesAndVolumesViewTest(test.TestCase):
    def test_index(self):
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())

        self.mox.ReplayAll()

        res = self.client.get(
            reverse('horizon:nova:instances_and_volumes:index'))

        self.assertTemplateUsed(res,
            'nova/instances_and_volumes/index.html')
        instances = res.context['instances_table'].data
        self.assertItemsEqual(instances, self.servers.list())

    def test_index_server_list_exception(self):
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        exception = novaclient_exceptions.ClientException('apiException')
        api.server_list(IsA(http.HttpRequest)).AndRaise(exception)
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())

        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:instances_and_volumes:index'))

        self.assertTemplateUsed(res,
                'nova/instances_and_volumes/index.html')
        self.assertEqual(len(res.context['instances_table'].data), 0)
