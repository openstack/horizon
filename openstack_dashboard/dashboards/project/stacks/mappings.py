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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.defaultfilters import register  # noqa
from django.utils import html
from django.utils import safestring
import six
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
    if (not resource or
            not resource.physical_resource_id or
            not hasattr(resource, 'resource_type')):
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
    if isinstance(output, six.string_types):
        parts = urlparse.urlsplit(output)
        if parts.netloc and parts.scheme in ('http', 'https'):
            url = html.escape(output)
            safe_link = u'<a href="%s" target="_blank">%s</a>' % (url, url)
            return safestring.mark_safe(safe_link)
    if isinstance(output, dict) or isinstance(output, list):
        output = json.dumps(output, indent=2)
    return safestring.mark_safe(u'<pre>%s</pre>' % html.escape(output))

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
    'ALARM_FAILED': static_url + 'dashboard/img/alarm-red.svg',
    'ALARM_DELETE': static_url + 'dashboard/img/alarm-red.svg',
    'ALARM_IN_PROGRESS': static_url + 'dashboard/img/alarm-gray.gif',
    'ALARM_INIT': static_url + 'dashboard/img/alarm-gray.svg',
    'ALARM_COMPLETE': static_url + 'dashboard/img/alarm-green.svg',
    'VOLUME_FAILED': static_url + 'dashboard/img/volume-red.svg',
    'VOLUME_DELETE': static_url + 'dashboard/img/volume-red.svg',
    'VOLUME_IN_PROGRESS': static_url + 'dashboard/img/volume-gray.gif',
    'VOLUME_INIT': static_url + 'dashboard/img/volume-gray.svg',
    'VOLUME_COMPLETE': static_url + 'dashboard/img/volume-green.svg',
    'IMAGE_FAILED': static_url + 'dashboard/img/image-red.svg',
    'IMAGE_DELETE': static_url + 'dashboard/img/image-red.svg',
    'IMAGE_IN_PROGRESS': static_url + 'dashboard/img/image-gray.gif',
    'IMAGE_INIT': static_url + 'dashboard/img/image-gray.svg',
    'IMAGE_COMPLETE': static_url + 'dashboard/img/image-green.svg',
    'WAIT_FAILED': static_url + 'dashboard/img/wait-red.svg',
    'WAIT_DELETE': static_url + 'dashboard/img/wait-red.svg',
    'WAIT_IN_PROGRESS': static_url + 'dashboard/img/wait-gray.gif',
    'WAIT_INIT': static_url + 'dashboard/img/wait-gray.svg',
    'WAIT_COMPLETE': static_url + 'dashboard/img/wait-green.svg',
    'FIREWALL_FAILED': static_url + 'dashboard/img/firewall-red.svg',
    'FIREWALL_DELETE': static_url + 'dashboard/img/firewall-red.svg',
    'FIREWALL_IN_PROGRESS': static_url + 'dashboard/img/firewall-gray.gif',
    'FIREWALL_INIT': static_url + 'dashboard/img/firewall-gray.svg',
    'FIREWALL_COMPLETE': static_url + 'dashboard/img/firewall-green.svg',
    'FLOATINGIP_FAILED': static_url + 'dashboard/img/floatingip-red.svg',
    'FLOATINGIP_DELETE': static_url + 'dashboard/img/floatingip-red.svg',
    'FLOATINGIP_IN_PROGRESS': static_url + 'dashboard/img/floatingip-gray.gif',
    'FLOATINGIP_INIT': static_url + 'dashboard/img/floatingip-gray.svg',
    'FLOATINGIP_COMPLETE': static_url + 'dashboard/img/floatingip-green.svg',
    'ROUTER_FAILED': static_url + 'dashboard/img/router-red.svg',
    'ROUTER_DELETE': static_url + 'dashboard/img/router-red.svg',
    'ROUTER_IN_PROGRESS': static_url + 'dashboard/img/router-gray.gif',
    'ROUTER_INIT': static_url + 'dashboard/img/router-gray.svg',
    'ROUTER_COMPLETE': static_url + 'dashboard/img/router-green.svg',
    'POLICY_FAILED': static_url + 'dashboard/img/policy-red.svg',
    'POLICY_DELETE': static_url + 'dashboard/img/policy-red.svg',
    'POLICY_IN_PROGRESS': static_url + 'dashboard/img/policy-gray.gif',
    'POLICY_INIT': static_url + 'dashboard/img/policy-gray.svg',
    'POLICY_COMPLETE': static_url + 'dashboard/img/policy-green.svg',
    'CONFIG_FAILED': static_url + 'dashboard/img/config-red.svg',
    'CONFIG_DELETE': static_url + 'dashboard/img/config-red.svg',
    'CONFIG_IN_PROGRESS': static_url + 'dashboard/img/config-gray.gif',
    'CONFIG_INIT': static_url + 'dashboard/img/config-gray.svg',
    'CONFIG_COMPLETE': static_url + 'dashboard/img/config-green.svg',
    'NETWORK_FAILED': static_url + 'dashboard/img/network-red.svg',
    'NETWORK_DELETE': static_url + 'dashboard/img/network-red.svg',
    'NETWORK_IN_PROGRESS': static_url + 'dashboard/img/network-gray.gif',
    'NETWORK_INIT': static_url + 'dashboard/img/network-gray.svg',
    'NETWORK_COMPLETE': static_url + 'dashboard/img/network-green.svg',
    'PORT_FAILED': static_url + 'dashboard/img/port-red.svg',
    'PORT_DELETE': static_url + 'dashboard/img/port-red.svg',
    'PORT_IN_PROGRESS': static_url + 'dashboard/img/port-gray.gif',
    'PORT_INIT': static_url + 'dashboard/img/port-gray.svg',
    'PORT_COMPLETE': static_url + 'dashboard/img/port-green.svg',
    'SECURITYGROUP_FAILED': static_url + 'dashboard/img/securitygroup-red.svg',
    'SECURITYGROUP_DELETE': static_url + 'dashboard/img/securitygroup-red.svg',
    'SECURITYGROUP_IN_PROGRESS':
        static_url + 'dashboard/img/securitygroup-gray.gif',
    'SECURITYGROUP_INIT': static_url + 'dashboard/img/securitygroup-gray.svg',
    'SECURITYGROUP_COMPLETE':
        static_url + 'dashboard/img/securitygroup-green.svg',
    'VPN_FAILED': static_url + 'dashboard/img/vpn-red.svg',
    'VPN_DELETE': static_url + 'dashboard/img/vpn-red.svg',
    'VPN_IN_PROGRESS': static_url + 'dashboard/img/vpn-gray.gif',
    'VPN_INIT': static_url + 'dashboard/img/vpn-gray.svg',
    'VPN_COMPLETE': static_url + 'dashboard/img/vpn-green.svg',
    'FLAVOR_FAILED': static_url + 'dashboard/img/flavor-red.svg',
    'FLAVOR_DELETE': static_url + 'dashboard/img/flavor-red.svg',
    'FLAVOR_IN_PROGRESS': static_url + 'dashboard/img/flavor-gray.gif',
    'FLAVOR_INIT': static_url + 'dashboard/img/flavor-gray.svg',
    'FLAVOR_COMPLETE': static_url + 'dashboard/img/flavor-green.svg',
    'KEYPAIR_FAILED': static_url + 'dashboard/img/keypair-red.svg',
    'KEYPAIR_DELETE': static_url + 'dashboard/img/keypair-red.svg',
    'KEYPAIR_IN_PROGRESS': static_url + 'dashboard/img/keypair-gray.gif',
    'KEYPAIR_INIT': static_url + 'dashboard/img/keypair-gray.svg',
    'KEYPAIR_COMPLETE': static_url + 'dashboard/img/keypair-green.svg',
    'UNKNOWN_FAILED': static_url + 'dashboard/img/unknown-red.svg',
    'UNKNOWN_DELETE': static_url + 'dashboard/img/unknown-red.svg',
    'UNKNOWN_IN_PROGRESS': static_url + 'dashboard/img/unknown-gray.gif',
    'UNKNOWN_INIT': static_url + 'dashboard/img/unknown-gray.svg',
    'UNKNOWN_COMPLETE': static_url + 'dashboard/img/unknown-green.svg',
}


