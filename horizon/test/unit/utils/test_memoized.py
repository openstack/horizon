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
