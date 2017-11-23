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

from openstack_dashboard.utils import futurist_utils


class FuturistUtilsTests(unittest.TestCase):

    def test_call_functions_parallel(self):
        def func1():
            return 10

        def func2():
            return 20

        ret = futurist_utils.call_functions_parallel(func1, func2)
        self.assertEqual(ret, (10, 20))

    def test_call_functions_parallel_with_args(self):
        def func1(a):
            return a

        def func2(a, b):
            return a + b

        def func3():
            return 3

        ret = futurist_utils.call_functions_parallel(
            (func1, [5]),
            (func2, [10, 20]),
            func3)
        self.assertEqual(ret, (5, 30, 3))

    def test_call_functions_parallel_with_kwargs(self):
        def func1(a):
            return a

        def func2(a, b):
            return a + b

        def func3():
            return 3

        ret = futurist_utils.call_functions_parallel(
            (func1, [], {'a': 5}),
            (func2, [], {'a': 10, 'b': 20}),
            func3)
        self.assertEqual(ret, (5, 30, 3))
