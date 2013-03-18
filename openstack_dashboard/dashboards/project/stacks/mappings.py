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

import json
import logging
import urlparse

from django.core.urlresolvers import reverse
from django.template.defaultfilters import register

from openstack_dashboard.api.swift import FOLDER_DELIMITER

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
        'link': 'horizon:project:volumes:detail'},
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
        'format_pattern': '%s' + FOLDER_DELIMITER},
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
        return u'<pre>%s</pre>' % json.dumps(output, indent=2)
    if isinstance(output, basestring):
        parts = urlparse.urlsplit(output)
        if parts.netloc and parts.scheme in ('http', 'https'):
            return u'<a href="%s" target="_blank">%s</a>' % (output, output)
    return unicode(output)
