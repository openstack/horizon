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

import contextlib
import json

from django.conf import settings
from osprofiler import _utils as utils
from osprofiler.drivers.base import get_driver as profiler_get_driver
from osprofiler import notifier
from osprofiler import profiler
from osprofiler import web
from six.moves.urllib.parse import urlparse


ROOT_HEADER = 'PARENT_VIEW_TRACE_ID'
PROFILER_SETTINGS = getattr(settings, 'OPENSTACK_PROFILER', {})


def init_notifier(connection_str, host="localhost"):
    _notifier = notifier.create(
        connection_str, project='horizon', service='horizon', host=host)
    notifier.set(_notifier)


@contextlib.contextmanager
def traced(request, name, info=None):
    if info is None:
        info = {}
    profiler_instance = profiler.get()
    if profiler_instance is not None:
        trace_id = profiler_instance.get_base_id()
        info['user_id'] = request.user.id
        with profiler.Trace(name, info=info):
            yield trace_id
    else:
        yield


def _get_engine_kwargs(request, connection_str):
    from openstack_dashboard.api import base
    engines_kwargs = {
        # NOTE(tsufiev): actually Horizon doesn't use ceilometer backend (too
        # slow for UI), but since osprofiler still supports it (due to API
        # deprecation cycle limitations), Horizon also should support this
        # option
        'ceilometer': lambda req: {
            'endpoint': base.url_for(req, 'metering'),
            'insecure': getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False),
            'cacert': getattr(settings, 'OPENSTACK_SSL_CACERT', None),
            'token': (lambda: req.user.token.id),
            'ceilometer_api_version': '2'
        }
    }

    engine = urlparse(connection_str).scheme
    return engines_kwargs.get(engine, lambda req: {})(request)


def _get_engine(request):
    connection_str = PROFILER_SETTINGS.get(
        'receiver_connection_string', "mongodb://")
    kwargs = _get_engine_kwargs(request, connection_str)
    return profiler_get_driver(connection_str, **kwargs)


def list_traces(request):
    engine = _get_engine(request)
    query = {"info.user_id": request.user.id}
    fields = ['base_id', 'timestamp', 'info.request.path']
    traces = engine.list_traces(query, fields)
    return [{'id': trace['base_id'],
             'timestamp': trace['timestamp'],
             'origin': trace['info']['request']['path']} for trace in traces]


def get_trace(request, trace_id):
    def rec(_data, level=0):
        _data['level'] = level
        _data['is_leaf'] = not len(_data['children'])
        _data['visible'] = True
        _data['childrenVisible'] = True
        finished = _data['info']['finished']
        for child in _data['children']:
            __, child_finished = rec(child, level + 1)
            # NOTE(tsufiev): in case of async requests the root request usually
            # finishes before the dependent requests do so, to we need to
            # normalize the duration of all requests by the finishing time of
            # the one which took longest
            if child_finished > finished:
                finished = child_finished
        return _data, finished

    engine = _get_engine(request)
    trace = engine.get_report(trace_id)
    data, max_finished = rec(trace)
    data['info']['max_finished'] = max_finished
    return data


def update_trace_headers(keys, **kwargs):
    trace_headers = web.get_trace_id_headers()
    trace_info = utils.signed_unpack(
        trace_headers[web.X_TRACE_INFO], trace_headers[web.X_TRACE_HMAC],
        keys)
    trace_info.update(kwargs)
    p = profiler.get()
    trace_data = utils.signed_pack(trace_info, p.hmac_key)
    return json.dumps({web.X_TRACE_INFO: trace_data[0],
                       web.X_TRACE_HMAC: trace_data[1]})


if not PROFILER_SETTINGS.get('enabled', False):
    def trace(function):
        return function
else:
    def trace(function):
        func_name = function.__module__ + '.' + function.__name__
        decorator = profiler.trace(func_name)
        return decorator(function)
