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

import glob
import json
import logging
import os

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages


LOG = logging.getLogger(__name__)

_MESSAGES_CACHE = None
_MESSAGES_MTIME = None


class JSONMessage(object):

    INFO = messages.info
    SUCCESS = messages.success
    WARNING = messages.warning
    ERROR = messages.error

    MESSAGE_LEVELS = {
        'info': INFO,
        'success': SUCCESS,
        'warning': WARNING,
        'error': ERROR
    }

    def __init__(self, path, fail_silently=False):
        self._path = path
        self._data = ''

        self.failed = False
        self.fail_silently = fail_silently
        self.message = ''
        self.level = self.INFO
        self.level_name = 'info'

    def _read(self):
        with open(self._path, 'rb') as file_obj:
            self._data = file_obj.read()

    def _parse(self):
        attrs = {}
        try:
            data = self._data.decode('utf-8')
            attrs = json.loads(data)
        except ValueError as exc:
            self.failed = True

            params = {'path': self._path, 'exception': exc}
            if self.fail_silently:
                LOG.warning("Message json file '%(path)s' is malformed. "
                            "%(exception)s", params)
            else:
                raise exceptions.MessageFailure(
                    _("Message json file '%(path)s' is malformed. "
                      "%(exception)s") % params)
        else:
            level_name = attrs.get('level', 'info')
            if level_name in self.MESSAGE_LEVELS:
                self.level_name = level_name

            self.level = self.MESSAGE_LEVELS.get(self.level_name, self.INFO)
            self.message = attrs.get('message', '')

    def load(self):
        """Read and parse the message file."""
        try:
            self._read()
            self._parse()
        except Exception as exc:
            self.failed = True

            params = {'path': self._path, 'exception': exc}
            if self.fail_silently:
                LOG.warning("Error processing message json file '%(path)s': "
                            "%(exception)s", params)
            else:
                raise exceptions.MessageFailure(
                    _("Error processing message json file '%(path)s': "
                      "%(exception)s") % params)

    def send_message(self, request):
        if self.failed:
            return
        self.level(request, mark_safe(self.message))


def _is_path(path):
    return os.path.exists(path) and os.path.isdir(path)


def _get_processed_messages(messages_path):
    msgs = list()

    if not _is_path(messages_path):
        LOG.error('%s is not a valid messages path.', messages_path)
        return msgs

    # Get all files from messages_path with .json extension
    for fname in glob.glob(os.path.join(messages_path, '*.json')):
        fpath = os.path.join(messages_path, fname)

        msg = JSONMessage(fpath, fail_silently=True)
        msg.load()

        if not msg.failed:
            msgs.append(msg)

    return msgs


def process_message_notification(request, messages_path):
    """Process all the msg file found in the message directory"""
    if not messages_path:
        return

    global _MESSAGES_CACHE
    global _MESSAGES_MTIME

    # NOTE (lhcheng): Cache the processed messages to avoid parsing
    # the files every time. Check directory modification time if
    # reload is necessary.
    if (_MESSAGES_CACHE is None or
            _MESSAGES_MTIME != os.path.getmtime(messages_path)):
        _MESSAGES_CACHE = _get_processed_messages(messages_path)
        _MESSAGES_MTIME = os.path.getmtime(messages_path)

    for msg in _MESSAGES_CACHE:
        msg.send_message(request)
