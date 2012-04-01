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


class VolumeViewTests(test.TestCase):
    def test_edit_attachments(self):
        volume = self.volumes.first()
        servers = self.servers.list()
        self.mox.StubOutWithMock(api, 'volume_get')
        self.mox.StubOutWithMock(api.nova, 'server_list')
        api.volume_get(IsA(http.HttpRequest), volume.id) \
                       .AndReturn(volume)
        api.nova.server_list(IsA(http.HttpRequest)).AndReturn(servers)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:volumes:attach',
                      args=[volume.id])
        res = self.client.get(url)
        # Asserting length of 2 accounts for the one instance option,
        # and the one 'Choose Instance' option.
        self.assertEqual(len(res.context['form'].fields['instance']._choices),
                         2)
        self.assertEqual(res.status_code, 200)

    def test_detail_view(self):
        volume = self.volumes.first()
        server = self.servers.first()
        volume.attachments = [{"server_id": server.id}]
        self.mox.StubOutWithMock(api.nova, 'volume_get')
        self.mox.StubOutWithMock(api.nova, 'server_get')
        api.nova.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:instances_and_volumes:volumes:detail',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertContains(res, "<dd>Volume name</dd>", 1, 200)
        self.assertContains(res, "<dd>1</dd>", 1, 200)
        self.assertContains(res, "<dd>Available</dd>", 1, 200)
        self.assertContains(res, "<dd>40 GB</dd>", 1, 200)
        self.assertContains(res, "<dd>04/01/12 at 10:30:00</dd>", 1, 200)
        self.assertContains(res, "<a href=\"/nova/instances_and_volumes/"
                            "instances/1/detail\">Instance server_1 "
                            "(1)</a>", 1, 200)

        self.assertNoMessages()
