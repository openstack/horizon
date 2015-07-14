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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.defaultfilters import register  # noqa
from django.utils import html
from django.utils import safestring
import six.moves.urllib.parse as urlparse

from openstack_dashboard.api import swift

LOG = logging.getLogger(__name__)


resource_urls = {
    "AWS::AutoScaling::AutoScalingGroup": {
        'link': 'horizon:project:stacks:detail'},
    "AWS::CloudFormation::Stack": {
        'link': 'horizon:project:stacks:detail'},
    "AWS::EC2::Instance": {
        'link': 'horizon:project:instances:detail'},
    "AWS::EC2::InternetGateway": {
        'link': 'horizon:project:networks:ports:detail'},
    "AWS::EC2::NetworkInterface": {
        'link': 'horizon:project:networks:ports:detail'},
    "AWS::EC2::RouteTable": {
        'link': 'horizon:project:routers:detail'},
    "AWS::EC2::SecurityGroup": {
        'link': 'horizon:project:access_and_security:index'},
    "AWS::EC2::Subnet": {
        'link': 'horizon:project:networks:subnets:detail'},
    "AWS::EC2::Volume": {
        'link': 'horizon:project:volumes:volumes:detail'},
    "AWS::EC2::VPC": {
        'link': 'horizon:project:networks:detail'},
    "AWS::S3::Bucket": {
        'link': 'horizon:project:containers:index'},
    "OS::Cinder::Volume": {
        'link': 'horizon:project:volumes:volumes:detail'},
    "OS::Heat::AccessPolicy": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Heat::AutoScalingGroup": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Heat::CloudConfig": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Neutron::Firewall": {
        'link': 'horizon:project:firewalls:firewalldetails'},
    "OS::Neutron::FirewallPolicy": {
        'link': 'horizon:project:firewalls:policydetails'},
    "OS::Neutron::FirewallRule": {
        'link': 'horizon:project:firewalls:ruledetails'},
    "OS::Heat::HARestarter": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Heat::InstanceGroup": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Heat::MultipartMime": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Heat::ResourceGroup": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Heat::SoftwareConfig": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Heat::StructuredConfig": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Heat::StructuredDeployment": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Heat::Stack": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Heat::WaitCondition": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Heat::WaitConditionHandle": {
        'link': 'horizon:project:stacks:detail'},
    "OS::Neutron::HealthMonitor": {
        'link': 'horizon:project:loadbalancers:monitordetails'},
    "OS::Neutron::IKEPolicy": {
        'link': 'horizon:project:vpn:ikepolicydetails'},
    "OS::Neutron::IPsecPolicy": {
        'link': 'horizon:project:vpn:ipsecpolicydetails'},
    "OS::Neutron::IPsecSiteConnection": {
        'link': 'horizon:project:vpn:ipsecsiteconnectiondetails'},
    "OS::Neutron::Net": {
        'link': 'horizon:project:networks:detail'},
    "OS::Neutron::Pool": {
        'link': 'horizon:project:loadbalancers:pooldetails'},
    "OS::Neutron::PoolMember": {
        'link': 'horizon:project:loadbalancers:memberdetails'},
    "OS::Neutron::Port": {
        'link': 'horizon:project:networks:ports:detail'},
    "OS::Neutron::Router": {
        'link': 'horizon:project:routers:detail'},
    "OS::Neutron::Subnet": {
        'link': 'horizon:project:networks:subnets:detail'},
    "OS::Neutron::VPNService": {
        'link': 'horizon:project:vpn:vpnservicedetails'},
    "OS::Nova::KeyPair": {
        'link': 'horizon:project:access_and_security:index'},
    "OS::Nova::Server": {
        'link': 'horizon:project:instances:detail'},
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


static_url = getattr(settings, "STATIC_URL", "/static/")
resource_images = {
    'LB_FAILED': static_url + 'dashboard/img/lb-red.svg',
    'LB_DELETE': static_url + 'dashboard/img/lb-red.svg',
    'LB_IN_PROGRESS': static_url + 'dashboard/img/lb-gray.gif',
    'LB_INIT': static_url + 'dashboard/img/lb-gray.svg',
    'LB_COMPLETE': static_url + 'dashboard/img/lb-green.svg',
    'DB_FAILED': static_url + 'dashboard/img/db-red.svg',
    'DB_DELETE': static_url + 'dashboard/img/db-red.svg',
    'DB_IN_PROGRESS': static_url + 'dashboard/img/db-gray.gif',
    'DB_INIT': static_url + 'dashboard/img/db-gray.svg',
    'DB_COMPLETE': static_url + 'dashboard/img/db-green.svg',
    'STACK_FAILED': static_url + 'dashboard/img/stack-red.svg',
    'STACK_DELETE': static_url + 'dashboard/img/stack-red.svg',
    'STACK_IN_PROGRESS': static_url + 'dashboard/img/stack-gray.gif',
    'STACK_INIT': static_url + 'dashboard/img/stack-gray.svg',
    'STACK_COMPLETE': static_url + 'dashboard/img/stack-green.svg',
    'SERVER_FAILED': static_url + 'dashboard/img/server-red.svg',
    'SERVER_DELETE': static_url + 'dashboard/img/server-red.svg',
    'SERVER_IN_PROGRESS': static_url + 'dashboard/img/server-gray.gif',
    'SERVER_INIT': static_url + 'dashboard/img/server-gray.svg',
    'SERVER_COMPLETE': static_url + 'dashboard/img/server-green.svg',
    'UNKNOWN_FAILED': static_url + 'dashboard/img/unknown-red.svg',
    'UNKNOWN_DELETE': static_url + 'dashboard/img/unknown-red.svg',
    'UNKNOWN_IN_PROGRESS': static_url + 'dashboard/img/unknown-gray.gif',
    'UNKNOWN_INIT': static_url + 'dashboard/img/unknown-gray.svg',
    'UNKNOWN_COMPLETE': static_url + 'dashboard/img/unknown-green.svg',
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
