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

from horizon.test import helpers as test
from horizon.utils import units


class UnitsTests(test.TestCase):
    def test_is_supported(self):
        self.assertTrue(units.is_supported('MB'))
        self.assertTrue(units.is_supported('min'))
        self.assertFalse(units.is_supported('KWh'))
        self.assertFalse(units.is_supported('unknown_unit'))

    def test_is_larger(self):
        self.assertTrue(units.is_larger('KB', 'B'))
        self.assertTrue(units.is_larger('MB', 'B'))
        self.assertTrue(units.is_larger('GB', 'B'))
        self.assertTrue(units.is_larger('TB', 'B'))
        self.assertTrue(units.is_larger('GB', 'MB'))
        self.assertFalse(units.is_larger('B', 'KB'))
        self.assertFalse(units.is_larger('MB', 'GB'))

        self.assertTrue(units.is_larger('min', 's'))
        self.assertTrue(units.is_larger('hr', 'min'))
        self.assertTrue(units.is_larger('hr', 's'))
        self.assertFalse(units.is_larger('s', 'min'))

    def test_convert(self):
        self.assertEqual(units.convert(4096, 'MB', 'GB'), (4, 'GB'))
        self.assertEqual(units.convert(4, 'GB', 'MB'), (4096, 'MB'))

        self.assertEqual(units.convert(1.5, 'hr', 'min'), (90, 'min'))
        self.assertEqual(units.convert(12, 'hr', 'day'), (0.5, 'day'))

    def test_normalize(self):
        self.assertEqual(units.normalize(1, 'B'), (1, 'B'))
        self.assertEqual(units.normalize(1000, 'B'), (1000, 'B'))
        self.assertEqual(units.normalize(1024, 'B'), (1, 'KB'))
        self.assertEqual(units.normalize(1024 * 1024, 'B'), (1, 'MB'))
        self.assertEqual(units.normalize(10 * 1024 ** 3, 'B'), (10, 'GB'))
        self.assertEqual(units.normalize(1000 * 1024 ** 4, 'B'), (1000, 'TB'))
        self.assertEqual(units.normalize(1024, 'KB'), (1, 'MB'))
        self.assertEqual(units.normalize(1024 ** 2, 'KB'), (1, 'GB'))
        self.assertEqual(units.normalize(10 * 1024, 'MB'), (10, 'GB'))
        self.assertEqual(units.normalize(0.5, 'KB'), (512, 'B'))
        self.assertEqual(units.normalize(0.0001, 'MB'), (104.9, 'B'))

        self.assertEqual(units.normalize(1, 's'), (1, 's'))
        self.assertEqual(units.normalize(120, 's'), (2, 'min'))
        self.assertEqual(units.normalize(3600, 's'), (60, 'min'))
        self.assertEqual(units.normalize(3600 * 24, 's'), (24, 'hr'))
        self.assertEqual(units.normalize(10 * 3600 * 24, 's'), (10, 'day'))
        self.assertEqual(units.normalize(90, 'min'), (90, 'min'))
        self.assertEqual(units.normalize(150, 'min'), (2.5, 'hr'))
        self.assertEqual(units.normalize(60 * 24, 'min'), (24, 'hr'))
        self.assertEqual(units.normalize(0.5, 'day'), (12, 'hr'))
        self.assertEqual(units.normalize(10800000000000, 'ns'), (3, 'hr'))
        self.assertEqual(units.normalize(14, 'day'), (2, 'week'))
        self.assertEqual(units.normalize(91, 'day'), (3, 'month'))
        self.assertEqual(units.normalize(18, 'month'), (18, 'month'))
        self.assertEqual(units.normalize(24, 'month'), (2, 'year'))

        self.assertEqual(units.normalize(1, 'unknown_unit'),
                         (1, 'unknown_unit'))
