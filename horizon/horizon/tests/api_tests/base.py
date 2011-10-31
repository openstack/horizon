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

from __future__ import absolute_import

from django import http
from django.conf import settings
from mox import IsA

from horizon import exceptions
from horizon.tests.api_tests.utils import *


# Wrapper classes that only define _attrs don't need extra testing.
class APIResourceWrapperTests(test.TestCase):
    def test_get_attribute(self):
        resource = APIResource.get_instance()
        self.assertEqual(resource.foo, 'foo')

    def test_get_invalid_attribute(self):
        resource = APIResource.get_instance()
        self.assertNotIn('missing', resource._attrs,
                msg="Test assumption broken.  Find new missing attribute")
        with self.assertRaises(AttributeError):
            resource.missing

    def test_get_inner_missing_attribute(self):
        resource = APIResource.get_instance()
        with self.assertRaises(AttributeError):
            resource.baz


class APIDictWrapperTests(test.TestCase):
    # APIDict allows for both attribute access and dictionary style [element]
    # style access.  Test both
    def test_get_item(self):
        resource = APIDict.get_instance()
        self.assertEqual(resource.foo, 'foo')
        self.assertEqual(resource['foo'], 'foo')

    def test_get_invalid_item(self):
        resource = APIDict.get_instance()
        self.assertNotIn('missing', resource._attrs,
                msg="Test assumption broken.  Find new missing attribute")
        with self.assertRaises(AttributeError):
            resource.missing
        with self.assertRaises(KeyError):
            resource['missing']

    def test_get_inner_missing_attribute(self):
        resource = APIDict.get_instance()
        with self.assertRaises(AttributeError):
            resource.baz
        with self.assertRaises(KeyError):
            resource['baz']

    def test_get_with_default(self):
        resource = APIDict.get_instance()

        self.assertEqual(resource.get('foo'), 'foo')

        self.assertIsNone(resource.get('baz'))

        self.assertEqual('retValue', resource.get('baz', 'retValue'))


class ApiHelperTests(test.TestCase):
    """ Tests for functions that don't use one of the api objects """

    def test_url_for(self):
        GLANCE_URL = 'http://glance/glanceapi/'
        NOVA_URL = 'http://nova/novapi/'

        url = api.url_for(self.request, 'image')
        self.assertEqual(url, GLANCE_URL + 'internal')

        url = api.url_for(self.request, 'image', admin=False)
        self.assertEqual(url, GLANCE_URL + 'internal')

        url = api.url_for(self.request, 'image', admin=True)
        self.assertEqual(url, GLANCE_URL + 'admin')

        url = api.url_for(self.request, 'compute')
        self.assertEqual(url, NOVA_URL + 'internal')

        url = api.url_for(self.request, 'compute', admin=False)
        self.assertEqual(url, NOVA_URL + 'internal')

        url = api.url_for(self.request, 'compute', admin=True)
        self.assertEqual(url, NOVA_URL + 'admin')

        self.assertNotIn('notAnApi', self.request.user.service_catalog,
                         'Select a new nonexistent service catalog key')
        with self.assertRaises(exceptions.ServiceCatalogException):
            url = api.url_for(self.request, 'notAnApi')
