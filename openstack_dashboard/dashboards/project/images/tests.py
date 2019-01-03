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
from socket import timeout as socket_timeout
import tempfile
import unittest

from django.urls import reverse

import mock
import six

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.images import utils
from openstack_dashboard.test import helpers as test


INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'
INDEX_URL = reverse('horizon:project:images:index')
CREATE_URL = reverse('horizon:project:images:images:create')


class BaseImagesTestCase(test.TestCase):
    def setUp(self):
        super(BaseImagesTestCase, self).setUp()
        self.patcher = mock.patch.object(api.glance, 'image_list_detailed')
        self.mock_image_list = self.patcher.start()


class ImagesAndSnapshotsTests(BaseImagesTestCase):
    def test_index(self):
        images = self.images.list()
        self.mock_image_list.return_value = [images, False, False]

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertContains(res, 'help_text="Deleted images'
                                 ' are not recoverable."')
        self.assertIn('images_table', res.context)
        images_table = res.context['images_table']
        images = images_table.data

        self.assertEqual(len(images), 10)
        row_actions = images_table.get_row_actions(images[0])
        self.assertEqual(len(row_actions), 5)
        row_actions = images_table.get_row_actions(images[1])
        self.assertEqual(len(row_actions), 3)
        self.assertNotIn('delete_image',
                         [a.name for a in row_actions])
        row_actions = images_table.get_row_actions(images[2])
        self.assertEqual(len(row_actions), 4)

        self.mock_image_list.assert_called_once_with(test.IsHttpRequest(),
                                                     marker=None,
                                                     paginate=True,
                                                     sort_dir='asc',
                                                     sort_key='name',
                                                     reversed_order=False)

    def test_index_no_images(self):
        self.mock_image_list.return_value = [(), False, False]

        res = self.client.get(INDEX_URL)

        self.mock_image_list.assert_called_once_with(test.IsHttpRequest(),
                                                     marker=None,
                                                     paginate=True,
                                                     sort_dir='asc',
                                                     sort_key='name',
                                                     reversed_order=False)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertContains(res, 'No items to display')

    def test_index_error(self):
        self.mock_image_list.side_effect = self.exceptions.glance

        res = self.client.get(INDEX_URL)

        self.mock_image_list.assert_called_once_with(test.IsHttpRequest(),
                                                     marker=None,
                                                     paginate=True,
                                                     sort_dir='asc',
                                                     sort_key='name',
                                                     reversed_order=False)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)

    def test_snapshot_actions(self):
        snapshots = self.snapshots.list()
        self.mock_image_list.return_value = [snapshots, False, False]

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertIn('images_table', res.context)
        snaps = res.context['images_table']
        self.assertEqual(len(snaps.get_rows()), 4)

        row_actions = snaps.get_row_actions(snaps.data[0])

        # first instance - status active, owned
        self.assertEqual(len(row_actions), 5)
        self.assertEqual(row_actions[0].verbose_name, u"Launch")
        self.assertEqual(row_actions[1].verbose_name, u"Create Volume")
        self.assertEqual(row_actions[2].verbose_name, u"Edit Image")
        self.assertEqual(row_actions[3].verbose_name, u"Update Metadata")
        self.assertEqual(row_actions[4].verbose_name, u"Delete Image")

        row_actions = snaps.get_row_actions(snaps.data[1])

        # second instance - status active, not owned
        self.assertEqual(len(row_actions), 2)
        self.assertEqual(row_actions[0].verbose_name, u"Launch")
        self.assertEqual(row_actions[1].verbose_name, u"Create Volume")

        row_actions = snaps.get_row_actions(snaps.data[2])
        # third instance - status queued, only delete is available
        self.assertEqual(len(row_actions), 1)
        self.assertEqual(six.text_type(row_actions[0].verbose_name),
                         u"Delete Image")
        self.assertEqual(str(row_actions[0]), "<DeleteImage: delete>")

        self.mock_image_list.assert_called_once_with(test.IsHttpRequest(),
                                                     marker=None,
                                                     paginate=True,
                                                     sort_dir='asc',
                                                     sort_key='name',
                                                     reversed_order=False)


