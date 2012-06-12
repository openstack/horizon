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

from copy import deepcopy
from django import http
from django.core.urlresolvers import reverse
from mox import IsA

from horizon import api
from horizon import test


class InstancesAndVolumesViewTest(test.TestCase):
    def test_index(self):
        self.mox.StubOutWithMock(api, 'flavor_list')
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())

        self.mox.ReplayAll()

        res = self.client.get(
            reverse('horizon:nova:instances_and_volumes:index'))

        self.assertTemplateUsed(res,
            'nova/instances_and_volumes/index.html')
        instances = res.context['instances_table'].data
        volumes = res.context['volumes_table'].data

        self.assertItemsEqual(instances, self.servers.list())
        self.assertItemsEqual(volumes, self.volumes.list())

    def test_attached_volume(self):
        volumes = deepcopy(self.volumes.list())
        attached_volume = deepcopy(self.volumes.list()[0])
        attached_volume.id = "2"
        attached_volume.display_name = "Volume2 name"
        attached_volume.size = "80"
        attached_volume.status = "in-use"
        attached_volume.attachments = [{"server_id": "1",
                                        "device": "/dev/hdn"}]
        volumes.append(attached_volume)

        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        self.mox.StubOutWithMock(api, 'flavor_list')
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.volume_list(IsA(http.HttpRequest)).AndReturn(volumes)

        self.mox.ReplayAll()

        res = self.client.get(
            reverse('horizon:nova:instances_and_volumes:index'))

        self.assertTemplateUsed(res,
            'nova/instances_and_volumes/index.html')
        instances = res.context['instances_table'].data
        resp_volumes = res.context['volumes_table'].data

        self.assertItemsEqual(instances, self.servers.list())
        self.assertItemsEqual(resp_volumes, volumes)

        self.assertContains(res, ">Volume name<", 1, 200)
        self.assertContains(res, ">40GB<", 1, 200)
        self.assertContains(res, ">Available<", 1, 200)

        self.assertContains(res, ">Volume2 name<", 1, 200)
        self.assertContains(res, ">80GB<", 1, 200)
        self.assertContains(res, ">In-Use<", 1, 200)
        self.assertContains(res, ">server_1<", 2, 200)
        self.assertContains(res, "on /dev/hdn", 1, 200)

    def test_index_server_list_exception(self):
        self.mox.StubOutWithMock(api, 'server_list')
        self.mox.StubOutWithMock(api, 'volume_list')
        api.server_list(IsA(http.HttpRequest)).AndRaise(self.exceptions.nova)
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())

        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:instances_and_volumes:index'))

        self.assertTemplateUsed(res,
                'nova/instances_and_volumes/index.html')
        self.assertEqual(len(res.context['instances_table'].data), 0)
