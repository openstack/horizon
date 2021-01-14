# Copyright 2014, Rackspace, US, Inc.
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
"""API over the nova service."""
from collections import OrderedDict

from django.utils import http as utils_http
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from novaclient import exceptions

from horizon import exceptions as hz_exceptions

from openstack_dashboard import api
from openstack_dashboard.api.rest import json_encoder
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils
from openstack_dashboard.dashboards.project.instances \
    import utils as instances_utils
from openstack_dashboard.usage import quotas


@urls.register
class Snapshots(generic.View):
    """API for nova snapshots."""
    url_regex = r'nova/snapshots/$'

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        instance_id = request.DATA['instance_id']
        name = request.DATA['name']
        result = api.nova.snapshot_create(request,
                                          instance_id=instance_id,
                                          name=name)
        return result


@urls.register
class Features(generic.View):
    """API for check if a specified feature is supported."""
    url_regex = r'nova/features/(?P<name>[^/]+)/$'

    @rest_utils.ajax()
    def get(self, request, name):
        """Check if a specified feature is supported."""
        return api.nova.is_feature_available(request, (name,))


@urls.register
class Keypairs(generic.View):
    """API for nova keypairs."""
    url_regex = r'nova/keypairs/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of keypairs associated with the current logged-in user.

        The listing result is an object with property "items".
        """
        result = api.nova.keypair_list(request)
        return {'items': [u.to_dict() for u in result]}

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        """Create a keypair.

        Create a keypair using the parameters supplied in the POST
        application/json object. The parameters are:

        :param name: the name to give the keypair
        :param public_key: (optional) a key to import

        This returns the new keypair object on success.
        """
        if 'public_key' in request.DATA:
            new = api.nova.keypair_import(request, request.DATA['name'],
                                          request.DATA['public_key'],
                                          request.DATA['key_type'])
        else:
            new = api.nova.keypair_create(request,
                                          request.DATA['name'],
                                          request.DATA['key_type'])
        return rest_utils.CreatedResponse(
            '/api/nova/keypairs/%s' % utils_http.urlquote(new.name),
            new.to_dict()
        )


@urls.register
class Keypair(generic.View):
    """API for retrieving a single keypair."""
    url_regex = r'nova/keypairs/(?P<name>[^/]+)$'

    @rest_utils.ajax()
    def get(self, request, name):
        """Get a specific keypair."""
        return api.nova.keypair_get(request, name).to_dict()

    @rest_utils.ajax()
    def delete(self, request, name):
        api.nova.keypair_delete(request, name)


@urls.register
class Services(generic.View):
    """API for nova services."""
    url_regex = r'nova/services/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of nova services.

        Will return HTTP 501 status code if the compute service is enabled.
        """
        if api.base.is_service_enabled(request, 'compute'):
            result = api.nova.service_list(request)
            return {'items': [u.to_dict() for u in result]}
        raise rest_utils.AjaxError(501, '')


