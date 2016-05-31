# Copyright 2016 NEC Corporation.
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
import logging

from django.conf import settings
from django.contrib import messages as django_messages
from django.core.exceptions import MiddlewareNotUsed

import six.moves.urllib.parse as urlparse

LOG = logging.getLogger(__name__)


class OperationLogMiddleware(object):
    """Middleware to output operation log.

    This log can includes information below.
      <domain name>, <domain id>
      <project name>, <project id>
      <user name>, <user id>
      <request scheme>, <referer url>, <request url>
      <message>, <method>, <http status>
      <request parameters>
    And log format is defined OPERATION_LOG_OPTIONS.
    """

    @property
    def OPERATION_LOG(self):
        # In order to allow to access from mock in test cases.
        return self._logger

    def __init__(self):
        if not getattr(settings, "OPERATION_LOG_ENABLED", False):
            raise MiddlewareNotUsed

        # set configurations
        _log_option = getattr(settings, "OPERATION_LOG_OPTIONS", {})
        _available_methods = ['POST', 'GET', 'PUT', 'DELETE']
        _methods = _log_option.get("target_methods", ['POST'])
        _default_format = (
            "[%(domain_name)s] [%(domain_id)s] [%(project_name)s]"
            " [%(project_id)s] [%(user_name)s] [%(user_id)s]"
            " [%(request_scheme)s] [%(referer_url)s] [%(request_url)s]"
            " [%(message)s] [%(method)s] [%(http_status)s] [%(param)s]")
        self.target_methods = [x for x in _methods if x in _available_methods]
        self.mask_fields = getattr(_log_option, "mask_fields", ['password'])
        self.format = getattr(_log_option, "format", _default_format)
        self.static_rule = ['/js/', '/static/']
        self._logger = logging.getLogger('horizon.operation_log')

    def process_response(self, request, response):
        """Log user operation."""
        log_format = self._get_log_format(request)
        if not log_format:
            return response

        params = self._get_parameters_from_request(request)
        # log a message displayed to user
        messages = django_messages.get_messages(request)
        result_message = None
        if messages:
            result_message = ', '.join('%s: %s' % (message.tags, message)
                                       for message in messages)
        elif 'action' in request.POST:
            result_message = request.POST['action']
        params['message'] = result_message
        params['http_status'] = response.status_code

        self.OPERATION_LOG.info(log_format, params)

        return response

    def process_exception(self, request, exception):
        """Log error info when exception occured."""
        log_format = self._get_log_format(request)
        if log_format is None:
            return

        params = self._get_parameters_from_request(request, True)
        params['message'] = exception
        params['http_status'] = '-'

        self.OPERATION_LOG.info(log_format, params)

    def _get_log_format(self, request):
        """Return operation log format."""
        if not (hasattr(request, 'user') and
                request.user.is_authenticated()):
            return
        method = request.method.upper()
        if not (method in self.target_methods):
            return
        if method == 'GET':
            request_url = urlparse.unquote(request.path)
            for rule in self.static_rule:
                if rule in request_url:
                    return
        return self.format

    def _get_parameters_from_request(self, request, exception=False):
        """Get parameters to log in OPERATION_LOG."""
        user = request.user
        referer_url = None
        try:
            referer_dic = urlparse.urlsplit(
                urlparse.unquote(request.META.get('HTTP_REFERER')))
            referer_url = referer_dic[2]
            if referer_dic[3]:
                referer_url += "?" + referer_dic[3]
            if isinstance(referer_url, str):
                referer_url = referer_url.decode('utf-8')
        except Exception:
            pass
        return {
            'domain_name': getattr(user, 'domain_name', None),
            'domain_id': getattr(user, 'domain_id', None),
            'project_name': getattr(user, 'project_name', None),
            'project_id': getattr(user, 'project_id', None),
            'user_name': getattr(user, 'username', None),
            'user_id': request.session.get('user_id', None),
            'request_scheme': request.scheme,
            'referer_url': referer_url,
            'request_url': urlparse.unquote(request.path),
            'method': request.method if not exception else None,
            'param': self._get_request_param(request),
        }

    def _get_request_param(self, request):
        """Change POST data to JSON string and mask data."""
        params = {}
        try:
            params = request.POST.copy()
            if not params:
                params = json.loads(request.body)
        except Exception:
            pass
        for key in params.items():
            # replace a value to a masked characters
            for key in self.mask_fields:
                params[key] = '*' * 8

        # when a file uploaded (E.g create image)
        files = request.FILES.values()
        if len(list(files)) > 0:
            filenames = ', '.join(
                [up_file.name for up_file in files])
            params['file_name'] = filenames

        return json.dumps(params, ensure_ascii=False)