class ImagesAndSnapshotsUtilsTests(BaseImagesTestCase):
    def test_list_image(self):
        public_images = [image for image in self.images.list()
                         if image.status == 'active' and image.is_public]
        private_images = [image for image in self.images.list()
                          if (image.status == 'active' and
                              not image.is_public)]
        shared_images = [image for image in self.imagesV2.list()
                         if (image.status == 'active' and
                             image.visibility == 'shared')]
        community_images = [image for image in self.imagesV2.list()
                            if (image.status == 'active' and
                                image.visibility == 'community')]
        self.mock_image_list.side_effect = [
            [public_images, False, False],
            [private_images, False, False],
            [community_images, False, False],
            [shared_images, False, False]
        ]

        image_calls = [
            mock.call(test.IsHttpRequest(),
                      filters={'is_public': True, 'status': 'active'}),
            mock.call(test.IsHttpRequest(),
                      filters={'property-owner_id': self.tenant.id,
                               'status': 'active'}),
            mock.call(test.IsHttpRequest(),
                      filters={'visibility': 'community', 'status': 'active'}),
            mock.call(test.IsHttpRequest(),
                      filters={'visibility': 'shared', 'status': 'active'})
        ]

        ret = utils.get_available_images(self.request, self.tenant.id)

        expected_images = [image for image in self.images.list()
                           if (image.status == 'active' and
                               image.container_format not in ('ami', 'aki'))]

        self.mock_image_list.assert_has_calls(image_calls)
        self.assertEqual(len(expected_images), len(ret))

    def test_list_image_using_cache(self):
        public_images = [image for image in self.images.list()
                         if image.status == 'active' and image.is_public]
        private_images = [image for image in self.images.list()
                          if (image.status == 'active' and
                              not image.is_public)]
        community_images = [image for image in self.imagesV2.list()
                            if (image.status == 'active' and
                                image.visibility == 'community')]
        shared_images = [image for image in self.imagesV2.list()
                         if (image.status == 'active' and
                             image.visibility == 'shared')]

        self.mock_image_list.side_effect = [
            [public_images, False, False],
            [private_images, False, False],
            [community_images, False, False],
            [shared_images, False, False],
            [private_images, False, False]
        ]

        image_calls = [
            mock.call(test.IsHttpRequest(),
                      filters={'is_public': True, 'status': 'active'}),
            mock.call(test.IsHttpRequest(),
                      filters={'property-owner_id': self.tenant.id,
                               'status': 'active'}),
            mock.call(test.IsHttpRequest(),
                      filters={'visibility': 'community', 'status': 'active'}),
            mock.call(test.IsHttpRequest(),
                      filters={'visibility': 'shared', 'status': 'active'}),
            mock.call(test.IsHttpRequest(),
                      filters={'property-owner_id': 'other-tenant',
                               'status': 'active'})
        ]

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
        self.assertEqual(
            len(community_images),
            len(images_cache['community_images']))
        self.assertEqual(
            len(shared_images),
            len(images_cache['shared_images']))

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

        self.mock_image_list.assert_has_calls(image_calls)

    @mock.patch.object(exceptions, 'handle')
    def test_list_image_error_public_image_list(self, mock_exception_handle):
        private_images = [image for image in self.images.list()
                          if (image.status == 'active' and
                              not image.is_public)]
        community_images = [image for image in self.imagesV2.list()
                            if (image.status == 'active' and
                                image.visibility == 'community')]
        shared_images = [image for image in self.imagesV2.list()
                         if (image.status == 'active' and
                             image.visibility == 'shared')]

        self.mock_image_list.side_effect = [
            self.exceptions.glance,
            [private_images, False, False],
            [community_images, False, False],
            [shared_images, False, False]
        ]

        images_cache = {}
        ret = utils.get_available_images(self.request, self.tenant.id,
                                         images_cache)
        image_calls = [
            mock.call(test.IsHttpRequest(),
                      filters={'is_public': True, 'status': 'active'}),
            mock.call(test.IsHttpRequest(),
                      filters={'status': 'active', 'property-owner_id': '1'}),
            mock.call(test.IsHttpRequest(),
                      filters={'visibility': 'community', 'status': 'active'}),
            mock.call(test.IsHttpRequest(),
                      filters={'visibility': 'shared', 'status': 'active'})
        ]
        self.mock_image_list.assert_has_calls(image_calls)
        mock_exception_handle.assert_called_once_with(
            test.IsHttpRequest(),
            "Unable to retrieve public images.")

        expected_images = [image for image in private_images
                           if image.container_format not in ('ami', 'aki')]
        self.assertEqual(len(expected_images), len(ret))
        self.assertNotIn('public_images', images_cache)
        self.assertEqual(1, len(images_cache['images_by_project']))
        self.assertEqual(
            len(private_images),
            len(images_cache['images_by_project'][self.tenant.id]))
        self.assertEqual(
            len(community_images),
            len(images_cache['community_images']))
        self.assertEqual(
            len(shared_images),
            len(images_cache['shared_images']))

    @mock.patch.object(exceptions, 'handle')
    def test_list_image_error_private_image_list(self, mock_exception_handle):
        public_images = [image for image in self.images.list()
                         if image.status == 'active' and image.is_public]
        private_images = [image for image in self.images.list()
                          if (image.status == 'active' and
                              not image.is_public)]
        community_images = [image for image in self.imagesV2.list()
                            if (image.status == 'active' and
                                image.visibility == 'community')]
        shared_images = [image for image in self.imagesV2.list()
                         if (image.status == 'active' and
                             image.visibility == 'shared')]

        self.mock_image_list.side_effect = [
            [public_images, False, False],
            self.exceptions.glance,
            [community_images, False, False],
            [shared_images, False, False],
            [private_images, False, False]
        ]
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
        self.assertEqual(
            len(community_images),
            len(images_cache['community_images']))
        self.assertEqual(
            len(shared_images),
            len(images_cache['shared_images']))

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
        self.assertEqual(
            len(community_images),
            len(images_cache['community_images']))
        self.assertEqual(
            len(shared_images),
            len(images_cache['shared_images']))

        image_calls = [
            mock.call(test.IsHttpRequest(),
                      filters={'status': 'active', 'is_public': True}),
            mock.call(test.IsHttpRequest(),
                      filters={'status': 'active', 'property-owner_id': '1'}),
            mock.call(test.IsHttpRequest(),
                      filters={'status': 'active', 'visibility': 'community'}),
            mock.call(test.IsHttpRequest(),
                      filters={'status': 'active', 'visibility': 'shared'}),
            mock.call(test.IsHttpRequest(),
                      filters={'status': 'active', 'property-owner_id': '1'})
        ]
        self.mock_image_list.assert_has_calls(image_calls)
        mock_exception_handle.assert_called_once_with(
            test.IsHttpRequest(),
            "Unable to retrieve images for the current project.")


