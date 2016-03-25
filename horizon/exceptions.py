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

"""
Exceptions raised by the Horizon code and the machinery for handling them.
"""

import logging
import os
import sys

import six

from django.core.management import color_style  # noqa
from django.http import HttpRequest  # noqa
from django.utils import encoding
from django.utils.translation import ugettext_lazy as _
from django.views.debug import CLEANSED_SUBSTITUTE  # noqa
from django.views.debug import SafeExceptionReporterFilter  # noqa

from horizon.conf import HORIZON_CONFIG  # noqa
from horizon import messages

LOG = logging.getLogger(__name__)


class HorizonReporterFilter(SafeExceptionReporterFilter):
    """Error report filter that's always active, even in DEBUG mode."""
    def is_active(self, request):
        return True


class HorizonException(Exception):
    """Base exception class for distinguishing our own exception classes."""
    pass


class Http302(HorizonException):
    """Error class which can be raised from within a handler to cause an
    early bailout and redirect at the middleware level.
    """
    status_code = 302

    def __init__(self, location, message=None):
        self.location = location
        self.message = message


class NotAuthorized(HorizonException):
    """Raised whenever a user attempts to access a resource which they do not
    have permission-based access to (such as when failing the
    :func:`~horizon.decorators.require_perms` decorator).

    The included :class:`~horizon.middleware.HorizonMiddleware` catches
    ``NotAuthorized`` and handles it gracefully by displaying an error
    message and redirecting the user to a login page.
    """
    status_code = 401


class NotAuthenticated(HorizonException):
    """Raised when a user is trying to make requests and they are not logged
    in.

    The included :class:`~horizon.middleware.HorizonMiddleware` catches
    ``NotAuthenticated`` and handles it gracefully by displaying an error
    message and redirecting the user to a login page.
    """
    status_code = 403


class NotFound(HorizonException):
    """Generic error to replace all "Not Found"-type API errors."""
    status_code = 404


class Conflict(HorizonException):
    """Generic error to replace all "Conflict"-type API errors."""
    status_code = 409


class BadRequest(HorizonException):
    """Generic error to replace all "BadRequest"-type API errors."""
    status_code = 400


class RecoverableError(HorizonException):
    """Generic error to replace any "Recoverable"-type API errors."""
    status_code = 100  # HTTP status code "Continue"


class ServiceCatalogException(HorizonException):
    """Raised when a requested service is not available in the
    ``ServiceCatalog`` returned by Keystone.
    """
    def __init__(self, service_name):
        message = 'Invalid service catalog service: %s' % service_name
        super(ServiceCatalogException, self).__init__(message)


@six.python_2_unicode_compatible
class AlreadyExists(HorizonException):
    """Exception to be raised when trying to create an API resource which
    already exists.
    """
    def __init__(self, name, resource_type):
        self.attrs = {"name": name, "resource": resource_type}
        self.msg = _('A %(resource)s with the name "%(name)s" already exists.')

    def __repr__(self):
        return self.msg % self.attrs

    def __str__(self):
        return self.msg % self.attrs


@six.python_2_unicode_compatible
class GetFileError(HorizonException):
    """Exception to be raised when the value of get_file did not start with
    https:// or http://
    """
    def __init__(self, name, resource_type):
        self.attrs = {"name": name, "resource": resource_type}
        self.msg = _('The value of %(resource)s is %(name)s inside the '
                     'template. When launching a stack from this interface,'
                     ' the value must start with "http://" or "https://"')

    def __repr__(self):
        return '<%s name=%r resource_type=%r>' % (self.__class__.__name__,
                                                  self.attrs['name'],
                                                  self.attrs['resource_type'])

    def __str__(self):
        return self.msg % self.attrs


class ConfigurationError(HorizonException):
    """Exception to be raised when invalid settings have been provided."""
    pass


class NotAvailable(HorizonException):
    """Exception to be raised when something is not available."""
    pass


class WorkflowError(HorizonException):
    """Exception to be raised when something goes wrong in a workflow."""
    pass


class WorkflowValidationError(HorizonException):
    """Exception raised during workflow validation if required data is missing,
    or existing data is not valid.
    """
    pass


class MessageFailure(HorizonException):
    """Exception raised during message notification."""
    pass


class HandledException(HorizonException):
    """Used internally to track exceptions that have gone through
    :func:`horizon.exceptions.handle` more than once.
    """
    def __init__(self, wrapped):
        self.wrapped = wrapped


UNAUTHORIZED = tuple(HORIZON_CONFIG['exceptions']['unauthorized'])
UNAUTHORIZED += (NotAuthorized,)
NOT_FOUND = tuple(HORIZON_CONFIG['exceptions']['not_found'])
NOT_FOUND += (GetFileError,)
RECOVERABLE = (AlreadyExists, Conflict, NotAvailable, ServiceCatalogException,
               BadRequest)
RECOVERABLE += tuple(HORIZON_CONFIG['exceptions']['recoverable'])


def error_color(msg):
    return color_style().ERROR_OUTPUT(msg)


