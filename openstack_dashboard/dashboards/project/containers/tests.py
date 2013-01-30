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

import tempfile

from django import http
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.urlresolvers import reverse

from mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from .tables import ContainersTable, ObjectsTable, wrap_delimiter
from . import forms


CONTAINER_INDEX_URL = reverse('horizon:project:containers:index')


class SwiftTests(test.TestCase):
    @test.create_stubs({api.swift: ('swift_get_containers',)})
    def test_index_no_container_selected(self):
        containers = self.containers.list()
        api.swift.swift_get_containers(IsA(http.HttpRequest), marker=None) \
            .AndReturn((containers, False))
        self.mox.ReplayAll()

        res = self.client.get(CONTAINER_INDEX_URL)

        self.assertTemplateUsed(res, 'project/containers/index.html')
        self.assertIn('table', res.context)
        resp_containers = res.context['table'].data
        self.assertEqual(len(resp_containers), len(containers))

    @test.create_stubs({api.swift: ('swift_delete_container',)})
    def test_delete_container(self):
        container = self.containers.get(name=u"container_two\u6346")
        api.swift.swift_delete_container(IsA(http.HttpRequest), container.name)
        self.mox.ReplayAll()

        action_string = u"containers__delete__%s" % container.name
        form_data = {"action": action_string}
        req = self.factory.post(CONTAINER_INDEX_URL, form_data)
        table = ContainersTable(req, self.containers.list())
        handled = table.maybe_handle()
        self.assertEqual(handled['location'], CONTAINER_INDEX_URL)

    @test.create_stubs({api.swift: ('swift_delete_container',)})
    def test_delete_container_nonempty(self):
        container = self.containers.first()
        exc = self.exceptions.swift
        exc.silence_logging = True
        api.swift.swift_delete_container(IsA(http.HttpRequest),
                                         container.name).AndRaise(exc)
        self.mox.ReplayAll()

        action_string = u"containers__delete__%s" % container.name
        form_data = {"action": action_string}
        req = self.factory.post(CONTAINER_INDEX_URL, form_data)
        table = ContainersTable(req, self.containers.list())
        handled = table.maybe_handle()
        self.assertEqual(handled['location'], CONTAINER_INDEX_URL)

    def test_create_container_get(self):
        res = self.client.get(reverse('horizon:project:containers:create'))
        self.assertTemplateUsed(res, 'project/containers/create.html')

    @test.create_stubs({api.swift: ('swift_create_container',)})
    def test_create_container_post(self):
        api.swift.swift_create_container(IsA(http.HttpRequest),
                                         self.containers.first().name)
        self.mox.ReplayAll()

        formData = {'name': self.containers.first().name,
                    'method': forms.CreateContainer.__name__}
        res = self.client.post(reverse('horizon:project:containers:create'),
                               formData)
        url = reverse('horizon:project:containers:index',
                      args=[wrap_delimiter(self.containers.first().name)])
        self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.swift: ('swift_get_containers',
                                    'swift_get_objects')})
    def test_index_container_selected(self):
        containers = (self.containers.list(), False)
        ret = (self.objects.list(), False)
        api.swift.swift_get_containers(IsA(http.HttpRequest),
                                       marker=None).AndReturn(containers)
        api.swift.swift_get_objects(IsA(http.HttpRequest),
                                    self.containers.first().name,
                                    marker=None,
                                    prefix=None).AndReturn(ret)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:containers:index',
                                      args=[wrap_delimiter(self.containers
                                                               .first()
                                                               .name)]))
        self.assertTemplateUsed(res, 'project/containers/index.html')
        # UTF8 encoding here to ensure there aren't problems with Nose output.
        expected = [obj.name.encode('utf8') for obj in self.objects.list()]
        self.assertQuerysetEqual(res.context['objects_table'].data,
                                 expected,
                                 lambda obj: obj.name.encode('utf8'))

    @test.create_stubs({api.swift: ('swift_upload_object',)})
    def test_upload(self):
        container = self.containers.first()
        obj = self.objects.first()
        OBJECT_DATA = 'objectData'

        temp_file = tempfile.TemporaryFile()
        temp_file.write(OBJECT_DATA)
        temp_file.flush()
        temp_file.seek(0)

        api.swift.swift_upload_object(IsA(http.HttpRequest),
                                      container.name,
                                      obj.name,
                                      IsA(InMemoryUploadedFile)).AndReturn(obj)
        self.mox.ReplayAll()

        upload_url = reverse('horizon:project:containers:object_upload',
                             args=[container.name])

        res = self.client.get(upload_url)
        self.assertTemplateUsed(res, 'project/containers/upload.html')

        res = self.client.get(upload_url)
        self.assertContains(res, 'enctype="multipart/form-data"')

        formData = {'method': forms.UploadObject.__name__,
                    'container_name': container.name,
                    'name': obj.name,
                    'object_file': temp_file}
        res = self.client.post(upload_url, formData)

        index_url = reverse('horizon:project:containers:index',
                            args=[wrap_delimiter(container.name)])
        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_delete_object',)})
    def test_delete(self):
        container = self.containers.first()
        obj = self.objects.first()
        index_url = reverse('horizon:project:containers:index',
                            args=[wrap_delimiter(container.name)])
        api.swift.swift_delete_object(IsA(http.HttpRequest),
                                      container.name,
                                      obj.name)
        self.mox.ReplayAll()

        action_string = "objects__delete_object__%s" % obj.name
        form_data = {"action": action_string}
        req = self.factory.post(index_url, form_data)
        kwargs = {"container_name": container.name}
        table = ObjectsTable(req, self.objects.list(), **kwargs)
        handled = table.maybe_handle()
        self.assertEqual(handled['location'], index_url)

    @test.create_stubs({api.swift: ('swift_get_object',)})
    def test_download(self):
        container = self.containers.first()
        obj = self.objects.first()

        api.swift.swift_get_object(IsA(http.HttpRequest),
                                   container.name,
                                   obj.name).AndReturn(obj)
        self.mox.ReplayAll()

        download_url = reverse('horizon:project:containers:object_download',
                               args=[container.name, obj.name])
        res = self.client.get(download_url)
        self.assertEqual(res.content, obj.data)
        self.assertTrue(res.has_header('Content-Disposition'))

    @test.create_stubs({api.swift: ('swift_get_containers',)})
    def test_copy_index(self):
        ret = (self.containers.list(), False)
        api.swift.swift_get_containers(IsA(http.HttpRequest)).AndReturn(ret)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:containers:object_copy',
                                      args=[self.containers.first().name,
                                            self.objects.first().name]))
        self.assertTemplateUsed(res, 'project/containers/copy.html')

    @test.create_stubs({api.swift: ('swift_get_containers',
                                    'swift_copy_object')})
    def test_copy(self):
        container_1 = self.containers.get(name=u"container_one\u6346")
        container_2 = self.containers.get(name=u"container_two\u6346")
        obj = self.objects.first()

        ret = (self.containers.list(), False)
        api.swift.swift_get_containers(IsA(http.HttpRequest)).AndReturn(ret)
        api.swift.swift_copy_object(IsA(http.HttpRequest),
                                    container_1.name,
                                    obj.name,
                                    container_2.name,
                                    obj.name)
        self.mox.ReplayAll()

        formData = {'method': forms.CopyObject.__name__,
                    'new_container_name': container_2.name,
                    'new_object_name': obj.name,
                    'orig_container_name': container_1.name,
                    'orig_object_name': obj.name}
        copy_url = reverse('horizon:project:containers:object_copy',
                           args=[container_1.name, obj.name])
        res = self.client.post(copy_url, formData)
        index_url = reverse('horizon:project:containers:index',
                            args=[wrap_delimiter(container_2.name)])
        self.assertRedirectsNoFollow(res, index_url)
