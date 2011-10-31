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

import tempfile

from cloudfiles.errors import ContainerNotEmpty
from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from mox import IgnoreArg, IsA

from horizon import api
from horizon import test


CONTAINER_INDEX_URL = reverse('horizon:nova:containers:index')


class ContainerViewTests(test.BaseViewTests):
    def setUp(self):
        super(ContainerViewTests, self).setUp()
        self.container = self.mox.CreateMock(api.Container)
        self.container.name = 'containerName'

    def test_index(self):
        self.mox.StubOutWithMock(api, 'swift_get_containers')
        api.swift_get_containers(
                IsA(http.HttpRequest), marker=None).AndReturn([self.container])

        self.mox.ReplayAll()

        res = self.client.get(CONTAINER_INDEX_URL)

        self.assertTemplateUsed(res, 'nova/containers/index.html')
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

        res = self.client.post(CONTAINER_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, CONTAINER_INDEX_URL)

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

        res = self.client.post(CONTAINER_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, CONTAINER_INDEX_URL)

        self.mox.VerifyAll()

    def test_create_container_get(self):
        res = self.client.get(reverse('horizon:nova:containers:create'))

        self.assertTemplateUsed(res, 'nova/containers/create.html')

    def test_create_container_post(self):
        formData = {'name': 'containerName',
                    'method': 'CreateContainer'}

        self.mox.StubOutWithMock(api, 'swift_create_container')
        api.swift_create_container(
                IsA(http.HttpRequest), 'CreateContainer')

        self.mox.StubOutWithMock(messages, 'success')
        messages.success(IgnoreArg(), IsA(basestring))

        res = self.client.post(reverse('horizon:nova:containers:create'),
                               formData)

        self.assertRedirectsNoFollow(res, CONTAINER_INDEX_URL)


