# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

"""
Unit tests for instance views.
"""

import boto.ec2.instance
import mox

from django.core.urlresolvers import reverse
from django_openstack.nova.tests.base import (BaseProjectViewTests,
                                              TEST_PROJECT)


TEST_INSTANCE_ID = 'i-abcdefgh'


class InstanceViewTests(BaseProjectViewTests):
    def test_index(self):
        self.mox.StubOutWithMock(self.project, 'get_instances')
        self.project.get_instances().AndReturn([])

        self.mox.ReplayAll()

        res = self.client.get(reverse('nova_instances', args=[TEST_PROJECT]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                'django_openstack/nova/instances/index.html')
        self.assertEqual(len(res.context['instances']), 0)

        self.mox.VerifyAll()

    def test_detail(self):
        instance = boto.ec2.instance.Instance()
        instance.id = TEST_INSTANCE_ID
        instance.displayName = instance.id
        instance.displayDescription = instance.id

        self.mox.StubOutWithMock(self.project, 'get_instance')
        self.project.get_instance(instance.id).AndReturn(instance)
        self.mox.StubOutWithMock(self.project, 'get_instances')
        self.project.get_instances().AndReturn([instance])

        self.mox.ReplayAll()

        res = self.client.get(reverse('nova_instances_detail',
                                     args=[TEST_PROJECT, TEST_INSTANCE_ID]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                'django_openstack/nova/instances/index.html')
        self.assertEqual(res.context['selected_instance'].id, instance.id)

        self.mox.VerifyAll()
