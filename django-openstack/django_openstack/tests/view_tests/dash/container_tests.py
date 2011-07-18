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
        container_inner = base.Object()
        container_inner.name = 'containerName'
        self.container = api.Container(container_inner)

    def test_index(self):
        self.mox.StubOutWithMock(api, 'swift_get_containers')
        api.swift_get_containers(
                IsA(http.HttpRequest)).AndReturn([self.container])

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_containers', args=['tenant']))

        self.assertTemplateUsed(res, 'dash_containers.html')
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

        self.assertTemplateUsed(res, 'dash_containers_create.html')

    def test_create_container_post(self):
        formData = {'name': 'containerName',
                    'method': 'CreateContainer'}

        self.mox.StubOutWithMock(api, 'swift_create_container')
        api.swift_create_container(
                IsA(http.HttpRequest), 'CreateContainer')

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(str))

        res = self.client.post(reverse('dash_containers_create',
                                       args=[self.request.user.tenant]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_containers',
                                          args=[self.request.user.tenant]))
