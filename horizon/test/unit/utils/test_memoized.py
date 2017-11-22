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

    def test_memoized_with_request_call(self):

        chorus = [
            "I",
            "Love",
            "Rock 'n' Roll",
            "put another coin",
            "in the Jukebox Baby."
        ]

        leader = 'Joan Jett'
        group = 'Blackhearts'

        for position, chorus_line in enumerate(chorus):

            changed_args = False

            def some_func(some_param):
                if not changed_args:
                    self.assertEqual(some_param, chorus_line)
                else:
                    self.assertNotEqual(some_param, chorus_line)
                    self.assertEqual(some_param, group)
                return leader

            @memoized.memoized_with_request(some_func, position)
            def some_other_func(*args):
                return args

            # check chorus_copy[position] is replaced by some_func's
            # output
            output1 = some_other_func(*chorus)
            self.assertEqual(output1[position], leader)

            # Change args used to call the function
            chorus_copy = list(chorus)
            chorus_copy[position] = group
            changed_args = True
            # check that some_func is called with a different parameter, and
            # that check chorus_copy[position] is replaced by some_func's
            # output and some_other_func still called with the same parameters
            output2 = some_other_func(*chorus_copy)
            self.assertEqual(output2[position], leader)
            # check that some_other_func returned a memoized list.
            self.assertIs(output1, output2)
