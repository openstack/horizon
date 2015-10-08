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
"""API over the nova service.
"""
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.utils import http as utils_http
from django.views import generic

from novaclient import exceptions

from openstack_dashboard import api
from openstack_dashboard.api.rest import json_encoder
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils


@urls.register
class Keypairs(generic.View):
    """API for nova keypairs.
    """
    url_regex = r'nova/keypairs/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of keypairs associated with the current logged-in
        account.

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
                                          request.DATA['public_key'])
        else:
            new = api.nova.keypair_create(request, request.DATA['name'])
        return rest_utils.CreatedResponse(
            '/api/nova/keypairs/%s' % utils_http.urlquote(new.name),
            new.to_dict()
        )


@urls.register
class Keypair(generic.View):
    url_regex = r'nova/keypairs/(?P<keypair_name>.+)/$'

    def get(self, request, keypair_name):
        """Creates a new keypair and associates it to the current project.

        * Since the response for this endpoint creates a new keypair and
          is not idempotent, it normally would be represented by a POST HTTP
          request. However, this solution was adopted as it
          would support automatic file download across browsers.

        :param keypair_name: the name to associate the keypair to
        :param regenerate: (optional) if set to the string 'true',
            replaces the existing keypair with a new keypair

        This returns the new keypair object on success.
        """
        try:
            regenerate = request.GET.get('regenerate') == 'true'
            if regenerate:
                api.nova.keypair_delete(request, keypair_name)

            keypair = api.nova.keypair_create(request, keypair_name)

        except exceptions.Conflict:
            return HttpResponse(status=409)

        except Exception:
            return HttpResponse(status=500)

        else:
            response = HttpResponse(content_type='application/binary')
            response['Content-Disposition'] = ('attachment; filename=%s.pem'
                                               % slugify(keypair_name))
            response.write(keypair.private_key)
            response['Content-Length'] = str(len(response.content))

            return response


@urls.register
class Services(generic.View):
    """API for nova services.
    """
    url_regex = r'nova/services/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of nova services.
        Will return HTTP 501 status code if the service_list extension is
        not supported.
        """
        if api.base.is_service_enabled(request, 'compute') \
           and api.nova.extension_supported('Services', request):
            result = api.nova.service_list(request)
            return {'items': [u.to_dict() for u in result]}
        else:
            raise rest_utils.AjaxError(501, '')


@urls.register
class AvailabilityZones(generic.View):
    """API for nova availability zones.
    """
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
    """API for nova limits.
    """
    url_regex = r'nova/limits/$'

    @rest_utils.ajax(json_encoder=json_encoder.NaNJSONEncoder)
    def get(self, request):
        """Get an object describing the current project limits.

        Note: the Horizon API doesn't support any other project (tenant) but
        the underlying client does...

        The following get parameters may be passed in the GET
        request:

        :param reserved: This may be set to "true" but it's not
            clear what the result of that is.

        The result is an object with limits as properties.
        """
        reserved = request.GET.get('reserved') == 'true'
        result = api.nova.tenant_absolute_limits(request, reserved)
        return result


@urls.register
class Servers(generic.View):
    """API over all servers.
    """
    url_regex = r'nova/servers/$'

    _optional_create = [
        'block_device_mapping', 'block_device_mapping_v2', 'nics', 'meta',
        'availability_zone', 'instance_count', 'admin_pass', 'disk_config',
        'config_drive'
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
        :param key_name: (optional extension) name of previously created
                      keypair to inject into the instance.
        :param user_data: user data to pass to be exposed by the metadata
                      server this can be a file type object as well or a
                      string.
        :param security_groups: An array of one or more objects with a "name"
            attribute.

        Other parameters are accepted as per the underlying novaclient:
        "block_device_mapping", "block_device_mapping_v2", "nics", "meta",
        "availability_zone", "instance_count", "admin_pass", "disk_config",
        "config_drive"

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
    """API for retrieving a single server
    """
    url_regex = r'nova/servers/(?P<server_id>[^/]+|default)$'

    @rest_utils.ajax()
    def get(self, request, server_id):
        """Get a specific server

        http://localhost/api/nova/servers/1
        """
        return api.nova.server_get(request, server_id).to_dict()


@urls.register
class ServerMetadata(generic.View):
    """API for server metadata.
    """
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
class Extensions(generic.View):
    """API for nova extensions.
    """
    url_regex = r'nova/extensions/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of extensions.

        The listing result is an object with property "items". Each item is
        an image.

        Example GET:
        http://localhost/api/nova/extensions
        """
        result = api.nova.list_extensions(request)
        return {'items': [e.to_dict() for e in result]}


@urls.register
class Flavors(generic.View):
    """API for nova flavors.
    """
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
    """API for retrieving a single flavor
    """
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
    """API for managing flavor extra specs
    """
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
    """API for managing aggregate extra specs
    """
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
