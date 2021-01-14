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

import datetime
import json
import logging

import pytz

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages as django_messages
from django import http
from django import shortcuts
from django.utils.encoding import iri_to_uri
from django.utils import timezone

from horizon import exceptions
from horizon.utils import functions as utils


LOG = logging.getLogger(__name__)


class HorizonMiddleware(object):
    """The main Horizon middleware class. Required for use of Horizon."""

    logout_reason = None

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self._process_request(request)
        response = self.get_response(request)
        response = self._process_response(request, response)
        return response

    def _process_request(self, request):
        """Adds data necessary for Horizon to function to the request."""

        request.horizon = {'dashboard': None,
                           'panel': None,
                           'async_messages': []}
        if not hasattr(request, "user") or not request.user.is_authenticated:
            # proceed no further if the current request is already known
            # not to be authenticated
            # it is CRITICAL to perform this check as early as possible
            # to avoid creating too many sessions
            return None

        # Since we know the user is present and authenticated, lets refresh the
        # session expiry if configured to do so.
        if settings.SESSION_REFRESH:
            timeout = settings.SESSION_TIMEOUT
            token_life = request.user.token.expires - datetime.datetime.now(
                pytz.utc)
            session_time = min(timeout, int(token_life.total_seconds()))
            request.session.set_expiry(session_time)

        if request.is_ajax():
            # if the request is Ajax we do not want to proceed, as clients can
            #  1) create pages with constant polling, which can create race
            #     conditions when a page navigation occurs
            #  2) might leave a user seemingly left logged in forever
            #  3) thrashes db backed session engines with tons of changes
            return None
        # If we use cookie-based sessions, check that the cookie size does not
        # reach the max size accepted by common web browsers.
        if (
            settings.SESSION_ENGINE ==
            'django.contrib.sessions.backends.signed_cookies'
        ):
            max_cookie_size = settings.SESSION_COOKIE_MAX_SIZE
            session_cookie_name = settings.SESSION_COOKIE_NAME
            session_key = request.COOKIES.get(session_cookie_name)
            if max_cookie_size is not None and session_key is not None:
                cookie_size = sum((
                    len(key) + len(value)
                    for key, value in request.COOKIES.items()
                ))
                if cookie_size >= max_cookie_size:
                    LOG.error(
                        'Total Cookie size for user_id: %(user_id)s is '
                        '%(cookie_size)sB >= %(max_cookie_size)sB. '
                        'You need to configure file-based or database-backed '
                        'sessions instead of cookie-based sessions: '
                        'https://docs.openstack.org/horizon/latest/'
                        'admin/sessions.html',
                        {
                            'user_id': request.session.get(
                                'user_id', 'Unknown'),
                            'cookie_size': cookie_size,
                            'max_cookie_size': max_cookie_size,
                        }
                    )

        tz = utils.get_timezone(request)
        if tz:
            timezone.activate(tz)

    def process_exception(self, request, exception):
        """Catches internal Horizon exception classes.

        Exception classes such as NotAuthorized, NotFound and Http302
        are caught and handles them gracefully.
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
            if isinstance(exception, exceptions.NotAuthorized):
                response.delete_cookie('messages')
                return shortcuts.render(request, 'not_authorized.html',
                                        status=403)

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

    @staticmethod
    def _copy_headers(src, dst, headers):
        for header in headers:
            dst[header] = src[header]

    def _process_response(self, request, response):
        """Convert HttpResponseRedirect to HttpResponse if request is via ajax.

        This is to allow ajax request to redirect url.
        """
        if request.is_ajax() and hasattr(request, 'horizon'):
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
                            request, redirect_response, self.logout_reason,
                            'error')
                else:
                    redirect_response = http.HttpResponse()
                # Use a set while checking if we want a cookie's attributes
                # copied
                cookie_keys = {'max_age', 'expires', 'path', 'domain',
                               'secure', 'httponly', 'logout_reason'}
                # Copy cookies from HttpResponseRedirect towards HttpResponse
                for cookie_name, cookie in response.cookies.items():
                    cookie_kwargs = dict((
                        (key, value) for key, value in cookie.items()
                        if key in cookie_keys and value
                    ))
                    redirect_response.set_cookie(
                        cookie_name, cookie.value, **cookie_kwargs)
                redirect_response['X-Horizon-Location'] = response['location']
                upload_url_key = 'X-File-Upload-URL'
                if upload_url_key in response:
                    self._copy_headers(response, redirect_response,
                                       (upload_url_key, 'X-Auth-Token'))
                return redirect_response
            if queued_msgs:
                # TODO(gabriel): When we have an async connection to the
                # client (e.g. websockets) this should be pushed to the
                # socket queue rather than being sent via a header.
                # The header method has notable drawbacks (length limits,
                # etc.) and is not meant as a long-term solution.
                response['X-Horizon-Messages'] = json.dumps(queued_msgs)
        return response
