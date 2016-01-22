# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright 2012 OpenStack Foundation
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

import os
from socket import timeout as socket_timeout  # noqa
import unittest

from django.core.urlresolvers import reverse
from django import http

from glanceclient.common import exceptions as glance_exec

from mox3.mox import IsA  # noqa
import six

from horizon import exceptions
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.images import utils
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:images:index')
CREATE_URL = reverse('horizon:project:images:images:create')


class ImagesAndSnapshotsTests(test.TestCase):
    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_index(self):
        images = self.images.list()
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True) \
            .AndReturn([images, False, False])
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/images/index.html')
        self.assertContains(res, 'help_text="Deleted images'
                                 ' are not recoverable."')
        self.assertIn('images_table', res.context)
        images_table = res.context['images_table']
        images = images_table.data

        self.assertEqual(len(images), 9)
        row_actions = images_table.get_row_actions(images[0])
        self.assertEqual(len(row_actions), 5)
        row_actions = images_table.get_row_actions(images[1])
        self.assertEqual(len(row_actions), 3)
        self.assertTrue('delete_image' not in
                        [a.name for a in row_actions])
        row_actions = images_table.get_row_actions(images[2])
        self.assertEqual(len(row_actions), 4)

    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_index_no_images(self):
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True) \
            .AndReturn([(), False, False])
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/images/index.html')
        self.assertContains(res, 'No items to display')

    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_index_error(self):
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True) \
            .AndRaise(self.exceptions.glance)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/images/index.html')

    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_snapshot_actions(self):
        snapshots = self.snapshots.list()
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True) \
            .AndReturn([snapshots, False, False])
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/images/index.html')
        self.assertIn('images_table', res.context)
        snaps = res.context['images_table']
        self.assertEqual(len(snaps.get_rows()), 3)

        row_actions = snaps.get_row_actions(snaps.data[0])

        # first instance - status active, owned
        self.assertEqual(len(row_actions), 5)
        self.assertEqual(row_actions[0].verbose_name, u"Launch Instance")
        self.assertEqual(row_actions[1].verbose_name, u"Create Volume")
        self.assertEqual(row_actions[2].verbose_name, u"Edit Image")
        self.assertEqual(row_actions[3].verbose_name, u"Update Metadata")
        self.assertEqual(row_actions[4].verbose_name, u"Delete Image")

        row_actions = snaps.get_row_actions(snaps.data[1])

        # second instance - status active, not owned
        self.assertEqual(len(row_actions), 2)
        self.assertEqual(row_actions[0].verbose_name, u"Launch Instance")
        self.assertEqual(row_actions[1].verbose_name, u"Create Volume")

        row_actions = snaps.get_row_actions(snaps.data[2])
        # third instance - status queued, only delete is available
        self.assertEqual(len(row_actions), 1)
        self.assertEqual(six.text_type(row_actions[0].verbose_name),
                         u"Delete Image")
        self.assertEqual(str(row_actions[0]), "<DeleteImage: delete>")


