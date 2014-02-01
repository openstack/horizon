# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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
Middleware provided and used by Horizon.
"""

import json
import logging
import time

from django.conf import settings  # noqa
from django.contrib.auth import REDIRECT_FIELD_NAME  # noqa
from django.contrib.auth.views import redirect_to_login  # noqa
from django.contrib import messages as django_messages
from django import http
from django.http import HttpResponseRedirect  # noqa
from django import shortcuts
from django.utils.encoding import iri_to_uri  # noqa
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon.utils import functions as utils

LOG = logging.getLogger(__name__)


class HorizonMiddleware(object):
    """ The main Horizon middleware class. Required for use of Horizon. """

    logout_reason = None

    def process_request(self, request):
        """ Adds data necessary for Horizon to function to the request. """
        # Activate timezone handling
        tz = request.session.get('django_timezone')
        if tz:
            timezone.activate(tz)

        # Check for session timeout
        try:
            timeout = settings.SESSION_TIMEOUT
        except AttributeError:
            timeout = 1800

        last_activity = request.session.get('last_activity', None)
        timestamp = int(time.time())
        request.horizon = {'dashboard': None,
                           'panel': None,
                           'async_messages': []}
        if (isinstance(last_activity, int)
                and (timestamp - last_activity) > timeout):
            request.session.pop('last_activity')
            response = HttpResponseRedirect(
                '%s?next=%s' % (settings.LOGOUT_URL, request.path))
            self.logout_reason = _("Session timed out.")
            utils.add_logout_reason(request, response, self.logout_reason)
            return response
        request.session['last_activity'] = timestamp

    def process_exception(self, request, exception):
        """
        Catches internal Horizon exception classes such as NotAuthorized,
        NotFound and Http302 and handles them gracefully.
        """
        if isinstance(exception, (exceptions.NotAuthorized,
                                  exceptions.NotAuthenticated)):
            auth_url = settings.LOGIN_URL
            next_url = iri_to_uri(request.get_full_path())
            if next_url != auth_url:
                field_name = REDIRECT_FIELD_NAME
            else:
                field_name = None
            login_url = request.build_absolute_uri(auth_url)
            response = redirect_to_login(next_url, login_url=login_url,
                                         redirect_field_name=field_name)

            if request.is_ajax():
                response_401 = http.HttpResponse(status=401)
                response_401['X-Horizon-Location'] = response['location']
                return response_401

            return response

        # If an internal "NotFound" error gets this far, return a real 404.
        if isinstance(exception, exceptions.NotFound):
            raise http.Http404(exception)

        if isinstance(exception, exceptions.Http302):
            # TODO(gabriel): Find a way to display an appropriate message to
            # the user *on* the login form...
            return shortcuts.redirect(exception.location)

    def process_response(self, request, response):
        """
        Convert HttpResponseRedirect to HttpResponse if request is via ajax
        to allow ajax request to redirect url
        """
        if request.is_ajax():
            queued_msgs = request.horizon['async_messages']
            if type(response) == http.HttpResponseRedirect:
                # Drop our messages back into the session as per usual so they
                # don't disappear during the redirect. Not that we explicitly
                # use django's messages methods here.
                for tag, message, extra_tags in queued_msgs:
                    getattr(django_messages, tag)(request, message, extra_tags)
                if response['location'].startswith(settings.LOGOUT_URL):
                    redirect_response = http.HttpResponse(status=401)
                    # This header is used for handling the logout in JS
                    redirect_response['logout'] = True
                    if self.logout_reason is not None:
                        utils.add_logout_reason(
                            request, redirect_response, self.logout_reason)
                else:
                    redirect_response = http.HttpResponse()
                # Copy cookies from HttpResponseRedirect towards HttpResponse
                for cookie_name, cookie in response.cookies.iteritems():
                    cookie_kwargs = dict((
                        (key, value) for key, value in cookie.iteritems()
                        if key in ('max_age', 'expires', 'path', 'domain',
                            'secure', 'httponly') and value
                    ))
                    redirect_response.set_cookie(
                        cookie_name, cookie.value, **cookie_kwargs)
                redirect_response['X-Horizon-Location'] = response['location']
                return redirect_response
            if queued_msgs:
                # TODO(gabriel): When we have an async connection to the
                # client (e.g. websockets) this should be pushed to the
                # socket queue rather than being sent via a header.
                # The header method has notable drawbacks (length limits,
                # etc.) and is not meant as a long-term solution.
                response['X-Horizon-Messages'] = json.dumps(queued_msgs)
        return response
