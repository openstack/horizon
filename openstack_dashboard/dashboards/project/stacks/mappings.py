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

import json
import logging
import re

from django.core.urlresolvers import reverse
from django.template.defaultfilters import register  # noqa
from django.utils import html
from django.utils import safestring
import six.moves.urllib.parse as urlparse

from openstack_dashboard.api import swift

LOG = logging.getLogger(__name__)


resource_urls = {
    "AWS::EC2::Instance": {
        'link': 'horizon:project:instances:detail'},
    "AWS::EC2::NetworkInterface": {
        'link': 'horizon:project:networks:ports:detail'},
    "AWS::EC2::RouteTable": {
        'link': 'horizon:project:routers:detail'},
    "AWS::EC2::Subnet": {
        'link': 'horizon:project:networks:subnets:detail'},
    "AWS::EC2::Volume": {
        'link': 'horizon:project:volumes:volumes:detail'},
    "AWS::EC2::VPC": {
        'link': 'horizon:project:networks:detail'},
    "AWS::S3::Bucket": {
        'link': 'horizon:project:containers:index'},
    "OS::Quantum::Net": {
        'link': 'horizon:project:networks:detail'},
    "OS::Quantum::Port": {
        'link': 'horizon:project:networks:ports:detail'},
    "OS::Quantum::Router": {
        'link': 'horizon:project:routers:detail'},
    "OS::Quantum::Subnet": {
        'link': 'horizon:project:networks:subnets:detail'},
    "OS::Swift::Container": {
        'link': 'horizon:project:containers:index',
        'format_pattern': '%s' + swift.FOLDER_DELIMITER},
}


def resource_to_url(resource):
    if not resource or not resource.physical_resource_id:
        return None

    mapping = resource_urls.get(resource.resource_type, {})
    try:
        if 'link' not in mapping:
            return None
        format_pattern = mapping.get('format_pattern') or '%s'
        rid = format_pattern % resource.physical_resource_id
        url = reverse(mapping['link'], args=(rid,))
    except Exception as e:
        LOG.exception(e)
        return None
    return url


@register.filter
def stack_output(output):
    if not output:
        return u''
    if isinstance(output, dict) or isinstance(output, list):
        json_string = json.dumps(output, indent=2)
        safe_output = u'<pre>%s</pre>' % html.escape(json_string)
        return safestring.mark_safe(safe_output)
    if isinstance(output, basestring):
        parts = urlparse.urlsplit(output)
        if parts.netloc and parts.scheme in ('http', 'https'):
            url = html.escape(output)
            safe_link = u'<a href="%s" target="_blank">%s</a>' % (url, url)
            return safestring.mark_safe(safe_link)
    return unicode(output)


resource_images = {
    'LB_FAILED': '/static/dashboard/img/lb-red.svg',
    'LB_DELETE': '/static/dashboard/img/lb-red.svg',
    'LB_IN_PROGRESS': '/static/dashboard/img/lb-gray.gif',
    'LB_INIT': '/static/dashboard/img/lb-gray.svg',
    'LB_COMPLETE': '/static/dashboard/img/lb-green.svg',
    'DB_FAILED': '/static/dashboard/img/db-red.svg',
    'DB_DELETE': '/static/dashboard/img/db-red.svg',
    'DB_IN_PROGRESS': '/static/dashboard/img/db-gray.gif',
    'DB_INIT': '/static/dashboard/img/db-gray.svg',
    'DB_COMPLETE': '/static/dashboard/img/db-green.svg',
    'STACK_FAILED': '/static/dashboard/img/stack-red.svg',
    'STACK_DELETE': '/static/dashboard/img/stack-red.svg',
    'STACK_IN_PROGRESS': '/static/dashboard/img/stack-gray.gif',
    'STACK_INIT': '/static/dashboard/img/stack-gray.svg',
    'STACK_COMPLETE': '/static/dashboard/img/stack-green.svg',
    'SERVER_FAILED': '/static/dashboard/img/server-red.svg',
    'SERVER_DELETE': '/static/dashboard/img/server-red.svg',
    'SERVER_IN_PROGRESS': '/static/dashboard/img/server-gray.gif',
    'SERVER_INIT': '/static/dashboard/img/server-gray.svg',
    'SERVER_COMPLETE': '/static/dashboard/img/server-green.svg',
    'UNKNOWN_FAILED': '/static/dashboard/img/unknown-red.svg',
    'UNKNOWN_DELETE': '/static/dashboard/img/unknown-red.svg',
    'UNKNOWN_IN_PROGRESS': '/static/dashboard/img/unknown-gray.gif',
    'UNKNOWN_INIT': '/static/dashboard/img/unknown-gray.svg',
    'UNKNOWN_COMPLETE': '/static/dashboard/img/unknown-green.svg',
}


def get_resource_type(type):
    if re.search('LoadBalancer', type):
        return 'LB'
    elif re.search('DBInstance', type) or re.search('Database', type):
        return 'DB'
    elif re.search('Instance', type) or re.search('Server', type):
        return 'SERVER'
    elif re.search('stack', type):
        return 'STACK'
    else:
        return 'UNKNOWN'


def get_resource_status(status):
    if re.search('IN_PROGRESS', status):
        return 'IN_PROGRESS'
    elif re.search('FAILED', status):
        return 'FAILED'
    elif re.search('DELETE', status):
        return 'DELETE'
    elif re.search('INIT', status):
        return 'INIT'
    else:
        return 'COMPLETE'


def get_resource_image(status, type):
    """Sets the image url and in_progress action sw based on status."""
    resource_type = get_resource_type(type)
    resource_status = get_resource_status(status)
    resource_state = resource_type + "_" + resource_status

    for key in resource_images:
        if key == resource_state:
            return resource_images.get(key)