class ImagesAndSnapshotsUtilsTests(test.TestCase):

    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_list_image(self):
        public_images = [image for image in self.images.list()
                         if image.status == 'active' and image.is_public]
        private_images = [image for image in self.images.list()
                          if (image.status == 'active' and
                              not image.is_public)]
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([public_images, False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([private_images, False, False])

        self.mox.ReplayAll()

        ret = utils.get_available_images(self.request, self.tenant.id)

        expected_images = [image for image in self.images.list()
                           if (image.status == 'active' and
                               image.container_format not in ('ami', 'aki'))]
        self.assertEqual(len(expected_images), len(ret))

    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_list_image_using_cache(self):
        public_images = [image for image in self.images.list()
                         if image.status == 'active' and image.is_public]
        private_images = [image for image in self.images.list()
                          if (image.status == 'active' and
                              not image.is_public)]
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([public_images, False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([private_images, False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': 'other-tenant',
                     'status': 'active'}) \
            .AndReturn([private_images, False, False])

        self.mox.ReplayAll()

        expected_images = [image for image in self.images.list()
                           if (image.status == 'active' and
                               image.container_format not in ('ari', 'aki'))]

        images_cache = {}
        ret = utils.get_available_images(self.request, self.tenant.id,
                                         images_cache)
        self.assertEqual(len(expected_images), len(ret))
        self.assertEqual(
            len(public_images),
            len(images_cache['public_images']))
        self.assertEqual(1, len(images_cache['images_by_project']))
        self.assertEqual(
            len(private_images),
            len(images_cache['images_by_project'][self.tenant.id]))

        ret = utils.get_available_images(self.request, self.tenant.id,
                                         images_cache)
        self.assertEqual(len(expected_images), len(ret))

        # image list for other-tenant
        ret = utils.get_available_images(self.request, 'other-tenant',
                                         images_cache)
        self.assertEqual(len(expected_images), len(ret))
        self.assertEqual(
            len(public_images),
            len(images_cache['public_images']))
        self.assertEqual(2, len(images_cache['images_by_project']))
        self.assertEqual(
            len(private_images),
            len(images_cache['images_by_project']['other-tenant']))

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        exceptions: ('handle',)})
    def test_list_image_error_public_image_list(self):
        public_images = [image for image in self.images.list()
                         if image.status == 'active' and image.is_public]
        private_images = [image for image in self.images.list()
                          if (image.status == 'active' and
                              not image.is_public)]
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndRaise(self.exceptions.glance)
        exceptions.handle(IsA(http.HttpRequest),
                          "Unable to retrieve public images.")
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([private_images, False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([public_images, False, False])

        self.mox.ReplayAll()

        images_cache = {}
        ret = utils.get_available_images(self.request, self.tenant.id,
                                         images_cache)

        expected_images = [image for image in private_images
                           if image.container_format not in ('ami', 'aki')]
        self.assertEqual(len(expected_images), len(ret))
        self.assertNotIn('public_images', images_cache)
        self.assertEqual(1, len(images_cache['images_by_project']))
        self.assertEqual(
            len(private_images),
            len(images_cache['images_by_project'][self.tenant.id]))

        ret = utils.get_available_images(self.request, self.tenant.id,
                                         images_cache)

        expected_images = [image for image in self.images.list()
                           if image.container_format not in ('ami', 'aki')]
        self.assertEqual(len(expected_images), len(ret))
        self.assertEqual(
            len(public_images),
            len(images_cache['public_images']))
        self.assertEqual(1, len(images_cache['images_by_project']))
        self.assertEqual(
            len(private_images),
            len(images_cache['images_by_project'][self.tenant.id]))

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        messages: ('error',)})
    def test_list_image_communication_error_public_image_list(self):
        public_images = [image for image in self.images.list()
                         if image.status == 'active' and image.is_public]
        private_images = [image for image in self.images.list()
                          if (image.status == 'active' and
                              not image.is_public)]
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndRaise(glance_exec.CommunicationError)
        # Make sure the exception is handled with the correct
        # error message. If the exception cannot be handled,
        # the error message will be different.
        messages.error(IsA(http.HttpRequest),
                       "Unable to retrieve public images.")
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([private_images, False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([public_images, False, False])

        self.mox.ReplayAll()

        images_cache = {}
        ret = utils.get_available_images(self.request, self.tenant.id,
                                         images_cache)

        expected_images = [image for image in private_images
                           if image.container_format not in ('ami', 'aki')]
        self.assertEqual(len(expected_images), len(ret))
        self.assertNotIn('public_images', images_cache)
        self.assertEqual(1, len(images_cache['images_by_project']))
        self.assertEqual(
            len(private_images),
            len(images_cache['images_by_project'][self.tenant.id]))

        ret = utils.get_available_images(self.request, self.tenant.id,
                                         images_cache)

        expected_images = [image for image in self.images.list()
                           if image.container_format not in ('ami', 'aki')]
        self.assertEqual(len(expected_images), len(ret))
        self.assertEqual(
            len(public_images),
            len(images_cache['public_images']))
        self.assertEqual(1, len(images_cache['images_by_project']))
        self.assertEqual(
            len(private_images),
            len(images_cache['images_by_project'][self.tenant.id]))

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        exceptions: ('handle',)})
    def test_list_image_error_private_image_list(self):
        public_images = [image for image in self.images.list()
                         if image.status == 'active' and image.is_public]
        private_images = [image for image in self.images.list()
                          if (image.status == 'active' and
                              not image.is_public)]
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'is_public': True, 'status': 'active'}) \
            .AndReturn([public_images, False, False])
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndRaise(self.exceptions.glance)
        exceptions.handle(IsA(http.HttpRequest),
                          "Unable to retrieve images for the current project.")
        api.glance.image_list_detailed(
            IsA(http.HttpRequest),
            filters={'property-owner_id': self.tenant.id,
                     'status': 'active'}) \
            .AndReturn([private_images, False, False])

        self.mox.ReplayAll()

        images_cache = {}
        ret = utils.get_available_images(self.request, self.tenant.id,
                                         images_cache)

        expected_images = [image for image in public_images
                           if image.container_format not in ('ami', 'aki')]
        self.assertEqual(len(expected_images), len(ret))
        self.assertEqual(
            len(public_images),
            len(images_cache['public_images']))
        self.assertFalse(len(images_cache['images_by_project']))

        ret = utils.get_available_images(self.request, self.tenant.id,
                                         images_cache)

        expected_images = [image for image in self.images.list()
                           if image.container_format not in ('ami', 'aki')]
        self.assertEqual(len(expected_images), len(ret))
        self.assertEqual(
            len(public_images),
            len(images_cache['public_images']))
        self.assertEqual(1, len(images_cache['images_by_project']))
        self.assertEqual(
            len(private_images),
            len(images_cache['images_by_project'][self.tenant.id]))


