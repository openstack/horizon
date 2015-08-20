# Copyright 2014, Rackspace, US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import functools
import json
import logging

from django.conf import settings
from django import http
from django.utils import decorators

from oslo_serialization import jsonutils

from horizon import exceptions

log = logging.getLogger(__name__)


class AjaxError(Exception):
    def __init__(self, http_status, msg):
        self.http_status = http_status
        super(AjaxError, self).__init__(msg)

http_errors = exceptions.UNAUTHORIZED + exceptions.NOT_FOUND + \
    exceptions.RECOVERABLE + (AjaxError, )


class CreatedResponse(http.HttpResponse):
    def __init__(self, location, data=None):
        if data is not None:
            content = jsonutils.dumps(data, sort_keys=settings.DEBUG)
            content_type = 'application/json'
        else:
            content = ''
            content_type = None
        super(CreatedResponse, self).__init__(status=201, content=content,
                                              content_type=content_type)
        self['Location'] = location


class JSONResponse(http.HttpResponse):
    def __init__(self, data, status=200, json_encoder=json.JSONEncoder):
        if status == 204:
            content = ''
        else:
            content = jsonutils.dumps(data, sort_keys=settings.DEBUG,
                                      cls=json_encoder)

        super(JSONResponse, self).__init__(
            status=status,
            content=content,
            content_type='application/json',
        )


def ajax(authenticated=True, data_required=False,
         json_encoder=json.JSONEncoder):
    '''Provide a decorator to wrap a view method so that it may exist in an
    entirely AJAX environment:

    - data decoded from JSON as input and data coded as JSON as output
    - result status is coded in the HTTP status code; any non-2xx response
      data will be coded as a JSON string, otherwise the response type (always
      JSON) is specific to the method called.

    if authenticated is true then we'll make sure the current user is
    authenticated.

    If data_required is true then we'll assert that there is a JSON body
    present.

    The wrapped view method should return either:

    - JSON serialisable data
    - an object of the django http.HttpResponse subclass (one of JSONResponse
      or CreatedResponse is suggested)
    - nothing

    Methods returning nothing (or None explicitly) will result in a 204 "NO
    CONTENT" being returned to the caller.
    '''
    def decorator(function, authenticated=authenticated,
                  data_required=data_required):
        @functools.wraps(function,
                         assigned=decorators.available_attrs(function))
        def _wrapped(self, request, *args, **kw):
            if authenticated and not request.user.is_authenticated():
                return JSONResponse('not logged in', 401)
            if not request.is_ajax():
                return JSONResponse('request must be AJAX', 400)

            # decode the JSON body if present
            request.DATA = None
            if request.body:
                try:
                    request.DATA = json.loads(request.body)
                except (TypeError, ValueError) as e:
                    return JSONResponse('malformed JSON request: %s' % e, 400)

            if data_required:
                if not request.DATA:
                    return JSONResponse('request requires JSON body', 400)

            # invoke the wrapped function, handling exceptions sanely
            try:
                data = function(self, request, *args, **kw)
                if isinstance(data, http.HttpResponse):
                    return data
                elif data is None:
                    return JSONResponse('', status=204)
                return JSONResponse(data, json_encoder=json_encoder)
            except http_errors as e:
                # exception was raised with a specific HTTP status
                if hasattr(e, 'http_status'):
                    http_status = e.http_status
                elif hasattr(e, 'code'):
                    http_status = e.code
                else:
                    log.exception('HTTP exception with no status/code')
                    return JSONResponse(str(e), 500)
                return JSONResponse(str(e), http_status)
            except Exception as e:
                log.exception('error invoking apiclient')
                return JSONResponse(str(e), 500)

        return _wrapped
    return decorator


def parse_filters_kwargs(request, client_keywords={}):
    """Extract REST filter parameters from the request GET args.

    Client processes some keywords separately from filters and takes
    them as separate inputs. This will ignore those keys to avoid
    potential conflicts.
    """
    filters = {}
    kwargs = {}
    for param in request.GET:
        if param in client_keywords:
            kwargs[param] = request.GET[param]
        else:
            filters[param] = request.GET[param]
    return filters, kwargs
