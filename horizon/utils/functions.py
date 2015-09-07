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

import decimal
import math
import re

from oslo_utils import units
import six

from django.conf import settings
from django.contrib.auth import logout  # noqa
from django import http
from django.utils.encoding import force_text
from django.utils.functional import lazy  # noqa
from django.utils import translation


def _lazy_join(separator, strings):
    return separator.join([force_text(s)
                           for s in strings])

lazy_join = lazy(_lazy_join, six.text_type)


def bytes_to_gigabytes(bytes):
    # Converts the number of bytes to the next highest number of Gigabytes
    # For example 5000000 (5 Meg) would return '1'
    return int(math.ceil(float(bytes) / units.Gi))


def add_logout_reason(request, response, reason):
    # Store the translated string in the cookie
    lang = translation.get_language_from_request(request)
    with translation.override(lang):
        reason = six.text_type(reason)
        if six.PY2:
            reason = reason.encode('utf-8')
        response.set_cookie('logout_reason', reason, max_age=10)


def logout_with_message(request, msg, redirect=True):
    """Send HttpResponseRedirect to LOGOUT_URL.

    `msg` is a message displayed on the login page after the logout, to explain
    the logout reason.
    """
    logout(request)
    if redirect:
        response = http.HttpResponseRedirect(
            '%s?next=%s' % (settings.LOGOUT_URL, request.path))
    else:
        response = http.HttpResponseRedirect(settings.LOGOUT_URL)
    add_logout_reason(request, response, msg)
    return response


def get_page_size(request, default=20):
    session = request.session
    cookies = request.COOKIES
    try:
        page_size = int(session.get('horizon_pagesize',
                                    cookies.get('horizon_pagesize',
                                                getattr(settings,
                                                        'API_RESULT_PAGE_SIZE',
                                                        default))))
    except ValueError:
        page_size = session['horizon_pagesize'] = int(default)
    return page_size


def get_log_length(request, default=35):
    session = request.session
    cookies = request.COOKIES
    try:
        log_length = int(session.get(
            'instance_log_length',
            cookies.get('instance_log_length',
                        getattr(settings,
                                'INSTANCE_LOG_LENGTH',
                                default))))
    except ValueError:
        log_length = session['instance_log_length'] = int(default)
    return log_length


def natural_sort(attr):
    return lambda x: [int(s) if s.isdigit() else s for s in
                      re.split(r'(\d+)', getattr(x, attr, x))]


def get_keys(tuple_of_tuples):
    """Processes a tuple of 2-element tuples and returns a tuple containing
    first component of each tuple.
    """
    return tuple([t[0] for t in tuple_of_tuples])


def value_for_key(tuple_of_tuples, key):
    """Processes a tuple of 2-element tuples and returns the value
    corresponding to the given key. If not value is found, the key is returned.
    """
    for t in tuple_of_tuples:
        if t[0] == key:
            return t[1]
    else:
        return key


def next_key(tuple_of_tuples, key):
    """Processes a tuple of 2-element tuples and returns the key which comes
    after the given key.
    """
    for i, t in enumerate(tuple_of_tuples):
        if t[0] == key:
            try:
                return tuple_of_tuples[i + 1][0]
            except IndexError:
                return None


def previous_key(tuple_of_tuples, key):
    """Processes a tuple of 2-element tuples and returns the key which comes
    before the given key.
    """
    for i, t in enumerate(tuple_of_tuples):
        if t[0] == key:
            try:
                return tuple_of_tuples[i - 1][0]
            except IndexError:
                return None


def format_value(value):
    """Returns the given value rounded to one decimal place if it is a
    decimal, or integer if it is an integer.
    """
    value = decimal.Decimal(str(value))
    if int(value) == value:
        return int(value)
    return round(value, 1)