@urls.register
class AvailabilityZones(generic.View):
    """API for nova availability zones."""
    url_regex = r'nova/availzones/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of availability zones.

        The following get parameters may be passed in the GET
        request:

        :param detailed: If this equals "true" then the result will
            include more detail.

        The listing result is an object with property "items".
        """
        detailed = request.GET.get('detailed') == 'true'
        result = api.nova.availability_zone_list(request, detailed)
        return {'items': [u.to_dict() for u in result]}


@urls.register
class Limits(generic.View):
    """API for nova limits."""
    url_regex = r'nova/limits/$'

    @rest_utils.ajax(json_encoder=json_encoder.NaNJSONEncoder)
    def get(self, request):
        """Get an object describing the current project limits.

        Note: the Horizon API doesn't support any other project (tenant) but
        the underlying client does...

        The following get parameters may be passed in the GET
        request:

        :param reserved: Take into account the reserved limits. Reserved limits
            may be instances in the rebuild process for example.

        The result is an object with limits as properties.
        """
        reserved = request.GET.get('reserved') == 'true'
        result = api.nova.tenant_absolute_limits(request, reserved)
        return result


@urls.register
class ServerActions(generic.View):
    """API over all server actions."""
    url_regex = r'nova/servers/(?P<server_id>[^/]+)/actions/$'

    @rest_utils.ajax()
    def get(self, request, server_id):
        """Get a list of server actions.

        The listing result is an object with property "items". Each item is
        an action taken against the given server.

        Example GET:
        http://localhost/api/nova/servers/abcd/actions/
        """
        actions = api.nova.instance_action_list(request, server_id)
        return {'items': [s.to_dict() for s in actions]}


@urls.register
class SecurityGroups(generic.View):
    """API over all server security groups."""
    url_regex = r'nova/servers/(?P<server_id>[^/]+)/security-groups/$'

    @rest_utils.ajax()
    def get(self, request, server_id):
        """Get a list of server security groups.

        The listing result is an object with property "items". Each item is
        security group associated with this server.

        Example GET:
        http://localhost/api/nova/servers/abcd/security-groups/
        """
        groups = api.neutron.server_security_groups(request, server_id)
        return {'items': [s.to_dict() for s in groups]}


@urls.register
class Volumes(generic.View):
    """API over all server volumes."""
    url_regex = r'nova/servers/(?P<server_id>[^/]+)/volumes/$'

    @rest_utils.ajax()
    def get(self, request, server_id):
        """Get a list of server volumes.

        The listing result is an object with property "items". Each item is
        a volume.

        Example GET:
        http://localhost/api/nova/servers/abcd/volumes/
        """
        volumes = api.nova.instance_volumes_list(request, server_id)
        return {'items': [s.to_dict() for s in volumes]}


@urls.register
class RemoteConsoleInfo(generic.View):
    """API for remote console information."""
    url_regex = r'nova/servers/(?P<server_id>[^/]+)/console-info/$'

    @rest_utils.ajax()
    def post(self, request, server_id):
        """Gets information of a remote console for the given server.

        Example POST:
        http://localhost/api/nova/servers/abcd/console-info/
        """
        console_type = request.DATA.get('console_type', 'AUTO')
        CONSOLES = OrderedDict([('VNC', api.nova.server_vnc_console),
                                ('SPICE', api.nova.server_spice_console),
                                ('RDP', api.nova.server_rdp_console),
                                ('SERIAL', api.nova.server_serial_console),
                                ('MKS', api.nova.server_mks_console)])

        """Get a tuple of console url and console type."""
        if console_type == 'AUTO':
            check_consoles = CONSOLES
        else:
            try:
                check_consoles = {console_type: CONSOLES[console_type]}
            except KeyError:
                msg = _('Console type "%s" not supported.') % console_type
                raise hz_exceptions.NotAvailable(msg)

        # Ugly workaround due novaclient API change from 2.17 to 2.18.
        try:
            httpnotimplemented = exceptions.HttpNotImplemented
        except AttributeError:
            httpnotimplemented = exceptions.HTTPNotImplemented

        for con_type, api_call in check_consoles.items():
            try:
                console = api_call(request, server_id)
            # If not supported, don't log it to avoid lot of errors in case
            # of AUTO.
            except httpnotimplemented:
                continue
            except Exception:
                continue

            if con_type == 'SERIAL':
                console_url = console.url
            else:
                console_url = "%s&%s(%s)" % (
                              console.url,
                              utils_http.urlencode({'title': _("Console")}),
                              server_id)

            return {"type": con_type, "url": console_url}
        raise hz_exceptions.NotAvailable(_('No available console found.'))


@urls.register
class ConsoleOutput(generic.View):
    """API for console output."""
    url_regex = r'nova/servers/(?P<server_id>[^/]+)/console-output/$'

    @rest_utils.ajax()
    def post(self, request, server_id):
        """Get a list of lines of console output.

        The listing result is an object with property "items". Each item is
        a line of output from the server.

        Example GET:
        http://localhost/api/nova/servers/abcd/console-output/
        """
        log_length = request.DATA.get('length', 100)
        console_lines = api.nova.server_console_output(request, server_id,
                                                       tail_length=log_length)
        return {"lines": console_lines.split('\n')}


@urls.register
class Servers(generic.View):
    """API over all servers."""
    url_regex = r'nova/servers/$'

    _optional_create = [
        'block_device_mapping', 'block_device_mapping_v2', 'nics', 'meta',
        'availability_zone', 'instance_count', 'admin_pass', 'disk_config',
        'config_drive', 'scheduler_hints', 'description'
    ]

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of servers.

        The listing result is an object with property "items". Each item is
        a server.

        Example GET:
        http://localhost/api/nova/servers
        """
        servers = api.nova.server_list(request)[0]
        return {'items': [s.to_dict() for s in servers]}

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        """Create a server.

        Create a server using the parameters supplied in the POST
        application/json object. The required parameters as specified by
        the underlying novaclient are:

        :param name: The new server name.
        :param source_id: The ID of the image to use.
        :param flavor_id: The ID of the flavor to use.
        :param key_name: (optional) name of previously created
                      keypair to inject into the instance.
        :param user_data: user data to pass to be exposed by the metadata
                      server this can be a file type object as well or a
                      string.
        :param security_groups: An array of one or more objects with a "name"
            attribute.

        Other parameters are accepted as per the underlying novaclient:
        "block_device_mapping", "block_device_mapping_v2", "nics", "meta",
        "availability_zone", "instance_count", "admin_pass", "disk_config",
        "config_drive", "scheduler_hints"

        This returns the new server object on success.
        """
        try:
            args = (
                request,
                request.DATA['name'],
                request.DATA['source_id'],
                request.DATA['flavor_id'],
                request.DATA['key_name'],
                request.DATA['user_data'],
                request.DATA['security_groups'],
            )
        except KeyError as e:
            raise rest_utils.AjaxError(400, 'missing required parameter '
                                            "'%s'" % e.args[0])
        kw = {}
        for name in self._optional_create:
            if name in request.DATA:
                kw[name] = request.DATA[name]

        new = api.nova.server_create(*args, **kw)
        return rest_utils.CreatedResponse(
            '/api/nova/servers/%s' % utils_http.urlquote(new.id),
            new.to_dict()
        )