resource_types = {
    # LB
    'LoadBalance': 'LB',
    'HealthMonitor': 'LB',
    'PoolMember': 'LB',
    'Pool': 'LB',
    # DB
    'DBInstance': 'DB',
    'Database': 'DB',
    # SERVER
    'Instance': 'SERVER',
    'Server': 'SERVER',
    # ALARM
    'Alarm': 'ALARM',
    'CombinationAlarm': 'ALARM',
    'CWLiteAlarm': 'ALARM',
    # VOLUME
    'Volume': 'VOLUME',
    'VolumeAttachment': 'VOLUME',
    # STACK
    'stack': 'STACK',
    'AutoScalingGroup': 'STACK',
    'InstanceGroup': 'STACK',
    'ServerGroup': 'STACK',
    'ResourceGroup': 'STACK',
    # IMAGE
    'Image': 'IMAGE',
    # WAIT
    'WaitCondition': 'WAIT',
    'WaitConditionHandle': 'WAIT',
    'UpdateWaitConditionHandle': 'WAIT',
    # FIREWALL
    'Firewall': 'FIREWALL',
    'FirewallPolicy': 'FIREWALL',
    'FirewallRule': 'FIREWALL',
    # FLOATINGIP
    'FloatingIP': 'FLOATINGIP',
    'FloatingIPAssociation': 'FLOATINGIP',
    # ROUTER
    'Router': 'ROUTER',
    'RouterGateway': 'ROUTER',
    'RouterInterface': 'ROUTER',
    # POLICY
    'ScalingPolicy': 'POLICY',
    # CONFIG
    'CloudConfig': 'CONFIG',
    'MultipartMime': 'CONFIG',
    'SoftwareConfig': 'CONFIG',
    'SoftwareDeployment': 'CONFIG',
    'StructuredConfig': 'CONFIG',
    'StructuredDeployment': 'CONFIG',
    # NETWORK
    'Net': 'NETWORK',
    'Subnet': 'NETWORK',
    'NetworkGateway': 'NETWORK',
    'ProviderNet': 'NETWORK',
    # PORT
    'Port': 'PORT',
    # SECURITYGROUP
    'SecurityGroup': 'SECURITYGROUP',
    # VPN
    'VPNService': 'VPN',
    # FLAVOR
    'Flavor': 'FLAVOR',
    # KEYPAIR
    'KeyPair': 'KEYPAIR',
}


def get_resource_type(type):
    for key, value in six.iteritems(resource_types):
        if key in type:
            return value

    return 'UNKNOWN'


def get_resource_status(status):
    if ('IN_PROGRESS' in status):
        return 'IN_PROGRESS'
    elif ('FAILED' in status):
        return 'FAILED'
    elif ('DELETE' in status):
        return 'DELETE'
    elif ('INIT' in status):
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