def check_message(keywords, message):
    """Checks an exception for given keywords and raises a new ``ActionError``
    with the desired message if the keywords are found. This allows selective
    control over API error messages.
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if set(str(exc_value).split(" ")).issuperset(set(keywords)):
        exc_value.message = message
        raise


def handle_unauthorized(request, message, redirect, ignore, escalate, handled,
                        force_silence, force_log,
                        log_method, log_entry, log_level):
    if ignore:
        return NotAuthorized
    if not force_silence and not handled:
        log_method(error_color("Unauthorized: %s" % log_entry))
    if not handled:
        if message:
            message = _("Unauthorized: %s") % message
        # We get some pretty useless error messages back from
        # some clients, so let's define our own fallback.
        fallback = _("Unauthorized. Please try logging in again.")
        messages.error(request, message or fallback)
    # Escalation means logging the user out and raising NotAuthorized
    # so the middleware will redirect them appropriately.
    if escalate:
        # Prevents creation of circular import. django.contrib.auth
        # requires openstack_dashboard.settings to be loaded (by trying to
        # access settings.CACHES in django.core.caches) while
        # openstack_dashboard.settings requires django.contrib.auth to be
        # loaded while importing openstack_auth.utils
        from django.contrib.auth import logout  # noqa
        logout(request)
        raise NotAuthorized
    # Otherwise continue and present our "unauthorized" error message.
    return NotAuthorized


def handle_notfound(request, message, redirect, ignore, escalate, handled,
                    force_silence, force_log,
                    log_method, log_entry, log_level):
    if not force_silence and not handled and (not ignore or force_log):
        log_method(error_color("Not Found: %s" % log_entry))
    if not ignore and not handled:
        messages.error(request, message or log_entry)
    if redirect:
        raise Http302(redirect)
    if not escalate:
        return NotFound  # return to normal code flow


def handle_recoverable(request, message, redirect, ignore, escalate, handled,
                       force_silence, force_log,
                       log_method, log_entry, log_level):
    if not force_silence and not handled and (not ignore or force_log):
        # Default recoverable error to WARN log level
        log_method = getattr(LOG, log_level or "warning")
        log_method(error_color("Recoverable error: %s" % log_entry))
    if not ignore and not handled:
        messages.error(request, message or log_entry)
    if redirect:
        raise Http302(redirect)
    if not escalate:
        return RecoverableError  # return to normal code flow


HANDLE_EXC_METHODS = [
    {'exc': UNAUTHORIZED, 'handler': handle_unauthorized,
     'set_wrap': False, 'escalate': True},
    {'exc': NOT_FOUND, 'handler': handle_notfound, 'set_wrap': True},
    {'exc': RECOVERABLE, 'handler': handle_recoverable, 'set_wrap': True},
]


def handle(request, message=None, redirect=None, ignore=False,
           escalate=False, log_level=None, force_log=None):
    """Centralized error handling for Horizon.

    Because Horizon consumes so many different APIs with completely
    different ``Exception`` types, it's necessary to have a centralized
    place for handling exceptions which may be raised.

    Exceptions are roughly divided into 3 types:

    #. ``UNAUTHORIZED``: Errors resulting from authentication or authorization
       problems. These result in being logged out and sent to the login screen.
    #. ``NOT_FOUND``: Errors resulting from objects which could not be
       located via the API. These generally result in a user-facing error
       message, but are otherwise returned to the normal code flow. Optionally
       a redirect value may be passed to the error handler so users are
       returned to a different view than the one requested in addition to the
       error message.
    #. RECOVERABLE: Generic API errors which generate a user-facing message
       but drop directly back to the regular code flow.

    All other exceptions bubble the stack as normal unless the ``ignore``
    argument is passed in as ``True``, in which case only unrecognized
    errors are bubbled.

    If the exception is not re-raised, an appropriate wrapper exception
    class indicating the type of exception that was encountered will be
    returned.
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log_method = getattr(LOG, log_level or "exception")
    force_log = force_log or os.environ.get("HORIZON_TEST_RUN", False)
    force_silence = getattr(exc_value, "silence_logging", False)

    # Because the same exception may travel through this method more than
    # once (if it's re-raised) we may want to treat it differently
    # the second time (e.g. no user messages/logging).
    handled = issubclass(exc_type, HandledException)
    wrap = False

    # Restore our original exception information, but re-wrap it at the end
    if handled:
        exc_type, exc_value, exc_traceback = exc_value.wrapped
        wrap = True

    log_entry = encoding.force_text(exc_value)

    user_message = ""
    # We trust messages from our own exceptions
    if issubclass(exc_type, HorizonException):
        user_message = log_entry
    # If the message has a placeholder for the exception, fill it in
    elif message and "%(exc)s" in message:
        user_message = encoding.force_text(message) % {"exc": log_entry}
    elif message:
        user_message = encoding.force_text(message)

    for exc_handler in HANDLE_EXC_METHODS:
        if issubclass(exc_type, exc_handler['exc']):
            if exc_handler['set_wrap']:
                wrap = True
            handler = exc_handler['handler']
            ret = handler(request, user_message, redirect, ignore,
                          exc_handler.get('escalate', escalate),
                          handled, force_silence, force_log,
                          log_method, log_entry, log_level)
            if ret:
                return ret  # return to normal code flow

    # If we've gotten here, time to wrap and/or raise our exception.
    if wrap:
        raise HandledException([exc_type, exc_value, exc_traceback])

    # assume exceptions handled in the code that pass in a message are already
    # handled appropriately and treat as recoverable
    if message:
        ret = handle_recoverable(request, user_message, redirect, ignore,
                                 escalate, handled, force_silence, force_log,
                                 log_method, log_entry, log_level)
        if ret:
            return ret

    six.reraise(exc_type, exc_value, exc_traceback)
