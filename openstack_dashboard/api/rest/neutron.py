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
"""API over the neutron service."""

from django.utils.translation import ugettext_lazy as _
from django.views import generic

from openstack_dashboard import api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils
from openstack_dashboard.usage import quotas


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
        new_network = api.neutron.network_create(request, **request.DATA)
        return rest_utils.CreatedResponse(
            '/api/neutron/networks/%s' % new_network.id,
            new_network.to_dict()
        )


@urls.register
class Subnets(generic.View):
    """API for Neutron Subnets

    http://developer.openstack.org/api-ref-networking-v2.html#subnets
    """
    url_regex = r'neutron/subnets/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of subnets for a project

        The listing result is an object with property "items".  Each item is
        a subnet.

        """
        result = api.neutron.subnet_list(request, **request.GET.dict())
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
        result = api.neutron.port_list(request, **request.GET.dict())
        return{'items': [n.to_dict() for n in result]}


@urls.register
class Trunk(generic.View):
    """API for a single neutron Trunk"""
    url_regex = r'neutron/trunks/(?P<trunk_id>[^/]+)/$'

    @rest_utils.ajax()
    def delete(self, request, trunk_id):
        api.neutron.trunk_delete(request, trunk_id)

    @rest_utils.ajax()
    def get(self, request, trunk_id):
        """Get a specific trunk"""
        trunk = api.neutron.trunk_show(request, trunk_id)
        return trunk.to_dict()


@urls.register
class Trunks(generic.View):
    """API for neutron Trunks"""
    url_regex = r'neutron/trunks/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of trunks

        The listing result is an object with property "items".
        Each item is a trunk.
        """
        result = api.neutron.trunk_list(request, **request.GET.dict())
        return {'items': [n.to_dict() for n in result]}


@urls.register
class Services(generic.View):
    """API for Neutron agents"""
    url_regex = r'neutron/agents/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of agents"""
        if api.base.is_service_enabled(request, 'network') and \
           api.neutron.is_extension_supported(request, 'agent'):
            result = api.neutron.agent_list(request, **request.GET.dict())
            return {'items': [n.to_dict() for n in result]}
        else:
            raise rest_utils.AjaxError(501, '')


@urls.register
class Extensions(generic.View):
    """API for neutron extensions."""
    url_regex = r'neutron/extensions/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of extensions.

        The listing result is an object with property "items". Each item is
        an extension.

        Example:
        http://localhost/api/neutron/extensions
        """
        result = api.neutron.list_extensions(request)
        return {'items': [e for e in result]}


class DefaultQuotaSets(generic.View):
    """API for getting default quotas for neutron"""
    url_regex = r'neutron/quota-sets/defaults/$'

    @rest_utils.ajax()
    def get(self, request):
        if api.base.is_service_enabled(request, 'network'):
            quota_set = api.neutron.tenant_quota_get(
                request, request.user.tenant_id)

            result = [{
                'display_name': quotas.QUOTA_NAMES.get(
                    quota.name,
                    quota.name.replace('_', ' ').title()
                ) + '',
                'name': quota.name,
                'limit': quota.limit
            } for quota in quota_set]

            return {'items': result}
        else:
            raise rest_utils.AjaxError(501, _('Service Neutron is disabled.'))


@urls.register
class QuotasSets(generic.View):
    """API for setting quotas of a given project."""
    url_regex = r'neutron/quotas-sets/(?P<project_id>[0-9a-f]+)$'

    @rest_utils.ajax(data_required=True)
    def patch(self, request, project_id):
        """Update a single project quota data.

        The PATCH data should be an application/json object with the
        attributes to set to new quota values.

        This method returns HTTP 204 (no content) on success.
        """
        # Filters only neutron quota fields
        disabled_quotas = quotas.get_disabled_quotas(request)

        if api.base.is_service_enabled(request, 'network') and \
                api.neutron.is_extension_supported(request, 'quotas'):
            neutron_data = {
                key: request.DATA[key] for key in quotas.NEUTRON_QUOTA_FIELDS
                if key not in disabled_quotas
            }

            api.neutron.tenant_quota_update(request,
                                            project_id,
                                            **neutron_data)
        else:
            message = _('Service Neutron is disabled or quotas extension not '
                        'available.')
            raise rest_utils.AjaxError(501, message)


@urls.register
class QoSPolicies(generic.View):
    """API for QoS Policy."""
    url_regex = r'neutron/qos_policies/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of QoS policies.

        The listing result is an object with property "items".
        Each item is a qos policy.
        """
        # TODO(amotoki):
        # project_id=request.user.project_id should be changed to
        # tenant_id=request.user.project_id once bug 1695954 is
        # addressed to allow tenant_id to be accepted.
        result = api.neutron.policy_list(request,
                                         project_id=request.user.project_id)
        return {'items': [p.to_dict() for p in result]}


@urls.register
class QoSPolicy(generic.View):
    """API for a single QoS Policy."""
    url_regex = r'neutron/qos_policy/(?P<policy_id>[^/]+)/$'

    @rest_utils.ajax()
    def get(self, request, policy_id):
        """Get a specific policy"""
        policy = api.neutron.policy_get(request, policy_id)
        return policy.to_dict()
