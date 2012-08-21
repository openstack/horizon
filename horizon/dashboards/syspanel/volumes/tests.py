# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


class VolumeTests(test.BaseAdminViewTests):
    @test.create_stubs({api: ('server_list', 'volume_list',)})
    def test_index(self):
        api.volume_list(IsA(http.HttpRequest), search_opts={
                            'all_tenants': 1}).AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:syspanel:volumes:index'))

        self.assertTemplateUsed(res, 'syspanel/volumes/index.html')
        volumes = res.context['volumes_table'].data

        self.assertItemsEqual(volumes, self.volumes.list())
