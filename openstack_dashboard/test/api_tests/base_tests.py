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

from __future__ import absolute_import

from horizon import exceptions

from openstack_dashboard.api import base as api_base
from openstack_dashboard.test import helpers as test


class APIResource(api_base.APIResourceWrapper):
    """ Simple APIResource for testing """
    _attrs = ['foo', 'bar', 'baz']

    @staticmethod
    def get_instance(innerObject=None):
        if innerObject is None:

            class InnerAPIResource(object):
                pass

            innerObject = InnerAPIResource()
            innerObject.foo = 'foo'
            innerObject.bar = 'bar'
        return APIResource(innerObject)


class APIDict(api_base.APIDictWrapper):
    """ Simple APIDict for testing """
    _attrs = ['foo', 'bar', 'baz']

    @staticmethod
    def get_instance(innerDict=None):
        if innerDict is None:
            innerDict = {'foo': 'foo',
                         'bar': 'bar'}
        return APIDict(innerDict)


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

    def test_repr(self):
        resource = APIResource.get_instance()
        resource_str = resource.__repr__()
        self.assertIn('foo', resource_str)
        self.assertIn('bar', resource_str)
        self.assertNotIn('baz', resource_str)


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
        url = api_base.url_for(self.request, 'image')
        self.assertEqual(url, 'http://public.glance.example.com:9292/v1')

        url = api_base.url_for(self.request, 'image', endpoint_type='adminURL')
        self.assertEqual(url, 'http://admin.glance.example.com:9292/v1')

        url = api_base.url_for(self.request, 'compute')
        self.assertEqual(url, 'http://public.nova.example.com:8774/v2')

        url = api_base.url_for(self.request, 'compute',
                               endpoint_type='adminURL')
        self.assertEqual(url, 'http://admin.nova.example.com:8774/v2')

        url = api_base.url_for(self.request, 'volume')
        self.assertEqual(url, 'http://public.nova.example.com:8776/v1')

        url = api_base.url_for(self.request, 'volume',
                               endpoint_type="internalURL")
        self.assertEqual(url, 'http://int.nova.example.com:8776/v1')

        url = api_base.url_for(self.request, 'volume',
                               endpoint_type='adminURL')
        self.assertEqual(url, 'http://admin.nova.example.com:8776/v1')

        self.assertNotIn('notAnApi', self.request.user.service_catalog,
                         'Select a new nonexistent service catalog key')
        with self.assertRaises(exceptions.ServiceCatalogException):
            url = api_base.url_for(self.request, 'notAnApi')

        self.request.user.services_region = "RegionTwo"
        url = api_base.url_for(self.request, 'compute')
        self.assertEqual(url, 'http://public.nova2.example.com:8774/v2')

        self.request.user.services_region = "RegionTwo"
        url = api_base.url_for(self.request, 'compute',
                               endpoint_type='adminURL')
        self.assertEqual(url, 'http://admin.nova2.example.com:8774/v2')

        self.request.user.services_region = "RegionTwo"
        with self.assertRaises(exceptions.ServiceCatalogException):
            url = api_base.url_for(self.request, 'image')

        self.request.user.services_region = "bogus_value"
        url = api_base.url_for(self.request, 'identity',
                               endpoint_type='adminURL')
        self.assertEqual(url, 'http://admin.keystone.example.com:35357/v2.0')

        self.request.user.services_region = "bogus_value"
        with self.assertRaises(exceptions.ServiceCatalogException):
            url = api_base.url_for(self.request, 'image')


class QuotaSetTests(test.TestCase):

    def test_quotaset_add_with_plus(self):
        quota_dict = {'foo': 1, 'bar': 10}
        other_quota_dict = {'my_test': 12}
        quota_set = api_base.QuotaSet(quota_dict)
        other_quota_set = api_base.QuotaSet(other_quota_dict)

        quota_set += other_quota_set
        self.assertEqual(len(quota_set), 3)

        quota_dict.update(other_quota_dict)
        for q in quota_set:
            self.assertEqual(q.limit, quota_dict[q.name])

    def test_quotaset_add_doesnt_override_existing_quota(self):
        quota_dict = {'foo': 1, 'bar': 10}
        quota_set = api_base.QuotaSet(quota_dict)
        other_quota_set = api_base.QuotaSet({'foo': 12})

        quota_set += other_quota_set
        self.assertEqual(len(quota_set), 2)

        for q in quota_set:
            self.assertEqual(q.limit, quota_dict[q.name])

    def test_quotaset_add_method(self):
        quota_dict = {'foo': 1, 'bar': 10}
        other_quota_dict = {'my_test': 12}
        quota_set = api_base.QuotaSet(quota_dict)
        other_quota_set = api_base.QuotaSet(other_quota_dict)

        quota_set.add(other_quota_set)
        self.assertEqual(len(quota_set), 3)

        quota_dict.update(other_quota_dict)
        for q in quota_set:
            self.assertEqual(q.limit, quota_dict[q.name])

    def test_quotaset_add_with_wrong_type(self):
        quota_set = api_base.QuotaSet({'foo': 1, 'bar': 10})
        self.assertRaises(ValueError, quota_set.add, {'test': 7})