class SeleniumTests(test.SeleniumTestCase):
    @test.create_mocks({api.glance: ('image_list_detailed',)})
    def test_modal_create_image_from_url(self):
        driver = self.selenium
        images = self.images.list()
        self.mock_image_list_detailed.return_value = [images, False, False]

        driver.get("%s%s" % (self.live_server_url, INDEX_URL))

        # Open the modal menu
        driver.find_element_by_id("images__action_create").click()
        wait = self.ui.WebDriverWait(self.selenium, 10,
                                     ignored_exceptions=[socket_timeout])
        wait.until(lambda x: driver.find_element_by_id("id_disk_format"))

        driver.find_element_by_xpath('//a[@data-select-value="url"]').click()
        copyfrom = driver.find_element_by_id("id_image_url")
        copyfrom.send_keys("http://www.test.com/test.iso")
        formats = self.ui.Select(driver.find_element_by_id("id_disk_format"))
        body = formats.first_selected_option
        self.assertIn("ISO", body.text,
                      "ISO should be selected when the extension is *.iso")

        self.assertEqual(3, self.mock_image_list_detailed.call_count)
        self.mock_image_list_detailed.assert_has_calls([
            mock.call(test.IsHttpRequest(), marker=None, paginate=True,
                      reversed_order=False, sort_dir='asc', sort_key='name'),
            mock.call(test.IsHttpRequest(), filters={'disk_format': 'aki'}),
            mock.call(test.IsHttpRequest(), filters={'disk_format': 'ari'}),
        ])

    @unittest.skipIf(os.environ.get('SELENIUM_PHANTOMJS'),
                     "PhantomJS cannot test file upload widgets.")
    @test.create_mocks({api.glance: ('image_list_detailed',)})
    def test_modal_create_image_from_file(self):
        driver = self.selenium
        images = self.images.list()
        self.mock_image_list_detailed.return_value = [images, False, False]

        driver.get("%s%s" % (self.live_server_url, INDEX_URL))

        # Open the modal menu
        driver.find_element_by_id("images__action_create").click()
        wait = self.ui.WebDriverWait(driver, 10,
                                     ignored_exceptions=[socket_timeout])
        wait.until(lambda x: driver.find_element_by_id("id_disk_format"))

        driver.find_element_by_xpath('//a[@data-select-value="file"]').click()
        with tempfile.NamedTemporaryFile() as tmp:
            driver.find_element_by_id("id_image_file").send_keys(tmp.name)
        formats = self.ui.Select(driver.find_element_by_id("id_disk_format"))
        formats.select_by_visible_text('ISO - Optical Disk Image')
        body = formats.first_selected_option
        self.assertIn("ISO", body.text,
                      "ISO should be selected when the extension is *.iso")

        self.assertEqual(3, self.mock_image_list_detailed.call_count)
        self.mock_image_list_detailed.assert_has_calls([
            mock.call(test.IsHttpRequest(), marker=None, paginate=True,
                      reversed_order=False, sort_dir='asc', sort_key='name'),
            mock.call(test.IsHttpRequest(), filters={'disk_format': 'aki'}),
            mock.call(test.IsHttpRequest(), filters={'disk_format': 'ari'}),
        ])

    @test.create_mocks({api.glance: ('image_list_detailed',)})
    def test_create_image_from_url(self):
        driver = self.selenium
        self.mock_image_list_detailed.return_value = [self.images.list(),
                                                      False, False]

        driver.get("%s%s" % (self.live_server_url, CREATE_URL))
        wait = self.ui.WebDriverWait(driver, 10,
                                     ignored_exceptions=[socket_timeout])
        wait.until(lambda x: driver.find_element_by_id("id_disk_format"))

        driver.find_element_by_xpath('//a[@data-select-value="url"]').click()
        copyfrom = driver.find_element_by_id("id_image_url")
        copyfrom.send_keys("http://www.test.com/test.iso")
        formats = self.ui.Select(driver.find_element_by_id("id_disk_format"))
        formats.select_by_visible_text('ISO - Optical Disk Image')
        body = formats.first_selected_option
        self.assertIn("ISO", body.text,
                      "ISO should be selected when the extension is *.iso")

        self.assertEqual(2, self.mock_image_list_detailed.call_count)
        self.mock_image_list_detailed.assert_has_calls([
            mock.call(test.IsHttpRequest(), filters={'disk_format': 'aki'}),
            mock.call(test.IsHttpRequest(), filters={'disk_format': 'ari'}),
        ])

    @unittest.skipIf(os.environ.get('SELENIUM_PHANTOMJS'),
                     "PhantomJS cannot test file upload widgets.")
    @test.create_mocks({api.glance: ('image_list_detailed',)})
    def test_create_image_from_file(self):
        driver = self.selenium
        self.mock_image_list_detailed.return_value = [self.images.list(),
                                                      False, False]

        driver.get("%s%s" % (self.live_server_url, CREATE_URL))
        wait = self.ui.WebDriverWait(driver, 10,
                                     ignored_exceptions=[socket_timeout])
        wait.until(lambda x: driver.find_element_by_id("id_disk_format"))

        driver.find_element_by_xpath('//a[@data-select-value="file"]').click()
        with tempfile.NamedTemporaryFile() as tmp:
            driver.find_element_by_id("id_image_file").send_keys(tmp.name)
        formats = self.ui.Select(driver.find_element_by_id("id_disk_format"))
        formats.select_by_visible_text('ISO - Optical Disk Image')
        body = formats.first_selected_option

        self.assertIn("ISO", body.text,
                      "ISO should be selected when the extension is *.iso")

        self.assertEqual(2, self.mock_image_list_detailed.call_count)
        self.mock_image_list_detailed.assert_has_calls([
            mock.call(test.IsHttpRequest(), filters={'disk_format': 'aki'}),
            mock.call(test.IsHttpRequest(), filters={'disk_format': 'ari'}),
        ])
