# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from django.conf import settings
from heatclient import client as heat_client
from horizon.utils import functions as utils
from openstack_dashboard.api import base

LOG = logging.getLogger(__name__)


def format_parameters(params):
    parameters = {}
    for count, p in enumerate(params, 1):
        parameters['Parameters.member.%d.ParameterKey' % count] = p
        parameters['Parameters.member.%d.ParameterValue' % count] = params[p]
    return parameters


def heatclient(request, password=None):
    api_version = "1"
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    endpoint = base.url_for(request, 'orchestration')
    LOG.debug('heatclient connection created using token "%s" and url "%s"' %
              (request.user.token.id, endpoint))
    kwargs = {
        'token': request.user.token.id,
        'insecure': insecure,
        'ca_file': cacert,
        'username': request.user.username,
        'password': password
        #'timeout': args.timeout,
        #'ca_file': args.ca_file,
        #'cert_file': args.cert_file,
        #'key_file': args.key_file,
    }
    client = heat_client.Client(api_version, endpoint, **kwargs)
    client.format_parameters = format_parameters
    return client


def stacks_list(request, marker=None, paginate=False):
    limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
    page_size = utils.get_page_size(request)

    if paginate:
        request_size = page_size + 1
    else:
        request_size = limit

    kwargs = {}
    if marker:
        kwargs['marker'] = marker

    stacks_iter = heatclient(request).stacks.list(limit=request_size,
                                                  **kwargs)

    has_more_data = False
    stacks = list(stacks_iter)
    if paginate:
        if len(stacks) > page_size:
            stacks.pop()
            has_more_data = True
    return (stacks, has_more_data)


def stack_delete(request, stack_id):
    return heatclient(request).stacks.delete(stack_id)


def stack_get(request, stack_id):
    return heatclient(request).stacks.get(stack_id)


def template_get(request, stack_id):
    return heatclient(request).stacks.template(stack_id)


def stack_create(request, password=None, **kwargs):
    return heatclient(request, password).stacks.create(**kwargs)


def stack_update(request, stack_id, **kwargs):
    if kwargs.get('password'):
        kwargs.pop('password')
    return heatclient(request).stacks.update(stack_id, **kwargs)


def events_list(request, stack_name):
    return heatclient(request).events.list(stack_name)


def resources_list(request, stack_name):
    return heatclient(request).resources.list(stack_name)


def resource_get(request, stack_id, resource_name):
    return heatclient(request).resources.get(stack_id, resource_name)


def resource_metadata_get(request, stack_id, resource_name):
    return heatclient(request).resources.metadata(stack_id, resource_name)


def template_validate(request, **kwargs):
    return heatclient(request).stacks.validate(**kwargs)
