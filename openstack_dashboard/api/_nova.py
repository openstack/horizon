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

"""
This module is a special module to define functions or other resources
which need to be imported outside of openstack_dashboard.api.nova
(like cinder.py) to avoid cyclic imports.
"""

from django.conf import settings
from glanceclient import exc as glance_exceptions
from novaclient import api_versions
from novaclient import client as nova_client

from horizon import exceptions as horizon_exceptions
from horizon.utils import memoized

from openstack_dashboard.api import base
from openstack_dashboard.api import glance
from openstack_dashboard.api import microversions
from openstack_dashboard.contrib.developer.profiler import api as profiler


# Supported compute versions
VERSIONS = base.APIVersionManager("compute", preferred_version=2)
VERSIONS.load_supported_version(1.1, {"client": nova_client, "version": 1.1})
VERSIONS.load_supported_version(2, {"client": nova_client, "version": 2})

INSECURE = settings.OPENSTACK_SSL_NO_VERIFY
CACERT = settings.OPENSTACK_SSL_CACERT


class Server(base.APIResourceWrapper):
    """Simple wrapper around novaclient.server.Server.

    Preserves the request info so image name can later be retrieved.
    """
    _attrs = ['addresses', 'attrs', 'id', 'image', 'links', 'description',
              'metadata', 'name', 'private_ip', 'public_ip', 'status', 'uuid',
              'image_name', 'VirtualInterfaces', 'flavor', 'key_name', 'fault',
              'tenant_id', 'user_id', 'created', 'locked',
              'OS-EXT-STS:power_state', 'OS-EXT-STS:task_state',
              'OS-EXT-SRV-ATTR:instance_name', 'OS-EXT-SRV-ATTR:host',
              'OS-EXT-AZ:availability_zone', 'OS-DCF:diskConfig']

    def __init__(self, apiresource, request):
        super(Server, self).__init__(apiresource)
        self.request = request

    # TODO(gabriel): deprecate making a call to Glance as a fallback.
    @property
    def image_name(self):
        if not self.image:
            return None
        elif hasattr(self.image, 'name'):
            return self.image.name
        elif 'name' in self.image:
            return self.image['name']
        else:
            try:
                image = glance.image_get(self.request, self.image['id'])
                self.image['name'] = image.name
                return image.name
            except (glance_exceptions.ClientException,
                    horizon_exceptions.ServiceCatalogException):
                self.image['name'] = None
                return None

    @property
    def internal_name(self):
        return getattr(self, 'OS-EXT-SRV-ATTR:instance_name', "")

    @property
    def availability_zone(self):
        return getattr(self, 'OS-EXT-AZ:availability_zone', "")

    @property
    def host_server(self):
        return getattr(self, 'OS-EXT-SRV-ATTR:host', '')


@memoized.memoized
def get_microversion(request, features):
    client = novaclient(request)
    min_ver, max_ver = api_versions._get_server_version_range(client)
    return (microversions.get_microversion_for_features(
        'nova', features, api_versions.APIVersion, min_ver, max_ver))


def get_auth_params_from_request(request):
    """Extracts properties needed by novaclient call from the request object.

    These will be used to memoize the calls to novaclient.
    """
    return (
        request.user.username,
        request.user.token.id,
        request.user.tenant_id,
        request.user.token.project.get('domain_id'),
        base.url_for(request, 'compute'),
        base.url_for(request, 'identity')
    )


@memoized.memoized
def cached_novaclient(request, version=None):
    (
        username,
        token_id,
        project_id,
        project_domain_id,
        nova_url,
        auth_url
    ) = get_auth_params_from_request(request)
    if version is None:
        version = VERSIONS.get_active_version()['version']
    c = nova_client.Client(version,
                           username,
                           token_id,
                           project_id=project_id,
                           project_domain_id=project_domain_id,
                           auth_url=auth_url,
                           insecure=INSECURE,
                           cacert=CACERT,
                           http_log_debug=settings.DEBUG,
                           auth_token=token_id,
                           endpoint_override=nova_url)
    return c


def novaclient(request, version=None):
    if isinstance(version, api_versions.APIVersion):
        version = version.get_string()
    return cached_novaclient(request, version)


def get_novaclient_with_instance_desc(request):
    microversion = get_microversion(request, "instance_description")
    return novaclient(request, version=microversion)


@profiler.trace
def server_get(request, instance_id):
    return Server(get_novaclient_with_instance_desc(request).servers.get(
        instance_id), request)
