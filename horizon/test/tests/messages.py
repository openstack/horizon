# Copyright 2012 Nebula, Inc.
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

import json

from django import http
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from horizon import messages
from horizon import middleware
from horizon.test import helpers as test


class MessageTests(test.TestCase):
    def test_middleware_header(self):
        req = self.request
        string = "Giant ants are attacking San Francisco!"
        expected = ["error", force_text(string), ""]
        self.assertIn("async_messages", req.horizon)
        self.assertItemsEqual(req.horizon['async_messages'], [])
        req.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        messages.error(req, string)
        self.assertItemsEqual(req.horizon['async_messages'], [expected])
        res = http.HttpResponse()
        res = middleware.HorizonMiddleware().process_response(req, res)
        self.assertEqual(json.dumps([expected]),
                         res['X-Horizon-Messages'])

    def test_error_message(self):
        req = self.request
        string = mark_safe("We are now safe from ants! Go <a>here</a>!")
        expected = ["error", force_text(string), " safe"]
        self.assertIn("async_messages", req.horizon)
        self.assertItemsEqual(req.horizon['async_messages'], [])
        req.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        messages.error(req, string)
        self.assertItemsEqual(req.horizon['async_messages'], [expected])
        res = http.HttpResponse()
        res = middleware.HorizonMiddleware().process_response(req, res)
        self.assertEqual(json.dumps([expected]),
                         res['X-Horizon-Messages'])
