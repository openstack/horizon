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

# NOTE: The following are from Django settings.
# LOGIN_URL
# LOGIN_REDIRECT_URL
# SESSION_ENGINE
# USE_TZ

# WEBROOT is the location relative to Webserver root
# should end with a slash in openstack_dashboard.settings..
WEBROOT = '/'

# TODO(amotoki): What is the right default value in openstack_auth?
LOGIN_ERROR = 'error/'

OPENSTACK_KEYSTONE_URL = "http://localhost:5000/v3"
# OPENSTACK_KEYSTONE_URL = 'http://localhost/identity/v3'

# TODO(amotoki): The default value in openstack_dashboard is different:
# publicURL. It should be consistent.
OPENSTACK_ENDPOINT_TYPE = 'public'
OPENSTACK_SSL_NO_VERIFY = False
# TODO(amotoki): Is it correct?
OPENSTACK_SSL_CACERT = True
OPENSTACK_API_VERSIONS = {
    'identity': 3,
}

AUTHENTICATION_PLUGINS = ['openstack_auth.plugin.password.PasswordPlugin',
                          'openstack_auth.plugin.token.TokenPlugin']

# This SESSION_TIMEOUT is a method to supercede the token timeout with a
# shorter horizon session timeout (in seconds). If SESSION_REFRESH is True (the
# default) SESSION_TIMEOUT acts like an idle timeout rather than being a hard
# limit, but will never exceed the token expiry. If your token expires in 60
# minutes, a value of 1800 will log users out after 30 minutes of inactivity,
# or 60 minutes with activity. Setting SESSION_REFRESH to False will make
# SESSION_TIMEOUT act like a hard limit on session times.
SESSION_TIMEOUT = 3600

TOKEN_TIMEOUT_MARGIN = 0
AVAILABLE_REGIONS = []

# For setting the default service region on a per-endpoint basis. Note that the
# default value for this setting is {}, and below is just an example of how it
# should be specified.
# A key of '*' is an optional global default if no other key matches.
# Example:
# DEFAULT_SERVICE_REGIONS = {
#     '*': 'RegionOne'
#     OPENSTACK_KEYSTONE_URL: 'RegionTwo'
# }
DEFAULT_SERVICE_REGIONS = {}

SECURE_PROXY_ADDR_HEADER = False

# Password will have an expiration date when using keystone v3 and enabling
# the feature.
# This setting allows you to set the number of days that the user will be
# alerted prior to the password expiration.
# Once the password expires keystone will deny the access and users must
# contact an admin to change their password.
PASSWORD_EXPIRES_WARNING_THRESHOLD_DAYS = -1

# Horizon can prompt the user to change their password when it is expired
# or required to be changed on first use. This is enabled by default, but
# can be disabled if not desired.
ALLOW_USERS_CHANGE_EXPIRED_PASSWORD = True

OPENSTACK_KEYSTONE_ADMIN_ROLES = ['admin']
OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT = False
# Set this to True if you want available domains displayed as a dropdown menu
# on the login screen. It is strongly advised NOT to enable this for public
# clouds, as advertising enabled domains to unauthenticated customers
# irresponsibly exposes private information. This should only be used for
# private clouds where the dashboard sits behind a corporate firewall.
OPENSTACK_KEYSTONE_DOMAIN_DROPDOWN = False

# If OPENSTACK_KEYSTONE_DOMAIN_DROPDOWN is enabled, this option can be used to
# set the available domains to choose from. This is a list of pairs whose first
# value is the domain name and the second is the display name.
# Example:
# OPENSTACK_KEYSTONE_DOMAIN_CHOICES = (
#   ('Default', 'Default'),
# )
OPENSTACK_KEYSTONE_DOMAIN_CHOICES = ()
OPENSTACK_KEYSTONE_DEFAULT_DOMAIN = 'Default'

# Enables keystone web single-sign-on if set to True.
WEBSSO_ENABLED = False

# Authentication mechanism to be selected as default.
# The value must be a key from WEBSSO_CHOICES.
WEBSSO_INITIAL_CHOICE = 'credentials'

# The list of authentication mechanisms which include keystone
# federation protocols and identity provider/federation protocol
# mapping keys (WEBSSO_IDP_MAPPING). Current supported protocol
# IDs are 'saml2' and 'oidc'  which represent SAML 2.0, OpenID
# Connect respectively.
# Do not remove the mandatory credentials mechanism.
# Note: The last two tuples are sample mapping keys to a identity provider
# and federation protocol combination (WEBSSO_IDP_MAPPING).
# Example:
# WEBSSO_CHOICES = (
#     ("credentials", _("Keystone Credentials")),
#     ("oidc", _("OpenID Connect")),
#     ("saml2", _("Security Assertion Markup Language")),
#     ("acme_oidc", "ACME - OpenID Connect"),
#     ("acme_saml2", "ACME - SAML2"),
# )
WEBSSO_CHOICES = ()

# A dictionary of specific identity provider and federation protocol
# combinations. From the selected authentication mechanism, the value
# will be looked up as keys in the dictionary. If a match is found,
# it will redirect the user to a identity provider and federation protocol
# specific WebSSO endpoint in keystone, otherwise it will use the value
# as the protocol_id when redirecting to the WebSSO by protocol endpoint.
# NOTE: The value is expected to be a tuple formatted as:
# (<idp_id>, <protocol_id>).
# Example:
# WEBSSO_IDP_MAPPING = {
#     "acme_oidc": ("acme", "oidc"),
#     "acme_saml2": ("acme", "saml2"),
# }
WEBSSO_IDP_MAPPING = {}

# Enables redirection on login to the identity provider defined on
# WEBSSO_DEFAULT_REDIRECT_PROTOCOL and WEBSSO_DEFAULT_REDIRECT_REGION
WEBSSO_DEFAULT_REDIRECT = False

# Specifies the protocol to use for default redirection on login
WEBSSO_DEFAULT_REDIRECT_PROTOCOL = None

# Specifies the region to which the connection will be established on login
WEBSSO_DEFAULT_REDIRECT_REGION = OPENSTACK_KEYSTONE_URL

# Enables redirection on logout to the method specified on the identity
# provider. Once logout the client will be redirected to the address specified
# in this variable.
WEBSSO_DEFAULT_REDIRECT_LOGOUT = None

# If set this URL will be used for web single-sign-on authentication
# instead of OPENSTACK_KEYSTONE_URL. This is needed in the deployment
# scenarios where network segmentation is used per security requirement.
# In this case, the controllers are not reachable from public network.
# Therefore, user's browser will not be able to access OPENSTACK_KEYSTONE_URL
# if it is set to the internal endpoint.
# Example: WEBSSO_KEYSTONE_URL = "http://keystone-public.example.com/v3"
WEBSSO_KEYSTONE_URL = None

# The Keystone Provider drop down uses Keystone to Keystone federation
# to switch between Keystone service providers.
# Set display name for Identity Provider (dropdown display name)
KEYSTONE_PROVIDER_IDP_NAME = 'Local Keystone'
# This id is used for only for comparison with the service provider IDs.
# This ID should not match any service provider IDs.
KEYSTONE_PROVIDER_IDP_ID = 'localkeystone'

POLICY_FILES_PATH = ''
POLICY_FILES = {}
POLICY_DIRS = {}
