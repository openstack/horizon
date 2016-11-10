# Copyright 2016 Mirantis Inc.
# All Rights Reserved.
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

from django.conf import settings
from django.core import exceptions
from django.core.urlresolvers import reverse
from django.utils import safestring
from django.utils.translation import ugettext_lazy as _
from osprofiler import _utils as profiler_utils
from osprofiler import profiler
from osprofiler import web
import six

from horizon import messages
from openstack_dashboard.contrib.developer.profiler import api

_REQUIRED_KEYS = ("base_id", "hmac_key")
_OPTIONAL_KEYS = ("parent_id",)

PROFILER_SETTINGS = getattr(settings, 'OPENSTACK_PROFILER', {})


class ProfilerClientMiddleware(object):
    def process_request(self, request):
        if 'profile_page' in request.COOKIES:
            hmac_key = PROFILER_SETTINGS.get('keys')[0]
            profiler.init(hmac_key)
            for hdr_key, hdr_value in web.get_trace_id_headers().items():
                request.META[hdr_key] = hdr_value
        return None


class ProfilerMiddleware(object):
    def __init__(self):
        self.name = PROFILER_SETTINGS.get('facility_name', 'horizon')
        self.hmac_keys = PROFILER_SETTINGS.get('keys')
        self._enabled = PROFILER_SETTINGS.get('enabled', False)
        if self._enabled:
            api.init_notifier(PROFILER_SETTINGS.get(
                'notifier_connection_string', 'mongodb://'))
        else:
            raise exceptions.MiddlewareNotUsed()

    @staticmethod
    def is_authenticated(request):
        return hasattr(request, "user") and request.user.is_authenticated()

    def is_enabled(self, request):
        return self.is_authenticated(request) and settings.DEBUG

    @staticmethod
    def _trace_is_valid(trace_info):
        if not isinstance(trace_info, dict):
            return False
        trace_keys = set(six.iterkeys(trace_info))
        if not all(k in trace_keys for k in _REQUIRED_KEYS):
            return False
        if trace_keys.difference(_REQUIRED_KEYS + _OPTIONAL_KEYS):
            return False
        return True

    def process_view(self, request, view_func, view_args, view_kwargs):
        # do not profile ajax requests for now
        if not self.is_enabled(request) or request.is_ajax():
            return None

        trace_info = profiler_utils.signed_unpack(
            request.META.get('X-Trace-Info'),
            request.META.get('X-Trace-HMAC'),
            self.hmac_keys)

        if not self._trace_is_valid(trace_info):
            return None

        profiler.init(**trace_info)
        info = {
            'request': {
                'path': request.path,
                'query': request.GET.urlencode(),
                'method': request.method,
                'scheme': request.scheme
            }
        }
        with api.traced(request, view_func.__name__, info) as trace_id:
            response = view_func(request, *view_args, **view_kwargs)
            url = reverse('horizon:developer:profiler:index')
            message = safestring.mark_safe(
                _('Traced with id %(id)s. Go to <a href="%(url)s">page</a>') %
                {'id': trace_id, 'url': url})
            messages.info(request, message)
            return response

    @staticmethod
    def clear_profiling_cookies(request, response):
        """Expire any cookie that initiated profiling request."""
        if 'profile_page' in request.COOKIES:
            path = request.path[:-1]
            response.set_cookie('profile_page', max_age=0, path=path)

    def process_response(self, request, response):
        self.clear_profiling_cookies(request, response)
        # do not profile ajax requests for now
        if not self.is_enabled(request) or request.is_ajax():
            return response

        return response
