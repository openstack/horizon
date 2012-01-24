# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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
from openstackx.api import exceptions as api_exceptions

from horizon import api
from horizon import test


class InstancesAndVolumesViewTest(test.BaseViewTests):
    def setUp(self):
        super(InstancesAndVolumesViewTest, self).setUp()
        server = api.Server(None, self.request)
        server.id = 1
        server.name = 'serverName'
        server.status = "ACTIVE"

        volume = api.Volume(self.request)
        volume.id = 1
        volume.size = 10
        volume.attachments = [{}]

        self.servers = (server,)
        self.volumes = (volume,)

    def test_index(self):
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers)
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes)

        self.mox.ReplayAll()

        res = self.client.get(
            reverse('horizon:nova:instances_and_volumes:index'))

        self.assertTemplateUsed(res,
            'nova/instances_and_volumes/index.html')
        instances = res.context['instances_table'].data
        self.assertItemsEqual(instances, self.servers)

    def test_index_server_list_exception(self):
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        exception = api_exceptions.ApiException('apiException')
        api.server_list(IsA(http.HttpRequest)).AndRaise(exception)
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes)

        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:instances_and_volumes:index'))

        self.assertTemplateUsed(res,
                'nova/instances_and_volumes/index.html')
        self.assertEqual(len(res.context['instances_table'].data), 0)