class ObjectViewTests(test.BaseViewTests):
    CONTAINER_NAME = 'containerName'

    def setUp(self):
        super(ObjectViewTests, self).setUp()
        swift_object = self.mox.CreateMock(api.SwiftObject)
        self.swift_objects = [swift_object]

    def test_index(self):
        self.mox.StubOutWithMock(api, 'swift_get_objects')
        api.swift_get_objects(
                IsA(http.HttpRequest),
                self.CONTAINER_NAME,
                marker=None).AndReturn(self.swift_objects)

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:containers:object_index',
                                      args=[self.CONTAINER_NAME]))
        self.assertTemplateUsed(res, 'nova/objects/index.html')
        self.assertItemsEqual(res.context['objects'], self.swift_objects)

        self.mox.VerifyAll()

    def test_upload_index(self):
        res = self.client.get(reverse('horizon:nova:containers:object_upload',
                                      args=[self.CONTAINER_NAME]))

        self.assertTemplateUsed(res, 'nova/objects/upload.html')

    def test_upload(self):
        OBJECT_DATA = 'objectData'
        OBJECT_FILE = tempfile.TemporaryFile()
        OBJECT_FILE.write(OBJECT_DATA)
        OBJECT_FILE.flush()
        OBJECT_FILE.seek(0)
        OBJECT_NAME = 'objectName'

        formData = {'method': 'UploadObject',
                    'container_name': self.CONTAINER_NAME,
                    'name': OBJECT_NAME,
                    'object_file': OBJECT_FILE}

        self.mox.StubOutWithMock(api, 'swift_upload_object')
        api.swift_upload_object(IsA(http.HttpRequest),
                                unicode(self.CONTAINER_NAME),
                                unicode(OBJECT_NAME),
                                OBJECT_DATA)

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:containers:object_upload',
                                       args=[self.CONTAINER_NAME]),
                               formData)

        self.assertRedirectsNoFollow(res,
                            reverse('horizon:nova:containers:object_upload',
                                    args=[self.CONTAINER_NAME]))

        self.mox.VerifyAll()

    def test_delete(self):
        OBJECT_NAME = 'objectName'
        formData = {'method': 'DeleteObject',
                    'container_name': self.CONTAINER_NAME,
                    'object_name': OBJECT_NAME}

        self.mox.StubOutWithMock(api, 'swift_delete_object')
        api.swift_delete_object(
                IsA(http.HttpRequest),
                self.CONTAINER_NAME, OBJECT_NAME)

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:containers:object_index',
                                       args=[self.CONTAINER_NAME]),
                               formData)

        self.assertRedirectsNoFollow(res,
                                reverse('horizon:nova:containers:object_index',
                                        args=[self.CONTAINER_NAME]))

        self.mox.VerifyAll()

    def test_download(self):
        OBJECT_DATA = 'objectData'
        OBJECT_NAME = 'objectName'

        self.mox.StubOutWithMock(api, 'swift_get_object_data')
        api.swift_get_object_data(IsA(http.HttpRequest),
                                  unicode(self.CONTAINER_NAME),
                                  unicode(OBJECT_NAME)).AndReturn(OBJECT_DATA)

        self.mox.ReplayAll()

        res = self.client.get(reverse(
                            'horizon:nova:containers:object_download',
                            args=[self.CONTAINER_NAME, OBJECT_NAME]))

        self.assertEqual(res.content, OBJECT_DATA)
        self.assertTrue(res.has_header('Content-Disposition'))

        self.mox.VerifyAll()

    def test_copy_index(self):
        OBJECT_NAME = 'objectName'

        container = self.mox.CreateMock(api.Container)
        container.name = self.CONTAINER_NAME

        self.mox.StubOutWithMock(api, 'swift_get_containers')
        api.swift_get_containers(
                IsA(http.HttpRequest)).AndReturn([container])

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:containers:object_copy',
                                      args=[self.CONTAINER_NAME,
                                            OBJECT_NAME]))

        self.assertTemplateUsed(res, 'nova/objects/copy.html')

        self.mox.VerifyAll()

    def test_copy(self):
        NEW_CONTAINER_NAME = self.CONTAINER_NAME
        NEW_OBJECT_NAME = 'newObjectName'
        ORIG_CONTAINER_NAME = 'origContainerName'
        ORIG_OBJECT_NAME = 'origObjectName'

        formData = {'method': 'CopyObject',
                    'new_container_name': NEW_CONTAINER_NAME,
                    'new_object_name': NEW_OBJECT_NAME,
                    'orig_container_name': ORIG_CONTAINER_NAME,
                    'orig_object_name': ORIG_OBJECT_NAME}

        container = self.mox.CreateMock(api.Container)
        container.name = self.CONTAINER_NAME

        self.mox.StubOutWithMock(api, 'swift_get_containers')
        api.swift_get_containers(
                IsA(http.HttpRequest)).AndReturn([container])

        self.mox.StubOutWithMock(api, 'swift_copy_object')
        api.swift_copy_object(IsA(http.HttpRequest),
                              ORIG_CONTAINER_NAME,
                              ORIG_OBJECT_NAME,
                              NEW_CONTAINER_NAME,
                              NEW_OBJECT_NAME)

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:containers:object_copy',
                                       args=[ORIG_CONTAINER_NAME,
                                             ORIG_OBJECT_NAME]),
                              formData)

        self.assertRedirectsNoFollow(res,
                            reverse('horizon:nova:containers:object_copy',
                                    args=[ORIG_CONTAINER_NAME,
                                          ORIG_OBJECT_NAME]))

        self.mox.VerifyAll()

    def test_filter(self):
        PREFIX = 'prefix'

        formData = {'method': 'FilterObjects',
                    'container_name': self.CONTAINER_NAME,
                    'object_prefix': PREFIX,
                    }

        self.mox.StubOutWithMock(api, 'swift_get_objects')
        api.swift_get_objects(IsA(http.HttpRequest),
                              unicode(self.CONTAINER_NAME),
                              prefix=unicode(PREFIX))\
                              .AndReturn(self.swift_objects)

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:containers:object_index',
                                       args=[self.CONTAINER_NAME]),
                               formData)

        self.assertTemplateUsed(res, 'nova/objects/index.html')

        self.mox.VerifyAll()
