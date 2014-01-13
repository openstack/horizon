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

import math

from django.conf import settings
from django.contrib.auth import logout  # noqa
from django import http
from django.utils.encoding import force_unicode
from django.utils.functional import lazy  # noqa
from django.utils import translation


def _lazy_join(separator, strings):
    return separator.join([force_unicode(s)
                           for s in strings])

lazy_join = lazy(_lazy_join, unicode)


def bytes_to_gigabytes(bytes):
    # Converts the number of bytes to the next highest number of Gigabytes
    # For example 5000000 (5 Meg) would return '1'
    return int(math.ceil(float(bytes) / 1024 ** 3))


def add_logout_reason(request, response, reason):
    # Store the translated string in the cookie
    lang = translation.get_language_from_request(request)
    with translation.override(lang):
        reason = unicode(reason).encode('utf-8')
        response.set_cookie('logout_reason', reason, max_age=30)


def logout_with_message(request, msg):
    """Send HttpResponseRedirect to LOGOUT_URL.

    `msg` is a message displayed on the login page after the logout, to explain
    the logout reason.
    """
    logout(request)
    response = http.HttpResponseRedirect(
        '%s?next=%s' % (settings.LOGOUT_URL, request.path))
    add_logout_reason(request, response, msg)
    return response


def get_page_size(request, default=20):
    session = request.session
    cookies = request.COOKIES
    return int(session.get('horizon_pagesize',
                           cookies.get('horizon_pagesize',
                                       getattr(settings,
                                               'API_RESULT_PAGE_SIZE',
                                               default))))
