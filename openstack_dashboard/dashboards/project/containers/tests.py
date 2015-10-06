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

import copy
import tempfile

import django
from django.core.files.uploadedfile import InMemoryUploadedFile  # noqa
from django import http
from django.utils import http as utils_http

from mox3.mox import IsA  # noqa
import six

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.containers import forms
from openstack_dashboard.dashboards.project.containers import tables
from openstack_dashboard.dashboards.project.containers import utils
from openstack_dashboard.dashboards.project.containers import views
from openstack_dashboard.test import helpers as test

from horizon.utils.urlresolvers import reverse  # noqa


CONTAINER_NAME_1 = u"container one%\u6346"
CONTAINER_NAME_2 = u"container_two\u6346"
CONTAINER_NAME_1_QUOTED = utils_http.urlquote(CONTAINER_NAME_1)
CONTAINER_NAME_2_QUOTED = utils_http.urlquote(CONTAINER_NAME_2)
INVALID_CONTAINER_NAME_1 = utils_http.urlquote(CONTAINER_NAME_1_QUOTED)
INVALID_CONTAINER_NAME_2 = utils_http.urlquote(CONTAINER_NAME_2_QUOTED)
CONTAINER_INDEX_URL = reverse('horizon:project:containers:index')

INVALID_PATHS = []


def invalid_paths():
    if not INVALID_PATHS:
        for x in (CONTAINER_NAME_1_QUOTED, CONTAINER_NAME_2_QUOTED):
            y = reverse('horizon:project:containers:index',
                        args=(utils.wrap_delimiter(x), ))
            INVALID_PATHS.append(y)
        for x in (CONTAINER_NAME_1, CONTAINER_NAME_2):
            INVALID_PATHS.append(CONTAINER_INDEX_URL + x)
    return INVALID_PATHS


