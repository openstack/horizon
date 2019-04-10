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

"""Default settings for openstack_dashboard"""

# This must be configured
# OPENSTACK_KEYSTONE_URL = 'http://localhost/identity/v3'

# The number of objects (Swift containers/objects or images) to display
# on a single page before providing a paging element (a "more" link)
# to paginate results.
API_RESULT_LIMIT = 1000
API_RESULT_PAGE_SIZE = 20

ENABLE_CLIENT_TOKEN = True
# Set this to True to display an 'Admin Password' field on the Change Password
# form to verify that it is indeed the admin logged-in who wants to change
# the password.
ENFORCE_PASSWORD_CHECK = False
# Set to 'legacy' or 'direct' to allow users to upload images to glance via
# Horizon server. When enabled, a file form field will appear on the create
# image form. If set to 'off', there will be no file form field on the create
# image form. See documentation for deployment considerations.
HORIZON_IMAGES_UPLOAD_MODE = 'legacy'
# Allow a location to be set when creating or updating Glance images.
# If using Glance V2, this value should be False unless the Glance
# configuration and policies allow setting locations.
IMAGES_ALLOW_LOCATION = False

# The size of chunk in bytes for downloading objects from Swift
SWIFT_FILE_TRANSFER_CHUNK_SIZE = 512 * 1024

# Overrides for OpenStack API versions. Use this setting to force the
# OpenStack dashboard to use a specific API version for a given service API.
# Versions specified here should be integers or floats, not strings.
# NOTE: The version should be formatted as it appears in the URL for the
# service API. For example, The identity service APIs have inconsistent
# use of the decimal point, so valid options would be 2.0 or 3.
# Minimum compute version to get the instance locked status is 2.9.
OPENSTACK_API_VERSIONS = {
    "identity": 3,
    "image": 2,
    "volume": 3,
    "compute": 2,
}

# OPENSTACK_ENDPOINT_TYPE specifies the endpoint type to use for the endpoints
# in the Keystone service catalog. Use this setting when Horizon is running
# external to the OpenStack environment. The default is 'publicURL'.
OPENSTACK_ENDPOINT_TYPE = 'publicURL'
# SECONDARY_ENDPOINT_TYPE specifies the fallback endpoint type to use in the
# case that OPENSTACK_ENDPOINT_TYPE is not present in the endpoints
# in the Keystone service catalog. Use this setting when Horizon is running
# external to the OpenStack environment. The default is None. This
# value should differ from OPENSTACK_ENDPOINT_TYPE if used.
SECONDARY_ENDPOINT_TYPE = None

