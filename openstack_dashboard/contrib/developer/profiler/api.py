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

from osprofiler import _utils as utils
from osprofiler.drivers.base import get_driver as profiler_get_driver
from osprofiler import notifier
from osprofiler import profiler
from osprofiler import web

from horizon.utils import settings as horizon_settings


ROOT_HEADER = 'PARENT_VIEW_TRACE_ID'


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


def _get_engine():
    connection_str = horizon_settings.get_dict_config(
        'OPENSTACK_PROFILER', 'receiver_connection_string')
    return profiler_get_driver(connection_str)


def list_traces():
    engine = _get_engine()
    fields = ['base_id', 'timestamp', 'info.request.path', 'info']
    traces = engine.list_traces(fields)
    return [{'id': trace['base_id'],
             'timestamp': trace['timestamp'],
             'origin': trace['info']['request']['path']} for trace in traces]


def get_trace(trace_id):
    def rec(_data, level=0):
        _data['level'] = level
        _data['is_leaf'] = not _data['children']
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

    engine = _get_engine()
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
    trace_data = [key.decode() if isinstance(key, bytes)
                  else key for key in trace_data]
    return json.dumps({web.X_TRACE_INFO: trace_data[0],
                       web.X_TRACE_HMAC: trace_data[1]})


if not horizon_settings.get_dict_config('OPENSTACK_PROFILER', 'enabled'):
    def trace(function):
        return function
else:
    def trace(function):
        func_name = function.__module__ + '.' + function.__name__
        decorator = profiler.trace(func_name)
        return decorator(function)
