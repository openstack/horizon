# Copyright (c) 2013 OpenStack Foundation
# All Rights Reserved.
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

import datetime
import uuid

from openstack_dashboard.test import helpers as test
from openstack_dashboard.utils import filters
from openstack_dashboard.utils import metering


class UtilsFilterTests(test.TestCase):
    def test_accept_valid_integer(self):
        val = 100
        ret = filters.get_int_or_uuid(val)
        self.assertEqual(val, ret)

    def test_accept_valid_integer_string(self):
        val = '100'
        ret = filters.get_int_or_uuid(val)
        self.assertEqual(int(val), ret)

    def test_accept_valid_uuid(self):
        val = str(uuid.uuid4())
        ret = filters.get_int_or_uuid(val)
        self.assertEqual(val, ret)

    def test_reject_random_string(self):
        val = '55WbJTpJDf'
        self.assertRaises(ValueError, filters.get_int_or_uuid, val)


class UtilsMeteringTests(test.TestCase):

    def test_calc_date_args_strings(self):
        date_from, date_to = metering.calc_date_args(
            "2012-04-11", "2012-04-12", "other")
        self.assertTrue(type(date_from) is datetime.datetime)
        self.assertTrue(type(date_to) is datetime.datetime)
        self.assertEqual(str(date_from.tzinfo), "UTC")
        self.assertEqual(str(date_to.tzinfo), "UTC")

    def test_calc_date_args_datetime_dates(self):
        date_from, date_to = metering.calc_date_args(
            datetime.date(2012, 4, 11), datetime.date(2012, 4, 12), "other")
        self.assertTrue(type(date_from) is datetime.datetime)
        self.assertTrue(type(date_to) is datetime.datetime)
        self.assertEqual(str(date_from.tzinfo), "UTC")
        self.assertEqual(str(date_to.tzinfo), "UTC")

    def test_calc_date_args_invalid(self):
        self.assertRaises(
            ValueError, metering.calc_date_args, object, object, "other")