@urls.register
class Server(generic.View):
    """API for retrieving a single server"""
    url_regex = r'nova/servers/(?P<server_id>[^/]+|default)$'

    @rest_utils.ajax()
    def get(self, request, server_id):
        """Get a specific server

        http://localhost/api/nova/servers/1
        """
        return api.nova.server_get(request, server_id).to_dict()

    @rest_utils.ajax(data_required=True)
    def post(self, request, server_id):
        """Perform a change to a server"""
        operation = request.DATA.get('operation', 'none')
        operations = {
            'stop': api.nova.server_stop,
            'start': api.nova.server_start,
            'pause': api.nova.server_pause,
            'unpause': api.nova.server_unpause,
            'suspend': api.nova.server_suspend,
            'resume': api.nova.server_resume,
            'hard_reboot': lambda r, s: api.nova.server_reboot(r, s, False),
            'soft_reboot': lambda r, s: api.nova.server_reboot(r, s, True),
        }
        return operations[operation](request, server_id)

    @rest_utils.ajax()
    def delete(self, request, server_id):
        api.nova.server_delete(request, server_id)


@urls.register
class ServerGroups(generic.View):
    """API for nova server groups."""
    url_regex = r'nova/servergroups/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of server groups.

        The listing result is an object with property "items".
        """
        result = api.nova.server_group_list(request)
        return {'items': [u.to_dict() for u in result]}

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        """Create a server group.

        Create a server group using parameters supplied in the POST
        application/json object. The "name" (string) parameter is required
        and the "policies" (array) parameter is required.

        This method returns the new server group object on success.
        """
        new_servergroup = api.nova.server_group_create(request, **request.DATA)
        return rest_utils.CreatedResponse(
            '/api/nova/servergroups/%s' % utils_http.urlquote(
                new_servergroup.id), new_servergroup.to_dict()
        )


@urls.register
class ServerGroup(generic.View):
    url_regex = r'nova/servergroups/(?P<servergroup_id>[^/]+)/$'

    @rest_utils.ajax()
    def delete(self, request, servergroup_id):
        """Delete a specific server group

        DELETE http://localhost/api/nova/servergroups/<servergroup_id>
        """
        api.nova.server_group_delete(request, servergroup_id)

    @rest_utils.ajax()
    def get(self, request, servergroup_id):
        """Get a specific server group

        http://localhost/api/nova/servergroups/1
        """
        return api.nova.server_group_get(request, servergroup_id).to_dict()


@urls.register
class ServerMetadata(generic.View):
    """API for server metadata."""
    url_regex = r'nova/servers/(?P<server_id>[^/]+|default)/metadata$'

    @rest_utils.ajax()
    def get(self, request, server_id):
        """Get a specific server's metadata

        http://localhost/api/nova/servers/1/metadata
        """
        return api.nova.server_get(request,
                                   server_id).to_dict().get('metadata')

    @rest_utils.ajax()
    def patch(self, request, server_id):
        """Update metadata items for a server

        http://localhost/api/nova/servers/1/metadata
        """
        updated = request.DATA['updated']
        removed = request.DATA['removed']
        if updated:
            api.nova.server_metadata_update(request, server_id, updated)
        if removed:
            api.nova.server_metadata_delete(request, server_id, removed)


@urls.register
class Flavors(generic.View):
    """API for nova flavors."""
    url_regex = r'nova/flavors/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of flavors.

        The listing result is an object with property "items". Each item is
        a flavor. By default this will return the flavors for the user's
        current project. If the user is admin, public flavors will also be
        returned.

        :param is_public: For a regular user, set to True to see all public
            flavors. For an admin user, set to False to not see public flavors.
        :param get_extras: Also retrieve the extra specs.

        Example GET:
        http://localhost/api/nova/flavors?is_public=true
        """
        is_public = request.GET.get('is_public')
        is_public = (is_public and is_public.lower() == 'true')
        get_extras = request.GET.get('get_extras')
        get_extras = bool(get_extras and get_extras.lower() == 'true')
        flavors = api.nova.flavor_list(request, is_public=is_public,
                                       get_extras=get_extras)
        flavors = instances_utils.sort_flavor_list(request, flavors,
                                                   with_menu_label=False)
        result = {'items': []}
        for flavor in flavors:
            d = flavor.to_dict()
            if get_extras:
                d['extras'] = flavor.extras
            result['items'].append(d)
        return result

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        flavor_access = request.DATA.get('flavor_access', [])
        flavor_id = request.DATA['id']
        is_public = not flavor_access

        flavor = api.nova.flavor_create(request,
                                        name=request.DATA['name'],
                                        memory=request.DATA['ram'],
                                        vcpu=request.DATA['vcpus'],
                                        disk=request.DATA['disk'],
                                        ephemeral=request
                                        .DATA['OS-FLV-EXT-DATA:ephemeral'],
                                        swap=request.DATA['swap'],
                                        flavorid=flavor_id,
                                        is_public=is_public
                                        )

        for project in flavor_access:
            api.nova.add_tenant_to_flavor(
                request, flavor.id, project.get('id'))

        return rest_utils.CreatedResponse(
            '/api/nova/flavors/%s' % flavor.id,
            flavor.to_dict()
        )


