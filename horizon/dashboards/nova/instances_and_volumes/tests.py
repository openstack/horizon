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

from horizon import api
from horizon import test


class InstancesAndVolumesViewTest(test.TestCase):
    @test.create_stubs({api: ('flavor_list', 'server_list', 'volume_list',)})
    def test_index(self):
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

    @test.create_stubs({api: ('flavor_list', 'server_list', 'volume_list',)})
    def test_attached_volume(self):
        api.flavor_list(IsA(http.HttpRequest)).AndReturn(self.flavors.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.volume_list(IsA(http.HttpRequest)) \
                .AndReturn(self.volumes.list()[1:3])

        self.mox.ReplayAll()

        res = self.client.get(
            reverse('horizon:nova:instances_and_volumes:index'))

        self.assertTemplateUsed(res,
            'nova/instances_and_volumes/index.html')
        instances = res.context['instances_table'].data
        resp_volumes = res.context['volumes_table'].data

        self.assertItemsEqual(instances, self.servers.list())
        self.assertItemsEqual(resp_volumes, self.volumes.list()[1:3])

        self.assertContains(res, ">My Volume<", 1, 200)
        self.assertContains(res, ">30GB<", 1, 200)
        self.assertContains(res, ">3b189ac8-9166-ac7f-90c9-16c8bf9e01ac<",
                            1,
                            200)
        self.assertContains(res, ">10GB<", 1, 200)
        self.assertContains(res, ">In-Use<", 2, 200)
        self.assertContains(res, "on /dev/hda", 1, 200)
        self.assertContains(res, "on /dev/hdk", 1, 200)

    @test.create_stubs({api: ('server_list', 'volume_list',)})
    def test_index_server_list_exception(self):
        api.server_list(IsA(http.HttpRequest)).AndRaise(self.exceptions.nova)
        api.volume_list(IsA(http.HttpRequest)).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())

        self.mox.ReplayAll()

        res = self.client.get(
                reverse('horizon:nova:instances_and_volumes:index'))

        self.assertTemplateUsed(res,
                'nova/instances_and_volumes/index.html')
        self.assertEqual(len(res.context['instances_table'].data), 0)
