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

from django import http
from django.core.urlresolvers import reverse
from django_openstack import api
from django_openstack.tests.view_tests import base
from mox import IsA


class ObjectViewTests(base.BaseViewTests):
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

        res = self.client.get(reverse('dash_objects',
                                      args=[self.TEST_TENANT,
                                            self.CONTAINER_NAME]))
        self.assertTemplateUsed(res,
                'django_openstack/dash/objects/index.html')
        self.assertItemsEqual(res.context['objects'], self.swift_objects)

        self.mox.VerifyAll()

    def test_upload_index(self):
        res = self.client.get(reverse('dash_objects_upload',
                                      args=[self.TEST_TENANT,
                                            self.CONTAINER_NAME]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/objects/upload.html')

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

        res = self.client.post(reverse('dash_objects_upload',
                                       args=[self.TEST_TENANT,
                                             self.CONTAINER_NAME]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_objects_upload',
                                                  args=[self.TEST_TENANT,
                                                        self.CONTAINER_NAME]))

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

        res = self.client.post(reverse('dash_objects',
                                       args=[self.TEST_TENANT,
                                             self.CONTAINER_NAME]),
                               formData)

        self.assertRedirectsNoFollow(res, reverse('dash_objects',
                                                  args=[self.TEST_TENANT,
                                                        self.CONTAINER_NAME]))

        self.mox.VerifyAll()

    def test_download(self):
        OBJECT_DATA = 'objectData'
        OBJECT_NAME = 'objectName'

        self.mox.StubOutWithMock(api, 'swift_get_object_data')
        api.swift_get_object_data(IsA(http.HttpRequest),
                                  unicode(self.CONTAINER_NAME),
                                  unicode(OBJECT_NAME)).AndReturn(OBJECT_DATA)

        self.mox.ReplayAll()

        res = self.client.get(reverse('dash_objects_download',
                                      args=[self.TEST_TENANT,
                                            self.CONTAINER_NAME,
                                            OBJECT_NAME]))

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

        res = self.client.get(reverse('dash_object_copy',
                                      args=[self.TEST_TENANT,
                                            self.CONTAINER_NAME,
                                            OBJECT_NAME]))

        self.assertTemplateUsed(res,
                'django_openstack/dash/objects/copy.html')

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

        res = self.client.post(reverse('dash_object_copy',
                                       args=[self.TEST_TENANT,
                                             ORIG_CONTAINER_NAME,
                                             ORIG_OBJECT_NAME]),
                              formData)

        self.assertRedirectsNoFollow(res, reverse('dash_object_copy',
                                                  args=[self.TEST_TENANT,
                                                        ORIG_CONTAINER_NAME,
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
                              prefix=unicode(PREFIX)
                             ).AndReturn(self.swift_objects)

        self.mox.ReplayAll()

        res = self.client.post(reverse('dash_objects',
                                       args=[self.TEST_TENANT,
                                             self.CONTAINER_NAME]),
                               formData)

        self.assertTemplateUsed(res,
                'django_openstack/dash/objects/index.html')

        self.mox.VerifyAll()