@urls.register
class Flavor(generic.View):
    """API for retrieving a single flavor"""
    url_regex = r'nova/flavors/(?P<flavor_id>[^/]+)/$'

    @rest_utils.ajax()
    def get(self, request, flavor_id):
        """Get a specific flavor

        :param get_extras: Also retrieve the extra specs.

        Example GET:
        http://localhost/api/nova/flavors/1
        """
        get_extras = self.extract_boolean(request, 'get_extras')
        get_access_list = self.extract_boolean(request, 'get_access_list')
        flavor = api.nova.flavor_get(request, flavor_id, get_extras=get_extras)

        result = flavor.to_dict()
        # Bug: nova API stores and returns empty string when swap equals 0
        # https://bugs.launchpad.net/nova/+bug/1408954
        if 'swap' in result and result['swap'] == '':
            result['swap'] = 0
        if get_extras:
            result['extras'] = flavor.extras

        if get_access_list and not flavor.is_public:
            access_list = [item.tenant_id for item in
                           api.nova.flavor_access_list(request, flavor_id)]
            result['access-list'] = access_list
        return result

    @rest_utils.ajax()
    def delete(self, request, flavor_id):
        api.nova.flavor_delete(request, flavor_id)

    @rest_utils.ajax(data_required=True)
    def patch(self, request, flavor_id):
        flavor_access = request.DATA.get('flavor_access', [])
        is_public = not flavor_access

        # Grab any existing extra specs, because flavor edit is currently
        # implemented as a delete followed by a create.
        extras_dict = api.nova.flavor_get_extras(request, flavor_id, raw=True)
        # Mark the existing flavor as deleted.
        api.nova.flavor_delete(request, flavor_id)
        # Then create a new flavor with the same name but a new ID.
        # This is in the same try/except block as the delete call
        # because if the delete fails the API will error out because
        # active flavors can't have the same name.
        flavor = api.nova.flavor_create(request,
                                        name=request.DATA['name'],
                                        memory=request.DATA['ram'],
                                        vcpu=request.DATA['vcpus'],
                                        disk=request.DATA['disk'],
                                        ephemeral=request
                                        .DATA['OS-FLV-EXT-DATA:ephemeral'],
                                        swap=request.DATA['swap'],
                                        flavorid=flavor_id,
                                        is_public=is_public
                                        )
        for project in flavor_access:
            api.nova.add_tenant_to_flavor(
                request, flavor.id, project.get('id'))

        if extras_dict:
            api.nova.flavor_extra_set(request, flavor.id, extras_dict)

    def extract_boolean(self, request, name):
        bool_string = request.GET.get(name)
        return bool(bool_string and bool_string.lower() == 'true')


