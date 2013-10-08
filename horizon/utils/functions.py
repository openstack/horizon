import math

from django.conf import settings  # noqa
from django.contrib.auth import logout  # noqa
from django import http
from django.utils.encoding import force_unicode  # noqa
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
    the logout reson.
    """
    logout(request)
    response = http.HttpResponseRedirect(
        '%s?next=%s' % (settings.LOGOUT_URL, request.path))
    add_logout_reason(request, response, msg)
    return response
