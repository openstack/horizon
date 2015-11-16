# Copyright 2015, Rackspace, US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock

from django.core.management import call_command
from django.core.management import CommandError
from django.test import TestCase

from horizon.management.commands import startdash
from horizon.management.commands import startpanel


class CommandsTestCase(TestCase):
    def test_startdash_usage_empty(self):
        self.assertRaises(CommandError, call_command, 'startdash')

    @mock.patch.object(startdash.Command, 'handle')
    def test_startdash_usage_correct(self, handle):
        call_command('startdash', 'test_dash')

        handle.assert_called_with(dash_name='test_dash',
                                  extensions=["py", "tmpl", "html", "js",
                                              "css"],
                                  files=[], no_color=False, pythonpath=None,
                                  settings=None, skip_checks=True, target=None,
                                  template=None, traceback=False, verbosity=1)

    def test_startpanel_usage_empty(self):
        self.assertRaises(CommandError, call_command, 'startpanel')

    @mock.patch.object(startpanel.Command, 'handle')
    def test_startpanel_usage_correct(self, handle):
        call_command('startpanel', 'test_dash', '--dashboard=foo.bar')

        handle.assert_called_with(panel_name='test_dash', dashboard='foo.bar',
                                  extensions=["py", "tmpl", "html"],
                                  files=[], no_color=False, pythonpath=None,
                                  settings=None, skip_checks=True, target=None,
                                  template=None, traceback=False, verbosity=1)
