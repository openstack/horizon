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
from django import template
from django.contrib import messages
from django.core.urlresolvers import reverse
from mox import IgnoreArg, IsA

from horizon import api
from horizon import test
from .tables import ContainersTable, ObjectsTable


CONTAINER_INDEX_URL = reverse('horizon:nova:containers:index')


class ContainerViewTests(test.BaseViewTests):
    def setUp(self):
        super(ContainerViewTests, self).setUp()
        self.container = api.Container(None)
        self.container.name = 'containerName'
        self.container.size_used = 128
        self.containers = (self.container,)

    def test_index(self):
        self.mox.StubOutWithMock(api, 'swift_get_containers')
        api.swift_get_containers(
                IsA(http.HttpRequest), marker=None).AndReturn(
                        ([self.container], False))

        self.mox.ReplayAll()

        res = self.client.get(CONTAINER_INDEX_URL)

        self.assertTemplateUsed(res, 'nova/containers/index.html')
        self.assertIn('table', res.context)
        containers = res.context['table'].data

        self.assertEqual(len(containers), 1)
        self.assertEqual(containers[0].name, 'containerName')

    def test_delete_container(self):
        self.mox.StubOutWithMock(api, 'swift_delete_container')
        api.swift_delete_container(IsA(http.HttpRequest),
                                   'containerName')

        self.mox.ReplayAll()

        action_string = "containers__delete__%s" % self.container.name
        form_data = {"action": action_string}
        req = self.factory.post(CONTAINER_INDEX_URL, form_data)
        table = ContainersTable(req, self.containers)
        handled = table.maybe_handle()

        self.assertEqual(handled['location'], CONTAINER_INDEX_URL)

    def test_delete_container_nonempty(self):
        self.mox.StubOutWithMock(api, 'swift_delete_container')

        exception = ContainerNotEmpty('containerNotEmpty')
        api.swift_delete_container(
                IsA(http.HttpRequest),
                'containerName').AndRaise(exception)

        self.mox.ReplayAll()

        action_string = "containers__delete__%s" % self.container.name
        form_data = {"action": action_string}
        req = self.factory.post(CONTAINER_INDEX_URL, form_data)
        table = ContainersTable(req, self.containers)
        handled = table.maybe_handle()

        self.assertEqual(handled['location'], CONTAINER_INDEX_URL)

    def test_create_container_get(self):
        res = self.client.get(reverse('horizon:nova:containers:create'))

        self.assertTemplateUsed(res, 'nova/containers/create.html')

    def test_create_container_post(self):
        formData = {'name': 'containerName',
                    'method': 'CreateContainer'}

        self.mox.StubOutWithMock(api, 'swift_create_container')
        api.swift_create_container(
                IsA(http.HttpRequest), u'containerName')

        self.mox.ReplayAll()

        res = self.client.post(reverse('horizon:nova:containers:create'),
                               formData)

        self.assertRedirectsNoFollow(res, CONTAINER_INDEX_URL)


class ObjectViewTests(test.BaseViewTests):
    CONTAINER_NAME = 'containerName'

    def setUp(self):
        class FakeCloudFile(object):
            def __init__(self):
                self.metadata = {}

            def sync_metadata(self):
                pass

        super(ObjectViewTests, self).setUp()
        swift_object = api.swift.SwiftObject(FakeCloudFile())
        swift_object.name = "test_object"
        swift_object.size = '128'
        swift_object.container = api.swift.Container(None)
        swift_object.container.name = 'container_name'
        self.swift_objects = [swift_object]

    def test_index(self):
        self.mox.StubOutWithMock(api, 'swift_get_objects')
        api.swift_get_objects(
                IsA(http.HttpRequest),
                self.CONTAINER_NAME,
                marker=None).AndReturn((self.swift_objects, False))

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:containers:object_index',
                                      args=[self.CONTAINER_NAME]))
        self.assertTemplateUsed(res, 'nova/objects/index.html')
        self.assertItemsEqual(res.context['table'].data, self.swift_objects)

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
                                OBJECT_DATA).AndReturn(self.swift_objects[0])

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:containers:object_upload',
                                       args=[self.CONTAINER_NAME]))

        self.assertContains(res, 'enctype="multipart/form-data"')

        res = self.client.post(reverse('horizon:nova:containers:object_upload',
                                       args=[self.CONTAINER_NAME]),
                               formData)

        self.assertRedirectsNoFollow(res,
                            reverse('horizon:nova:containers:object_index',
                                    args=[self.CONTAINER_NAME]))

    def test_delete(self):
        self.mox.StubOutWithMock(api, 'swift_delete_object')
        api.swift_delete_object(
                IsA(http.HttpRequest),
                self.CONTAINER_NAME, self.swift_objects[0].name)

        self.mox.ReplayAll()

        OBJECT_INDEX_URL = reverse('horizon:nova:containers:object_index',
                                   args=[self.CONTAINER_NAME])
        action_string = "objects__delete__%s" % self.swift_objects[0].name
        form_data = {"action": action_string}
        req = self.factory.post(OBJECT_INDEX_URL, form_data)
        kwargs = {"container_name": self.CONTAINER_NAME}
        table = ObjectsTable(req, self.swift_objects, **kwargs)
        handled = table.maybe_handle()

        self.assertEqual(handled['location'], OBJECT_INDEX_URL)

    def test_download(self):
        OBJECT_DATA = 'objectData'
        OBJECT_NAME = 'objectName'

        self.mox.StubOutWithMock(api, 'swift_get_object_data')
        self.mox.StubOutWithMock(api.swift, 'swift_get_object')

        api.swift.swift_get_object(IsA(http.HttpRequest),
                                  unicode(self.CONTAINER_NAME),
                                  unicode(OBJECT_NAME)) \
                                  .AndReturn(self.swift_objects[0])
        api.swift_get_object_data(IsA(http.HttpRequest),
                                  unicode(self.CONTAINER_NAME),
                                  unicode(OBJECT_NAME)).AndReturn(OBJECT_DATA)

        self.mox.ReplayAll()

        res = self.client.get(reverse(
                            'horizon:nova:containers:object_download',
                            args=[self.CONTAINER_NAME, OBJECT_NAME]))

        self.assertEqual(res.content, OBJECT_DATA)
        self.assertTrue(res.has_header('Content-Disposition'))

    def test_copy_index(self):
        OBJECT_NAME = 'objectName'

        container = self.mox.CreateMock(api.Container)
        container.name = self.CONTAINER_NAME

        self.mox.StubOutWithMock(api, 'swift_get_containers')
        api.swift_get_containers(
                IsA(http.HttpRequest)).AndReturn(([container], False))

        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:nova:containers:object_copy',
                                      args=[self.CONTAINER_NAME,
                                            OBJECT_NAME]))

        self.assertTemplateUsed(res, 'nova/objects/copy.html')

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
                IsA(http.HttpRequest)).AndReturn(([container], False))

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
                            reverse('horizon:nova:containers:object_index',
                                    args=[NEW_CONTAINER_NAME]))
