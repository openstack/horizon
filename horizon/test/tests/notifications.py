# Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

from django.conf import settings

from horizon import exceptions
from horizon.notifications import JSONMessage
from horizon.test import helpers as test


class NotificationTests(test.TestCase):

    MESSAGES_PATH = os.path.abspath(os.path.join(settings.ROOT_PATH,
                                                 'messages'))

    def _test_msg(self, path, expected_level, expected_msg=''):
        msg = JSONMessage(path)
        msg.load()

        self.assertEqual(expected_level, msg.level_name)
        self.assertEqual(expected_msg, msg.message)

    def test_warning_msg(self):
        path = self.MESSAGES_PATH + '/test_warning.json'

        self._test_msg(path, 'warning', 'warning message')

    def test_info_msg(self):
        path = self.MESSAGES_PATH + '/test_info.json'

        self._test_msg(path, 'info', 'info message')

    def test_invalid_msg_file(self):
        path = self.MESSAGES_PATH + '/test_invalid.json'

        with self.assertRaises(exceptions.MessageFailure):
            msg = JSONMessage(path)
            msg.load()

    def test_invalid_msg_file_fail_silently(self):
        path = self.MESSAGES_PATH + '/test_invalid.json'

        msg = JSONMessage(path, fail_silently=True)
        msg.load()

        self.assertTrue(msg.failed)
