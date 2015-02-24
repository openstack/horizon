#
#    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API over the neutron service.
"""

from django.views import generic

from openstack_dashboard import api
from openstack_dashboard.api.rest import utils as rest_utils

from openstack_dashboard.api.rest import urls


@urls.register
class Networks(generic.View):
    """API for Neutron Networks
    http://developer.openstack.org/api-ref-networking-v2.html
    """
    url_regex = r'neutron/networks/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of networks for a project

        The listing result is an object with property "items".  Each item is
        a network.
        """
        tenant_id = request.user.tenant_id
        result = api.neutron.network_list_for_tenant(request, tenant_id)
        return{'items': [n.to_dict() for n in result]}

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        """Create a network
        :param  admin_state_up (optional): The administrative state of the
                network, which is up (true) or down (false).
        :param name (optional): The network name. A request body is optional:
                If you include it, it can specify this optional attribute.
        :param net_profile_id (optional): network profile id
        :param shared (optional): Indicates whether this network is shared
                across all tenants. By default, only administrative users can
                change this value.
        :param tenant_id (optional): Admin-only. The UUID of the tenant that
                will own the network. This tenant can be different from the
                tenant that makes the create network request. However, only
                administrative users can specify a tenant ID other than their
                own. You cannot change this value through authorization
                policies.

         :return: JSON representation of a Network
         """
        if not api.neutron.is_port_profiles_supported():
            request.DATA.pop("net_profile_id", None)
        new_network = api.neutron.network_create(request, **request.DATA)
        return rest_utils.CreatedResponse(
            '/api/neutron/networks/%s' % new_network.id,
            new_network.to_dict()
        )


@urls.register
class Subnets(generic.View):
    """API for Neutron SubNets
    http://developer.openstack.org/api-ref-networking-v2.html#subnets
    """
    url_regex = r'neutron/subnets/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of subnets for a project

        The listing result is an object with property "items".  Each item is
        a subnet.

        """
        result = api.neutron.subnet_list(request, **request.GET)
        return{'items': [n.to_dict() for n in result]}

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        """Create a Subnet for a given Network

        :param name (optional):  The subnet name.
        :param network_id: The ID of the attached network.
        :param tenant_id (optional): The ID of the tenant who owns the network.
                Only administrative users can specify a tenant ID other than
                their own.
        :param allocation_pools (optional): The start and end addresses for the
                allocation pools.
        :param gateway_ip (optional): The gateway IP address.
        :param ip_version: The IP version, which is 4 or 6.
        :param cidr: The CIDR.
        :param id (optional): The ID of the subnet.
        :param enable_dhcp (optional): Set to true if DHCP is enabled and false
                if DHCP is disabled.

        :return: JSON representation of a Subnet

        """
        new_subnet = api.neutron.subnet_create(request, **request.DATA)
        return rest_utils.CreatedResponse(
            '/api/neutron/subnets/%s' % new_subnet.id,
            new_subnet.to_dict()
        )


@urls.register
class Ports(generic.View):
    """API for Neutron Ports
    http://developer.openstack.org/api-ref-networking-v2.html#ports
    """
    url_regex = r'neutron/ports/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of ports for a network

        The listing result is an object with property "items".  Each item is
        a subnet.
        """
        # see
        # https://github.com/openstack/neutron/blob/master/neutron/api/v2/attributes.py
        result = api.neutron.port_list(request, **request.GET)
        return{'items': [n.to_dict() for n in result]}
