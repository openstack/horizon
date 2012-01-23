# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Nebula, Inc.
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
import sys

from django.contrib import messages
from django.utils.translation import ugettext as _
from cloudfiles import errors as swiftclient
from glance.common import exception as glanceclient
from keystoneclient import exceptions as keystoneclient
from novaclient import exceptions as novaclient
from openstackx.api import exceptions as openstackx


LOG = logging.getLogger(__name__)


UNAUTHORIZED = (openstackx.Unauthorized,
                openstackx.Unauthorized,
                keystoneclient.Unauthorized,
                keystoneclient.Forbidden,
                novaclient.Unauthorized,
                novaclient.Forbidden,
                glanceclient.AuthorizationFailure,
                glanceclient.NotAuthorized,
                swiftclient.AuthenticationFailed,
                swiftclient.AuthenticationError)

NOT_FOUND = (keystoneclient.NotFound,
             novaclient.NotFound,
             openstackx.NotFound,
             glanceclient.NotFound,
             swiftclient.NoSuchContainer,
             swiftclient.NoSuchObject)

# NOTE(gabriel): This is very broad, and may need to be dialed in.
RECOVERABLE = (keystoneclient.ClientException,
               novaclient.ClientException,
               openstackx.ApiException,
               glanceclient.GlanceException,
               swiftclient.Error)


class Http302(Exception):
    """
    Error class which can be raised from within a handler to cause an
    early bailout and redirect at the middleware level.
    """
    def __init__(self, location, message=None):
        self.location = location
        self.message = message


class NotAuthorized(Exception):
    """
    Raised whenever a user attempts to access a resource which they do not
    have role-based access to (such as when failing the
    :func:`~horizon.decorators.require_roles` decorator).

    The included :class:`~horizon.middleware.HorizonMiddleware` catches
    ``NotAuthorized`` and handles it gracefully by displaying an error
    message and redirecting the user to a login page.
    """
    pass


class ServiceCatalogException(Exception):
    """
    Raised when a requested service is not available in the ``ServiceCatalog``
    returned by Keystone.
    """
    def __init__(self, service_name):
        message = 'Invalid service catalog service: %s' % service_name
        super(ServiceCatalogException, self).__init__(message)


class HandledException(Exception):
    """
    Used internally to track exceptions that have gone through
    :func:`horizon.exceptions.handle` more than once.
    """
    def __init__(self, wrapped):
        self.wrapped = wrapped


def handle(request, message=None, redirect=None, ignore=False, escalate=False):
    """ Centralized error handling for Horizon.

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
    errors are
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()

    # Because the same exception may travel through this method more than
    # once (if it's re-raised) we may want to treat it differently
    # the second time (e.g. no user messages/logging).
    handled = issubclass(exc_type, HandledException)
    wrap = False

    # Restore our original exception information, but re-wrap it at the end
    if handled:
        exc_type, exc_value, exc_traceback = exc_value.wrapped
        wrap = True

    # If the message has a placeholder for the exception, fill it in
    if message and "%(exc)s" in message:
        message = message % {"exc": exc_value}

    if issubclass(exc_type, UNAUTHORIZED):
        if ignore:
            return
        request.session.clear()
        if not handled:
            LOG.debug("Unauthorized: %s" % exc_value)
            # We get some pretty useless error messages back from
            # some clients, so let's define our own fallback.
            fallback = _("Unauthorized. Please try logging in again.")
            messages.error(request, message or fallback, extra_tags="login")
        raise NotAuthorized  # Redirect handled in middleware

    if issubclass(exc_type, NOT_FOUND):
        if not ignore and not handled:
            LOG.debug("Not Found: %s" % exc_value)
            messages.error(request, message or exc_value)
        if redirect:
            raise Http302(redirect)
        wrap = True
        if not escalate:
            return  # return to normal code flow

    if issubclass(exc_type, RECOVERABLE) and not ignore:
        if not ignore and not handled:
            LOG.debug("Recoverable error: %s" % exc_value)
            messages.error(request, message or exc_value)
            wrap = True
        if redirect:
            raise Http302(redirect)
        if not escalate:
            return  # return to normal code flow

    # If we've gotten here, time to wrap and/or raise our exception.
    if wrap:
        raise HandledException([exc_type, exc_value, exc_traceback])
    raise exc_type, exc_value, exc_traceback
