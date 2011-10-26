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

from cloudfiles.errors import ContainerNotEmpty
from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django_openstack import api
from django_openstack.tests.view_tests import base
from mox import IgnoreArg, IsA


class ContainerViewTests(base.BaseViewTests):
    def setUp(self):
        super(ContainerViewTests, self).setUp()
        self.container = self.mox.CreateMock(api.Container)
        self.container.name = 'containerName'

    def test_index(self):
        self.mox.StubOutWithMock(api, 'swift_get_containers')
        api.swift_get_containers(
                IsA(http.HttpRequest), marker=None).AndReturn([self.container])

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_containers', args=['tenant']))

        self.assertTemplateUsed(res,
                'django_openstack/dash/containers/index.html')
        self.assertIn('containers', res.context)
        containers = res.context['containers']

        self.assertEqual(len(containers), 1)
        self.assertEqual(containers[0].name, 'containerName')

        self.mox.VerifyAll()

    def test_delete_container(self):
        formData = {'container_name': 'containerName',
                    'method': 'DeleteContainer'}

        self.mox.StubOutWithMock(api, 'swift_delete_container')
        api.swift_delete_container(IsA(http.HttpRequest),
                                   'containerName')

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_containers', args=['tenant']),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_containers',
                                                  args=['tenant']))

        self.mox.VerifyAll()

    def test_delete_container_nonempty(self):
        formData = {'container_name': 'containerName',
                          'method': 'DeleteContainer'}

        exception = ContainerNotEmpty('containerNotEmpty')

        self.mox.StubOutWithMock(api, 'swift_delete_container')
        api.swift_delete_container(
                IsA(http.HttpRequest),
                'containerName').AndRaise(exception)

        self.mox.StubOutWithMock(messages, 'error')

        messages.error(IgnoreArg(), IsA(unicode))

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_containers', args=['tenant']),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_containers',
                                          args=['tenant']))

        self.mox.VerifyAll()

    def test_create_container_get(self):
        res = self.client.get(reverse('dash_containers_create',
                              args=['tenant']))

        self.assertTemplateUsed(res,
                'django_openstack/dash/containers/create.html')

    def test_create_container_post(self):
        formData = {'name': 'containerName',
                    'method': 'CreateContainer'}

        self.mox.StubOutWithMock(api, 'swift_create_container')
        api.swift_create_container(
                IsA(http.HttpRequest), 'CreateContainer')

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(basestring))

        res = self.client.post(reverse('dash_containers_create',
                                       args=[self.request.user.tenant_id]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_containers',
                                          args=[self.request.user.tenant_id]))
