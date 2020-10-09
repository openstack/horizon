# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.middleware import csrf
from django import test

from openstack_auth import views


class CsrfTestCase(test.TestCase):
    COOKIES_OFF_MSG = ("Cookies may be turned off. "
                       "Make sure cookies are enabled and try again.")

    def test_no_csrf(self):
        reason = views.get_csrf_reason(None)
        self.assertIsNone(reason)

    def test_valid_csrf(self):
        reason = views.get_csrf_reason(csrf.REASON_NO_CSRF_COOKIE)
        expected = csrf.REASON_NO_CSRF_COOKIE + " " + self.COOKIES_OFF_MSG

        self.assertEqual(expected, reason)

    def test_invalid_csrf(self):
        reason = views.get_csrf_reason("error message")
        expected = self.COOKIES_OFF_MSG

        self.assertEqual(expected, reason)