# Set True to disable SSL certificate checks
# (useful for self-signed certificates):
OPENSTACK_SSL_NO_VERIFY = False
# The CA certificate to use to verify SSL connections
# Example: OPENSTACK_SSL_CACERT = '/path/to/cacert.pem'
OPENSTACK_SSL_CACERT = None
# The OPENSTACK_CINDER_FEATURES settings can be used to enable optional
# services provided by cinder that is not exposed by its extension API.
OPENSTACK_CINDER_FEATURES = {
    'enable_backup': False,
}
# Overrides the default domain used when running on single-domain model
# with Keystone V3. All entities will be created in the default domain.
# NOTE: This value must be the name of the default domain, NOT the ID.
# Also, you will most likely have a value in the keystone policy file like this
#    "cloud_admin": "rule:admin_required and domain_id:<your domain id>"
# This value must be the name of the domain whose ID is specified there.
OPENSTACK_KEYSTONE_DEFAULT_DOMAIN = 'Default'
OPENSTACK_KEYSTONE_DEFAULT_ROLE = '_member_'
# The OPENSTACK_KEYSTONE_BACKEND settings can be used to identify the
# capabilities of the auth backend for Keystone.
# If Keystone has been configured to use LDAP as the auth backend then set
# can_edit_user to False and name to 'ldap'.
#
# TODO(tres): Remove these once Keystone has an API to identify auth backend.
OPENSTACK_KEYSTONE_BACKEND = {
    'name': 'native',
    'can_edit_domain': True,
    'can_edit_group': True,
    'can_edit_project': True,
    'can_edit_role': True,
    'can_edit_user': True,
}
# Set this to True if running on a multi-domain model. When this is enabled, it
# will require the user to enter the Domain name in addition to the username
# for login.
OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT = False
# Set this to True to enable panels that provide the ability for users to
# manage Identity Providers (IdPs) and establish a set of rules to map
# federation protocol attributes to Identity API attributes.
# This extension requires v3.0+ of the Identity API.
OPENSTACK_KEYSTONE_FEDERATION_MANAGEMENT = False
# The OPENSTACK_NEUTRON_NETWORK settings can be used to enable optional
# services provided by neutron. Options currently available are load
# balancer service, security groups, quotas, VPN service.
OPENSTACK_NEUTRON_NETWORK = {
    'enable_auto_allocated_network': False,
    'enable_distributed_router': False,
    'enable_fip_topology_check': True,
    'enable_ha_router': False,
    'enable_ipv6': True,
    # TODO(amotoki): Change the default value to True? See local_settings.py
    'enable_quotas': False,
    'enable_router': True,

    # Default dns servers you would like to use when a subnet is
    # created.  This is only a default, users can still choose a different
    # list of dns servers when creating a new subnet.
    # The entries below are examples only, and are not appropriate for
    # real deployments
    # 'default_dns_nameservers': ["8.8.8.8", "8.8.4.4", "208.67.222.222"],

    # Set which provider network types are supported. Only the network types
    # in this list will be available to choose from when creating a network.
    # Network types include local, flat, vlan, gre, vxlan and geneve.
    # 'supported_provider_types': ['*'],

    # You can configure available segmentation ID range per network type
    # in your deployment.
    # 'segmentation_id_range': {
    #     'vlan': [1024, 2048],
    #     'vxlan': [4094, 65536],
    # },

    # You can define additional provider network types here.
    # 'extra_provider_types': {
    #     'awesome_type': {
    #         'display_name': 'Awesome New Type',
    #         'require_physical_network': False,
    #         'require_segmentation_id': True,
    #     }
    # },

    # Set which VNIC types are supported for port binding. Only the VNIC
    # types in this list will be available to choose from when creating a
    # port.
    # VNIC types include 'normal', 'direct', 'direct-physical', 'macvtap',
    # 'baremetal' and 'virtio-forwarder'
    # Set to empty list or None to disable VNIC type selection.
    'supported_vnic_types': ['*'],

    # Set list of available physical networks to be selected in the physical
    # network field on the admin create network modal. If it's set to an empty
    # list, the field will be a regular input field.
    # e.g. ['default', 'test']
    'physical_networks': [],
}
OPENSTACK_NOVA_EXTENSIONS_BLACKLIST = []
# The Xen Hypervisor has the ability to set the mount point for volumes
# attached to instances (other Hypervisors currently do not). Setting
# can_set_mount_point to True will add the option to set the mount point
# from the UI.
OPENSTACK_HYPERVISOR_FEATURES = {
    'can_set_mount_point': False,
    'can_set_password': False,
    'enable_quotas': True,
    'requires_keypair': False,
}

# AngularJS requires some settings to be made available to
# the client side. Some settings are required by in-tree / built-in horizon
# features. These settings must be added to REST_API_REQUIRED_SETTINGS in the
# form of ['SETTING_1','SETTING_2'], etc.
#
# You may remove settings from this list for security purposes, but do so at
# the risk of breaking a built-in horizon feature. These settings are required
# for horizon to function properly. Only remove them if you know what you
# are doing. These settings may in the future be moved to be defined within
# the enabled panel configuration.
# You should not add settings to this list for out of tree extensions.
# See: https://wiki.openstack.org/wiki/Horizon/RESTAPI
REST_API_REQUIRED_SETTINGS = [
    'CREATE_IMAGE_DEFAULTS',
    'ENFORCE_PASSWORD_CHECK'
    'LAUNCH_INSTANCE_DEFAULTS',
    'OPENSTACK_HYPERVISOR_FEATURES',
    'OPENSTACK_IMAGE_FORMATS',
    'OPENSTACK_KEYSTONE_BACKEND',
    'OPENSTACK_KEYSTONE_DEFAULT_DOMAIN',
]
# Additional settings can be made available to the client side for
# extensibility by specifying them in REST_API_ADDITIONAL_SETTINGS
# !! Please use extreme caution as the settings are transferred via HTTP/S
# and are not encrypted on the browser. This is an experimental API and
# may be deprecated in the future without notice.
REST_API_ADDITIONAL_SETTINGS = []
