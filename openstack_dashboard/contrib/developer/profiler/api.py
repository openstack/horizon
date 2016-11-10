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

from django.conf import settings
from osprofiler.drivers.base import get_driver as profiler_get_driver
from osprofiler import notifier
from osprofiler import profiler
from six.moves.urllib.parse import urlparse


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
        for child in _data['children']:
            rec(child, level + 1)
        return _data

    engine = _get_engine(request)
    trace = engine.get_report(trace_id)
    # throw away toplevel node which is dummy and doesn't contain any info,
    # use its first and only child as the toplevel node
    return rec(trace['children'][0])