class SeleniumTests(test.SeleniumTestCase):
    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_modal_create_image_from_url(self):
        driver = self.selenium
        images = self.images.list()
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None).AndReturn([images,
                                                               False, False])
        filters = {'disk_format': 'aki'}
        api.glance.image_list_detailed(
            IsA(http.HttpRequest), filters=filters).AndReturn(
            [self.images.list(), False, False])
        filters = {'disk_format': 'ari'}
        api.glance.image_list_detailed(
            IsA(http.HttpRequest), filters=filters).AndReturn(
            [self.images.list(), False, False])
        self.mox.ReplayAll()

        driver.get("%s%s" % (self.live_server_url, INDEX_URL))

        # Open the modal menu
        driver.find_element_by_id("images__action_create").send_keys("\n")
        wait = self.ui.WebDriverWait(self.selenium, 10,
                                     ignored_exceptions=[socket_timeout])
        wait.until(lambda x: driver.find_element_by_id("id_disk_format"))

        srctypes = self.ui.Select(driver.find_element_by_id("id_source_type"))
        srctypes.select_by_value("url")
        copyfrom = driver.find_element_by_id("id_image_url")
        copyfrom.send_keys("http://www.test.com/test.iso")
        formats = self.ui.Select(driver.find_element_by_id("id_disk_format"))
        body = formats.first_selected_option
        self.assertTrue("ISO" in body.text,
                        "ISO should be selected when the extension is *.iso")

    @unittest.skipIf(os.environ.get('SELENIUM_PHANTOMJS'),
                     "PhantomJS cannot test file upload widgets.")
    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_modal_create_image_from_file(self):
        driver = self.selenium
        images = self.images.list()
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None).AndReturn([images,
                                                               False, False])
        filters = {'disk_format': 'aki'}
        api.glance.image_list_detailed(
            IsA(http.HttpRequest), filters=filters).AndReturn(
            [self.images.list(), False, False])
        filters = {'disk_format': 'ari'}
        api.glance.image_list_detailed(
            IsA(http.HttpRequest), filters=filters).AndReturn(
            [self.images.list(), False, False])
        self.mox.ReplayAll()

        driver.get("%s%s" % (self.live_server_url, INDEX_URL))

        # Open the modal menu
        driver.find_element_by_id("images__action_create").send_keys("\n")
        wait = self.ui.WebDriverWait(driver, 10,
                                     ignored_exceptions=[socket_timeout])
        wait.until(lambda x: driver.find_element_by_id("id_disk_format"))

        srctypes = self.ui.Select(driver.find_element_by_id("id_source_type"))
        srctypes.select_by_value("file")
        driver.find_element_by_id("id_image_file").send_keys("/tmp/test.iso")
        formats = self.ui.Select(driver.find_element_by_id("id_disk_format"))
        body = formats.first_selected_option
        self.assertTrue("ISO" in body.text,
                        "ISO should be selected when the extension is *.iso")

    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_create_image_from_url(self):
        driver = self.selenium
        filters = {'disk_format': 'aki'}
        api.glance.image_list_detailed(
            IsA(http.HttpRequest), filters=filters).AndReturn(
            [self.images.list(), False, False])
        filters = {'disk_format': 'ari'}
        api.glance.image_list_detailed(
            IsA(http.HttpRequest), filters=filters).AndReturn(
            [self.images.list(), False, False])
        self.mox.ReplayAll()

        driver.get("%s%s" % (self.live_server_url, CREATE_URL))
        wait = self.ui.WebDriverWait(driver, 10,
                                     ignored_exceptions=[socket_timeout])
        wait.until(lambda x: driver.find_element_by_id("id_disk_format"))

        srctypes = self.ui.Select(driver.find_element_by_id("id_source_type"))
        srctypes.select_by_value("url")
        copyfrom = driver.find_element_by_id("id_image_url")
        copyfrom.send_keys("http://www.test.com/test.iso")
        formats = self.ui.Select(driver.find_element_by_id("id_disk_format"))
        body = formats.first_selected_option
        self.assertTrue("ISO" in body.text,
                        "ISO should be selected when the extension is *.iso")

    @unittest.skipIf(os.environ.get('SELENIUM_PHANTOMJS'),
                     "PhantomJS cannot test file upload widgets.")
    @test.create_stubs({api.glance: ('image_list_detailed',)})
    def test_create_image_from_file(self):
        driver = self.selenium
        filters = {'disk_format': 'aki'}
        api.glance.image_list_detailed(
            IsA(http.HttpRequest), filters=filters).AndReturn(
            [self.images.list(), False, False])
        filters = {'disk_format': 'ari'}
        api.glance.image_list_detailed(
            IsA(http.HttpRequest), filters=filters).AndReturn(
            [self.images.list(), False, False])
        self.mox.ReplayAll()

        driver.get("%s%s" % (self.live_server_url, CREATE_URL))
        wait = self.ui.WebDriverWait(driver, 10,
                                     ignored_exceptions=[socket_timeout])
        wait.until(lambda x: driver.find_element_by_id("id_disk_format"))

        srctypes = self.ui.Select(driver.find_element_by_id("id_source_type"))
        srctypes.select_by_value("file")
        driver.find_element_by_id("id_image_file").send_keys("/tmp/test.iso")
        formats = self.ui.Select(driver.find_element_by_id("id_disk_format"))
        body = formats.first_selected_option
        self.assertTrue("ISO" in body.text,
                        "ISO should be selected when the extension is *.iso")