@urls.register
class FlavorExtraSpecs(generic.View):
    """API for managing flavor extra specs"""
    url_regex = r'nova/flavors/(?P<flavor_id>[^/]+)/extra-specs/$'

    @rest_utils.ajax()
    def get(self, request, flavor_id):
        """Get a specific flavor's extra specs

        Example GET:
        http://localhost/api/nova/flavors/1/extra-specs
        """
        return api.nova.flavor_get_extras(request, flavor_id, raw=True)

    @rest_utils.ajax(data_required=True)
    def patch(self, request, flavor_id):
        """Update a specific flavor's extra specs.

        This method returns HTTP 204 (no content) on success.
        """
        if request.DATA.get('removed'):
            api.nova.flavor_extra_delete(
                request, flavor_id, request.DATA.get('removed')
            )
        api.nova.flavor_extra_set(
            request, flavor_id, request.DATA['updated']
        )


@urls.register
class AggregateExtraSpecs(generic.View):
    """API for managing aggregate extra specs"""
    url_regex = r'nova/aggregates/(?P<aggregate_id>[^/]+)/extra-specs/$'

    @rest_utils.ajax()
    def get(self, request, aggregate_id):
        """Get a specific aggregate's extra specs

        Example GET:
        http://localhost/api/nova/flavors/1/extra-specs
        """
        return api.nova.aggregate_get(request, aggregate_id).metadata

    @rest_utils.ajax(data_required=True)
    def patch(self, request, aggregate_id):
        """Update a specific aggregate's extra specs.

        This method returns HTTP 204 (no content) on success.
        """
        updated = request.DATA['updated']
        if request.DATA.get('removed'):
            for name in request.DATA.get('removed'):
                updated[name] = None
        api.nova.aggregate_set_metadata(request, aggregate_id, updated)


@urls.register
class DefaultQuotaSets(generic.View):
    """API for getting default quotas for nova"""
    url_regex = r'nova/quota-sets/defaults/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get the values for Nova specific quotas

        Example GET:
        http://localhost/api/nova/quota-sets/defaults/
        """
        if not api.base.is_service_enabled(request, 'compute'):
            raise rest_utils.AjaxError(501, _('Service Nova is disabled.'))

        quota_set = api.nova.default_quota_get(request,
                                               request.user.tenant_id)

        disabled_quotas = quotas.get_disabled_quotas(request)

        filtered_quotas = [quota for quota in quota_set
                           if quota.name not in disabled_quotas]

        result = [{
            'display_name': quotas.QUOTA_NAMES.get(
                quota.name,
                quota.name.replace("_", " ").title()
            ) + '',
            'name': quota.name,
            'limit': quota.limit
        } for quota in filtered_quotas]

        return {'items': result}

    @rest_utils.ajax(data_required=True)
    def patch(self, request):
        """Update the values for Nova specific quotas

        This method returns HTTP 204 (no content) on success.
        """
        if api.base.is_service_enabled(request, 'compute'):
            disabled_quotas = quotas.get_disabled_quotas(request)

            filtered_quotas = [quota for quota in quotas.NOVA_QUOTA_FIELDS
                               if quota not in disabled_quotas]

            request_data = {
                key: request.DATA.get(key, None) for key in filtered_quotas
            }

            nova_data = {key: value for key, value in request_data.items()
                         if value is not None}

            api.nova.default_quota_update(request, **nova_data)
        else:
            raise rest_utils.AjaxError(501, _('Service Nova is disabled.'))


@urls.register
class EditableQuotaSets(generic.View):
    """API for editable quotas."""
    url_regex = r'nova/quota-sets/editable/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of editable quota fields.

        The listing result is an object with property "items". Each item
        is an editable quota. Returns an empty list in case no editable
        quota is found.
        """
        disabled_quotas = quotas.get_disabled_quotas(request)
        editable_quotas = [quota for quota in quotas.QUOTA_FIELDS
                           if quota not in disabled_quotas]
        return {'items': editable_quotas}


@urls.register
class QuotaSets(generic.View):
    """API for setting quotas for a given project."""
    url_regex = r'nova/quota-sets/(?P<project_id>[0-9a-f]+)$'

    @rest_utils.ajax(data_required=True)
    def patch(self, request, project_id):
        """Update a single project quota data.

        The PATCH data should be an application/json object with the
        attributes to set to new quota values.

        This method returns HTTP 204 (no content) on success.
        """
        disabled_quotas = quotas.get_disabled_quotas(request)

        if api.base.is_service_enabled(request, 'compute'):
            nova_data = {
                key: request.DATA[key] for key in quotas.NOVA_QUOTA_FIELDS
                if key not in disabled_quotas
            }

            api.nova.tenant_quota_update(request, project_id, **nova_data)
        else:
            raise rest_utils.AjaxError(501, _('Service Nova is disabled.'))
