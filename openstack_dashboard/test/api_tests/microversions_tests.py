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

import unittest

import mock

from openstack_dashboard.api import microversions


class _VersionWrapper(object):

    def __init__(self, version):
        self.version = version

    def matches(self, min_ver, max_ver):
        return min_ver <= self.version <= max_ver


class MicroversionsTests(unittest.TestCase):

    def _test_get_microversion(self, min_ver, max_ver,
                               features=None, service=None,
                               feature_versions=None):
        if feature_versions is None:
            feature_versions = {'myservice': {'feature_a': ['2.3', '2.5']}}
        if features is None:
            features = ['feature_a']
        if service is None:
            service = 'myservice'
        with mock.patch.object(microversions, 'MICROVERSION_FEATURES',
                               feature_versions):
            return microversions.get_microversion_for_features(
                service, features, _VersionWrapper, min_ver, max_ver)

    def test_get_microversion(self):
        ret = self._test_get_microversion('2.1', '2.5')
        self.assertIsInstance(ret, _VersionWrapper)
        self.assertEqual('2.5', ret.version)

    def test_get_microversion_second_version(self):
        ret = self._test_get_microversion('2.1', '2.4')
        self.assertIsInstance(ret, _VersionWrapper)
        self.assertEqual('2.3', ret.version)

    def test_get_microversion_out_of_range(self):
        ret = self._test_get_microversion('2.1', '2.2')
        self.assertIsNone(ret)

    def test_get_microversion_string_feature(self):
        ret = self._test_get_microversion('2.1', '2.5', 'feature_a')
        self.assertIsInstance(ret, _VersionWrapper)
        # NOTE: ret.version depends on a wrapper class.
        self.assertEqual('2.5', ret.version)

    def test_get_microversion_multiple_features(self):
        feature_versions = {'myservice': {'feature_a': ['2.3', '2.5', '2.7'],
                                          'feature_b': ['2.5', '2.7', '2.8']}}
        ret = self._test_get_microversion(
            '2.1', '2.9', ['feature_a', 'feature_b'],
            feature_versions=feature_versions)
        self.assertIsInstance(ret, _VersionWrapper)
        self.assertEqual('2.7', ret.version)

    def test_get_microversion_multiple_features_second_largest(self):
        feature_versions = {'myservice': {'feature_a': ['2.3', '2.5', '2.7'],
                                          'feature_b': ['2.5', '2.7', '2.8']}}
        ret = self._test_get_microversion(
            '2.1', '2.6', ['feature_a', 'feature_b'],
            feature_versions=feature_versions)
        self.assertIsInstance(ret, _VersionWrapper)
        self.assertEqual('2.5', ret.version)

    def test_get_microversion_multiple_features_out_of_range(self):
        feature_versions = {'myservice': {'feature_a': ['2.3', '2.5', '2.7'],
                                          'feature_b': ['2.5', '2.7', '2.8']}}
        ret = self._test_get_microversion(
            '2.1', '2.4', ['feature_a', 'feature_b'],
            feature_versions=feature_versions)
        self.assertIsNone(ret)

    def test_get_microversion_multiple_features_no_common_version(self):
        feature_versions = {'myservice': {'feature_a': ['2.3', '2.5', '2.7'],
                                          'feature_b': ['2.6', '2.8']}}
        ret = self._test_get_microversion(
            '2.1', '2.9', ['feature_a', 'feature_b'],
            feature_versions=feature_versions)
        self.assertIsNone(ret)

    def test_get_microversion_version_number_sort(self):
        feature_versions = {'myservice': {'feature_a': ['2.3', '2.20', '2.2']}}
        ret = self._test_get_microversion('2.1', '2.30',
                                          feature_versions=feature_versions)
        self.assertIsInstance(ret, _VersionWrapper)
        self.assertEqual('2.20', ret.version)

    def test_get_microversion_undefined_service(self):
        ret = self._test_get_microversion('2.1', '2.5', service='notfound')
        self.assertIsNone(ret)
