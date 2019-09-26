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

from django.test import utils as test_utils

from openstack_dashboard.test import helpers as test
from openstack_dashboard.utils import settings as utils


class SettingsTests(test.TestCase):
    def test_get_dict_config_default_value(self):
        self.assertEqual(
            True,
            utils.get_dict_config('OPENSTACK_NEUTRON_NETWORK',
                                  'enable_router'))

    @test_utils.override_settings(OPENSTACK_NEUTRON_NETWORK={
        'enable_router': False})
    def test_get_dict_config_configured_value(self):
        self.assertEqual(
            False,
            utils.get_dict_config('OPENSTACK_NEUTRON_NETWORK',
                                  'enable_router'))

    @test_utils.override_settings(OPENSTACK_NEUTRON_NETWORK={})
    def test_get_dict_config_missing_key(self):
        self.assertEqual(
            True,
            utils.get_dict_config('OPENSTACK_NEUTRON_NETWORK',
                                  'enable_router'))
