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

from django.core.urlresolvers import reverse

from horizon import test


INDEX_URL = reverse('horizon:syspanel:services:index')


class ServicessViewTests(test.BaseAdminViewTests):
    def test_index(self):
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'syspanel/services/index.html')
        self.assertQuerysetEqual(res.context['table'].data,
                                 ['<Service: compute>',
                                  '<Service: volume>',
                                  '<Service: image>',
                                  '<Service: identity (native backend)>',
                                  '<Service: object-store>',
                                  '<Service: network>',
                                  '<Service: ec2>'])