class SwiftTests(test.TestCase):

    def _test_invalid_paths(self, response):
        for x in invalid_paths():
            self.assertNotContains(response, x)

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

    @test.create_stubs({api.swift: ('swift_delete_container', )})
    def test_delete_container(self):
        for container in self.containers.list():
            self.mox.ResetAll()  # mandatory in a for loop
            api.swift.swift_delete_container(IsA(http.HttpRequest),
                                             container.name)
            self.mox.ReplayAll()

            action_string = u"containers__delete__%s" % container.name
            form_data = {"action": action_string}
            req = self.factory.post(CONTAINER_INDEX_URL, form_data)
            table = tables.ContainersTable(req, self.containers.list())
            handled = table.maybe_handle()
            self.assertEqual(handled['location'], CONTAINER_INDEX_URL)

    @test.create_stubs({api.swift: ('swift_get_objects', )})
    def test_delete_container_nonempty(self):
        container = self.containers.first()
        objects = self.objects.list()
        api.swift.swift_get_objects(IsA(http.HttpRequest),
                                    container.name).AndReturn([objects, False])
        self.mox.ReplayAll()

        action_string = u"containers__delete__%s" % container.name
        form_data = {"action": action_string}
        req = self.factory.post(CONTAINER_INDEX_URL, form_data)
        req.META['HTTP_REFERER'] = '%s/%s' % (CONTAINER_INDEX_URL,
                                              container.name)
        table = tables.ContainersTable(req, self.containers.list())
        handled = table.maybe_handle()

        self.assertEqual(handled.status_code, 302)
        self.assertEqual(six.text_type(list(req._messages)[0].message),
                         u"The container cannot be deleted "
                         u"since it is not empty.")

    def test_create_container_get(self):
        res = self.client.get(reverse('horizon:project:containers:create'))
        self.assertTemplateUsed(res, 'project/containers/create.html')

    @test.create_stubs({api.swift: ('swift_create_container',)})
    def test_create_container_post(self):
        for container in self.containers.list():
            self.mox.ResetAll()  # mandatory in a for loop
            api.swift.swift_create_container(IsA(http.HttpRequest),
                                             container.name,
                                             metadata=({'is_public': False}))
            self.mox.ReplayAll()

            formData = {'name': container.name,
                        'access': "private",
                        'method': forms.CreateContainer.__name__}
            res = self.client.post(
                reverse('horizon:project:containers:create'), formData)
            args = (utils.wrap_delimiter(container.name),)
            url = reverse('horizon:project:containers:index', args=args)
            self.assertRedirectsNoFollow(res, url)

    @test.create_stubs({api.swift: ('swift_update_container', )})
    def test_update_container_to_public(self):
        container = self.containers.get(name=u"container one%\u6346")
        api.swift.swift_update_container(IsA(http.HttpRequest),
                                         container.name,
                                         metadata=({'is_public': True}))
        self.mox.ReplayAll()

        action_string = u"containers__make_public__%s" % container.name
        form_data = {"action": action_string}
        req = self.factory.post(CONTAINER_INDEX_URL, form_data)
        table = tables.ContainersTable(req, self.containers.list())
        handled = table.maybe_handle()
        self.assertEqual(handled['location'], CONTAINER_INDEX_URL)

    @test.create_stubs({api.swift: ('swift_update_container', )})
    def test_update_container_to_private(self):
        container = self.containers.get(name=u"container_two\u6346")
        api.swift.swift_update_container(IsA(http.HttpRequest),
                                         container.name,
                                         metadata=({'is_public': False}))
        self.mox.ReplayAll()

        action_string = u"containers__make_private__%s" % container.name
        form_data = {"action": action_string}
        req = self.factory.post(CONTAINER_INDEX_URL, form_data)
        table = tables.ContainersTable(req, self.containers.list())
        handled = table.maybe_handle()
        self.assertEqual(handled['location'], CONTAINER_INDEX_URL)

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

        container_name = self.containers.first().name
        res = self.client.get(
            reverse('horizon:project:containers:index',
                    args=[utils.wrap_delimiter(container_name)]))
        self.assertTemplateUsed(res, 'project/containers/index.html')
        # UTF8 encoding here to ensure there aren't problems with Nose output.
        expected = [obj.name.encode('utf8') for obj in self.objects.list()]
        self.assertQuerysetEqual(res.context['objects_table'].data,
                                 expected,
                                 lambda obj: obj.name.encode('utf8'))
        # Check if the two forms' URL are properly 'urlquote()d'.
        form_action = ' action="%s%s/" ' % (CONTAINER_INDEX_URL,
                                            CONTAINER_NAME_1_QUOTED)
        self.assertContains(res, form_action, count=2)
        self._test_invalid_paths(res)

    @test.create_stubs({api.swift: ('swift_upload_object',)})
    def test_upload(self):
        container = self.containers.first()
        obj = self.objects.first()
        OBJECT_DATA = b'objectData'

        temp_file = tempfile.NamedTemporaryFile()
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
        self.assertContains(res, 'enctype="multipart/form-data"')
        self._test_invalid_paths(res)

        formData = {'method': forms.UploadObject.__name__,
                    'container_name': container.name,
                    'name': obj.name,
                    'object_file': temp_file}
        res = self.client.post(upload_url, formData)

        args = (utils.wrap_delimiter(container.name),)
        index_url = reverse('horizon:project:containers:index', args=args)
        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_upload_object',)})
    def test_upload_without_file(self):
        container = self.containers.first()
        obj = self.objects.first()

        api.swift.swift_upload_object(IsA(http.HttpRequest),
                                      container.name,
                                      obj.name,
                                      None).AndReturn(obj)
        self.mox.ReplayAll()

        upload_url = reverse('horizon:project:containers:object_upload',
                             args=[container.name])

        res = self.client.get(upload_url)
        self.assertTemplateUsed(res, 'project/containers/upload.html')

        res = self.client.get(upload_url)
        self.assertContains(res, 'enctype="multipart/form-data"')
        self.assertNotContains(res, INVALID_CONTAINER_NAME_1)
        self.assertNotContains(res, INVALID_CONTAINER_NAME_2)

        formData = {'method': forms.UploadObject.__name__,
                    'container_name': container.name,
                    'name': obj.name,
                    'object_file': None}
        res = self.client.post(upload_url, formData)

        args = (utils.wrap_delimiter(container.name),)
        index_url = reverse('horizon:project:containers:index', args=args)
        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_create_pseudo_folder',)})
    def test_create_pseudo_folder(self):
        container = self.containers.first()
        obj = self.objects.first()

        api.swift.swift_create_pseudo_folder(IsA(http.HttpRequest),
                                             container.name,
                                             obj.name + "/").AndReturn(obj)
        self.mox.ReplayAll()

        create_pseudo_folder_url = reverse('horizon:project:containers:'
                                           'create_pseudo_folder',
                                           args=[container.name])

        res = self.client.get(create_pseudo_folder_url)
        self.assertTemplateUsed(res,
                                'project/containers/create_pseudo_folder.html')
        self._test_invalid_paths(res)

        formData = {'method': forms.CreatePseudoFolder.__name__,
                    'container_name': container.name,
                    'name': obj.name}
        res = self.client.post(create_pseudo_folder_url, formData)

        index_url = reverse('horizon:project:containers:index',
                            args=[utils.wrap_delimiter(container.name)])

        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_delete_object',)})
    def test_delete(self):
        container = self.containers.first()
        obj = self.objects.first()
        args = (utils.wrap_delimiter(container.name),)
        index_url = reverse('horizon:project:containers:index', args=args)
        api.swift.swift_delete_object(IsA(http.HttpRequest),
                                      container.name,
                                      obj.name)
        self.mox.ReplayAll()

        action_string = "objects__delete_object__%s" % obj.name
        form_data = {"action": action_string}
        req = self.factory.post(index_url, form_data)
        kwargs = {"container_name": container.name}
        table = tables.ObjectsTable(req, self.objects.list(), **kwargs)
        handled = table.maybe_handle()
        self.assertEqual(handled['location'], index_url)

    @test.create_stubs({api.swift: ('swift_delete_object',)})
    def test_delete_pseudo_folder(self):
        container = self.containers.first()
        folder = self.folder.first()
        args = (utils.wrap_delimiter(container.name),)
        index_url = reverse('horizon:project:containers:index', args=args)
        api.swift.swift_delete_object(IsA(http.HttpRequest),
                                      container.name,
                                      folder.name + '/')
        self.mox.ReplayAll()

        action_string = "objects__delete_object__%s/%s" % (container.name,
                                                           folder.name)
        form_data = {"action": action_string}
        req = self.factory.post(index_url, form_data)
        kwargs = {"container_name": container.name}
        table = tables.ObjectsTable(req, self.folder.list(), **kwargs)
        handled = table.maybe_handle()
        self.assertEqual(handled['location'], index_url)

    @test.create_stubs({api.swift: ('swift_get_object',)})
    def test_download(self):
        for container in self.containers.list():
            for obj in self.objects.list():
                self.mox.ResetAll()  # mandatory in a for loop
                obj = copy.copy(obj)
                _data = obj.data

                def make_iter():
                    yield _data

                obj.data = make_iter()
                api.swift.swift_get_object(
                    IsA(http.HttpRequest),
                    container.name,
                    obj.name,
                    resp_chunk_size=api.swift.CHUNK_SIZE).AndReturn(obj)
                self.mox.ReplayAll()

                download_url = reverse(
                    'horizon:project:containers:object_download',
                    args=[container.name, obj.name])
                res = self.client.get(download_url)

                self.assertTrue(res.has_header('Content-Disposition'))
                if django.VERSION >= (1, 5):
                    self.assertEqual(b''.join(res.streaming_content), _data)
                    self.assertNotContains(res, INVALID_CONTAINER_NAME_1)
                    self.assertNotContains(res, INVALID_CONTAINER_NAME_2)
                else:
                    self.assertEqual(res.content, _data)
                    self.assertNotContains(res, INVALID_CONTAINER_NAME_1)
                    self.assertNotContains(res, INVALID_CONTAINER_NAME_2)

                # Check that the returned Content-Disposition filename is well
                # surrounded by double quotes and with commas removed
                expected_name = '"%s"' % obj.name.replace(',', '')
                if six.PY2:
                    expected_name = expected_name.encode('utf-8')
                self.assertEqual(
                    res.get('Content-Disposition'),
                    'attachment; filename=%s' % expected_name
                )

    @test.create_stubs({api.swift: ('swift_get_containers',)})
    def test_copy_index(self):
        ret = (self.containers.list(), False)
        api.swift.swift_get_containers(IsA(http.HttpRequest)).AndReturn(ret)
        self.mox.ReplayAll()

        res = self.client.get(reverse('horizon:project:containers:object_copy',
                                      args=[self.containers.first().name,
                                            self.objects.first().name]))
        self.assertTemplateUsed(res, 'project/containers/copy.html')
        self.assertNotContains(res, INVALID_CONTAINER_NAME_1)
        self.assertNotContains(res, INVALID_CONTAINER_NAME_2)

    @test.create_stubs({api.swift: ('swift_get_containers',
                                    'swift_copy_object')})
    def test_copy(self):
        container_1 = self.containers.get(name=CONTAINER_NAME_1)
        container_2 = self.containers.get(name=CONTAINER_NAME_2)
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
        args = (utils.wrap_delimiter(container_2.name),)
        index_url = reverse('horizon:project:containers:index', args=args)
        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_get_containers',
                                    'swift_copy_object')})
    def test_copy_get(self):
        original_name = u"test.txt"
        copy_name = u"test.copy.txt"
        container = self.containers.first()
        obj = self.objects.get(name=original_name)
        ret = (self.containers.list(), False)
        api.swift.swift_get_containers(IsA(http.HttpRequest)).AndReturn(ret)
        self.mox.ReplayAll()
        copy_url = reverse('horizon:project:containers:object_copy',
                           args=[container.name, obj.name])
        res = self.client.get(copy_url)
        # The copy's name must appear in initial data
        pattern = ('<input id="id_new_object_name" value="%s" '
                   'name="new_object_name" type="text" '
                   'class="form-control" maxlength="255" />' % copy_name)
        self.assertContains(res, pattern, html=True)

    def test_get_copy_name(self):
        self.assertEqual(views.CopyView.get_copy_name('test.txt'),
                         'test.copy.txt')
        self.assertEqual(views.CopyView.get_copy_name('test'),
                         'test.copy')

    @test.create_stubs({api.swift: ('swift_upload_object',)})
    def test_update_with_file(self):
        container = self.containers.first()
        obj = self.objects.first()
        OBJECT_DATA = b'objectData'

        temp_file = tempfile.NamedTemporaryFile()
        temp_file.write(OBJECT_DATA)
        temp_file.flush()
        temp_file.seek(0)

        api.swift.swift_upload_object(IsA(http.HttpRequest),
                                      container.name,
                                      obj.name,
                                      IsA(InMemoryUploadedFile)).AndReturn(obj)
        self.mox.ReplayAll()

        update_url = reverse('horizon:project:containers:object_update',
                             args=[container.name, obj.name])

        res = self.client.get(update_url)
        self.assertTemplateUsed(res, 'project/containers/update.html')
        self.assertContains(res, 'enctype="multipart/form-data"')
        self._test_invalid_paths(res)

        formData = {'method': forms.UpdateObject.__name__,
                    'container_name': container.name,
                    'name': obj.name,
                    'object_file': temp_file}
        res = self.client.post(update_url, formData)

        args = (utils.wrap_delimiter(container.name),)
        index_url = reverse('horizon:project:containers:index', args=args)
        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_upload_object',)})
    def test_update_without_file(self):
        container = self.containers.first()
        obj = self.objects.first()

        self.mox.ReplayAll()

        update_url = reverse('horizon:project:containers:object_update',
                             args=[container.name, obj.name])

        res = self.client.get(update_url)
        self.assertTemplateUsed(res, 'project/containers/update.html')
        self.assertContains(res, 'enctype="multipart/form-data"')
        self._test_invalid_paths(res)

        formData = {'method': forms.UpdateObject.__name__,
                    'container_name': container.name,
                    'name': obj.name}
        res = self.client.post(update_url, formData)

        args = (utils.wrap_delimiter(container.name),)
        index_url = reverse('horizon:project:containers:index', args=args)
        self.assertRedirectsNoFollow(res, index_url)

    @test.create_stubs({api.swift: ('swift_get_container', )})
    def test_view_container(self):
        for container in self.containers.list():
            self.mox.ResetAll()  # mandatory in a for loop
            api.swift.swift_get_container(IsA(http.HttpRequest),
                                          container.name,
                                          with_data=False) \
                .AndReturn(container)
            self.mox.ReplayAll()

            view_url = reverse('horizon:project:containers:container_detail',
                               args=[container.name])
            res = self.client.get(view_url)

            self.assertTemplateUsed(res,
                                    'project/containers/container_detail.html')
            self.assertContains(res, container.name, 1, 200)
            self.assertNotContains(res, INVALID_CONTAINER_NAME_1)
            self.assertNotContains(res, INVALID_CONTAINER_NAME_2)

    @test.create_stubs({api.swift: ('swift_get_object', )})
    def test_view_object(self):
        for container in self.containers.list():
            for obj in self.objects.list():
                self.mox.ResetAll()  # mandatory in a for loop
                api.swift.swift_get_object(IsA(http.HttpRequest),
                                           container.name,
                                           obj.name,
                                           with_data=False) \
                    .AndReturn(obj)
                self.mox.ReplayAll()
                view_url = reverse('horizon:project:containers:object_detail',
                                   args=[container.name, obj.name])
                res = self.client.get(view_url)

                self.assertTemplateUsed(
                    res, 'project/containers/object_detail.html')
                self.assertContains(res, obj.name, 1, 200)
                self._test_invalid_paths(res)

    def test_wrap_delimiter(self):
        expected = {
            'containerA': 'containerA/',
            'containerB%': 'containerB%/',  # no urlquote() should occur
            'containerC/': 'containerC/',   # already wrapped name
            'containerD/objectA': 'containerD/objectA/'
        }
        for name, expected_name in expected.items():
            self.assertEqual(utils.wrap_delimiter(name), expected_name)
