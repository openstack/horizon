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
from horizon.utils import memoized


class MemoizedTests(test.TestCase):
    def test_memoized_decorator_cache_on_next_call(self):
        values_list = []

        @memoized.memoized
        def cache_calls(remove_from):
            values_list.append(remove_from)
            return True

        def non_cached_calls(remove_from):
            values_list.append(remove_from)
            return True

        for x in range(0, 5):
            non_cached_calls(1)
        self.assertEqual(5, len(values_list))

        values_list = []
        for x in range(0, 5):
            cache_calls(1)
        self.assertEqual(1, len(values_list))

    def test_memoized_decorator_cache_with_LRU(self):
        values_list = []

        @memoized.memoized(max_size=5)
        def cache_calls(param):
            values_list.append(param)
            return param

        def non_cached_calls(param):
            values_list.append(param)
            return param

        for x in range(0, 5):
            non_cached_calls(1)
        self.assertEqual(5, len(values_list))

        values_list = []
        for x in range(0, 5):
            cache_calls(1)
        self.assertEqual(1, len(values_list))
        # cache only has value for key with 1

        for x in range(2, 6):
            cache_calls(x)
        self.assertEqual(5, len(values_list))
        # cache has has 5 values, with 1 as least recently used key
        cache_calls(6)
        self.assertEqual(6, len(values_list))
        # 1 is popped off cache
        cache_calls(1)
        self.assertEqual(7, len(values_list))
        # 1 is readded and cached 2 will be popped off

        cache_calls(3)
        self.assertEqual(7, len(values_list))
        # 3 was least recently used, but has now been updated to most recent

        cache_calls(2)
        self.assertEqual(8, len(values_list))
        # 2 is readded, 4 is dropped

        cache_calls(4)
        self.assertEqual(9, len(values_list))
        # 4 is readded, 5 is dropped
