# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import logging
import re

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import models
from django.utils import timezone
from keystoneauth1.identity import v3 as v3_auth
from keystoneauth1 import session
from keystoneauth1 import token_endpoint
from keystoneclient.v3 import client as client_v3
from six.moves.urllib import parse as urlparse

from openstack_auth import defaults

LOG = logging.getLogger(__name__)

"""
We need the request object to get the user, so we'll slightly modify the
existing django.contrib.auth.get_user method. To do so we update the
auth middleware to point to our overridden method.

Calling "patch_middleware_get_user" is done in our custom middleware at
"openstack_auth.middleware" to monkeypatch the code in before it is needed.
"""


def middleware_get_user(request):
    if not hasattr(request, '_cached_user'):
        request._cached_user = get_user(request)
    return request._cached_user


def get_user(request):
    try:
        user_id = request.session[auth.SESSION_KEY]
        backend_path = request.session[auth.BACKEND_SESSION_KEY]
        backend = auth.load_backend(backend_path)
        backend.request = request
        user = backend.get_user(user_id) or models.AnonymousUser()
    except KeyError:
        user = models.AnonymousUser()
    return user


def patch_middleware_get_user():
    # NOTE(adriant): We can't import middleware until our customer user model
    # is actually registered, otherwise a call to get_user_model within the
    # middleware module will fail.
    from django.contrib.auth import middleware
    middleware.get_user = middleware_get_user
    auth.get_user = get_user


""" End Monkey-Patching. """


def is_token_valid(token, margin=None):
    """Timezone-aware checking of the auth token's expiration timestamp.

    Returns ``True`` if the token has not yet expired, otherwise ``False``.

    :param token: The openstack_auth.user.Token instance to check

    :param margin:
       A time margin in seconds to subtract from the real token's validity.
       An example usage is that the token can be valid once the middleware
       passed, and invalid (timed-out) during a view rendering and this
       generates authorization errors during the view rendering.
       A default margin can be set by the TOKEN_TIMEOUT_MARGIN in the
       django settings.
    """
    expiration = token.expires
    # In case we get an unparseable expiration timestamp, return False
    # so you can't have a "forever" token just by breaking the expires param.
    if expiration is None:
        return False
    if margin is None:
        margin = settings.TOKEN_TIMEOUT_MARGIN
    expiration = expiration - datetime.timedelta(seconds=margin)
    if settings.USE_TZ and timezone.is_naive(expiration):
        # Presumes that the Keystone is using UTC.
        expiration = timezone.make_aware(expiration, timezone.utc)
    return expiration > timezone.now()


# NOTE(amotoki):
# This is a copy from openstack_dashboard.utils.settings.get_dict_config().
# This copy is needed to look up defaults for openstack_auth.defaults
# instead of openstack_dashboard.defaults.
# TODO(amotoki): This copy might be cleanup if we can use oslo.config
# for openstack_auth configurations.
def _get_dict_config(name, key):
    config = getattr(settings, name)
    if key in config:
        return config[key]
    return getattr(defaults, name)[key]


# Helper for figuring out keystone version
# Implementation will change when API version discovery is available
def get_keystone_version():
    return _get_dict_config('OPENSTACK_API_VERSIONS', 'identity')


def get_session(**kwargs):
    insecure = settings.OPENSTACK_SSL_NO_VERIFY
    verify = settings.OPENSTACK_SSL_CACERT

    if insecure:
        verify = False

    return session.Session(verify=verify, **kwargs)


def get_keystone_client():
    return client_v3


def allow_expired_passowrd_change():
    """Checks if users should be able to change their expired passwords."""
    return getattr(settings, 'ALLOW_USERS_CHANGE_EXPIRED_PASSWORD', True)


def is_websso_enabled():
    """Websso is supported in Keystone version 3."""
    return settings.WEBSSO_ENABLED


def is_websso_default_redirect():
    """Checks if the websso default redirect is available.

    As with websso, this is only supported in Keystone version 3.
    """
    websso_default_redirect = settings.WEBSSO_DEFAULT_REDIRECT
    keystonev3_plus = (get_keystone_version() >= 3)
    return websso_default_redirect and keystonev3_plus


def get_websso_default_redirect_protocol():
    return settings.WEBSSO_DEFAULT_REDIRECT_PROTOCOL


def get_websso_default_redirect_region():
    return settings.WEBSSO_DEFAULT_REDIRECT_REGION


def get_websso_default_redirect_logout():
    return settings.WEBSSO_DEFAULT_REDIRECT_LOGOUT


def build_absolute_uri(request, relative_url):
    """Ensure absolute_uri are relative to WEBROOT."""
    webroot = settings.WEBROOT
    if webroot.endswith("/") and relative_url.startswith("/"):
        webroot = webroot[:-1]

    return request.build_absolute_uri(webroot + relative_url)


def get_websso_url(request, auth_url, websso_auth):
    """Return the keystone endpoint for initiating WebSSO.

    Generate the keystone WebSSO endpoint that will redirect the user
    to the login page of the federated identity provider.

    Based on the authentication type selected by the user in the login
    form, it will construct the keystone WebSSO endpoint.

    :param request: Django http request object.
    :type request: django.http.HttpRequest
    :param auth_url: Keystone endpoint configured in the horizon setting.
                     If WEBSSO_KEYSTONE_URL is defined, its value will be
                     used. Otherwise, the value is derived from:
                     - OPENSTACK_KEYSTONE_URL
                     - AVAILABLE_REGIONS
    :type auth_url: string
    :param websso_auth: Authentication type selected by the user from the
                        login form. The value is derived from the horizon
                        setting WEBSSO_CHOICES.
    :type websso_auth: string

    Example of horizon WebSSO setting::

        WEBSSO_CHOICES = (
            ("credentials", "Keystone Credentials"),
            ("oidc", "OpenID Connect"),
            ("saml2", "Security Assertion Markup Language"),
            ("acme_oidc", "ACME - OpenID Connect"),
            ("acme_saml2", "ACME - SAML2")
        )

        WEBSSO_IDP_MAPPING = {
            "acme_oidc": ("acme", "oidc"),
            "acme_saml2": ("acme", "saml2")
            }
        }

    The value of websso_auth will be looked up in the WEBSSO_IDP_MAPPING
    dictionary, if a match is found it will return a IdP specific WebSSO
    endpoint using the values found in the mapping.

    The value in WEBSSO_IDP_MAPPING is expected to be a tuple formatted as
    (<idp_id>, <protocol_id>). Using the values found, a IdP/protocol
    specific URL will be constructed::

        /auth/OS-FEDERATION/identity_providers/<idp_id>
        /protocols/<protocol_id>/websso

    If no value is found from the WEBSSO_IDP_MAPPING dictionary, it will
    treat the value as the global WebSSO protocol <protocol_id> and
    construct the WebSSO URL by::

        /auth/OS-FEDERATION/websso/<protocol_id>

    :returns: Keystone WebSSO endpoint.
    :rtype: string

    """
    origin = build_absolute_uri(request, '/auth/websso/')
    idp_mapping = settings.WEBSSO_IDP_MAPPING
    idp_id, protocol_id = idp_mapping.get(websso_auth,
                                          (None, websso_auth))

    if idp_id:
        # Use the IDP specific WebSSO endpoint
        url = ('%s/auth/OS-FEDERATION/identity_providers/%s'
               '/protocols/%s/websso?origin=%s' %
               (auth_url, idp_id, protocol_id, origin))
    else:
        # If no IDP mapping found for the identifier,
        # perform WebSSO by protocol.
        url = ('%s/auth/OS-FEDERATION/websso/%s?origin=%s' %
               (auth_url, protocol_id, origin))

    return url


def has_in_url_path(url, subs):
    """Test if any of `subs` strings is present in the `url` path."""
    scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
    return any([sub in path for sub in subs])


def url_path_replace(url, old, new, count=None):
    """Return a copy of url with replaced path.

    Return a copy of url with all occurrences of old replaced by new in the url
    path.  If the optional argument count is given, only the first count
    occurrences are replaced.
    """
    args = []
    scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
    if count is not None:
        args.append(count)
    return urlparse.urlunsplit((
        scheme, netloc, path.replace(old, new, *args), query, fragment))


def url_path_append(url, suffix):
    scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
    path = (path + suffix).replace('//', '/')
    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))


def _augment_url_with_version(auth_url):
    """Optionally augment auth_url path with version suffix.

    Check if path component already contains version suffix and if it does
    not, append version suffix to the end of path, not erasing the previous
    path contents, since keystone web endpoint (like /identity) could be
    there. Keystone version needs to be added to endpoint because as of Kilo,
    the identity URLs returned by Keystone might no longer contain API
    versions, leaving the version choice up to the user.
    """
    if has_in_url_path(auth_url, ["/v3"]):
        return auth_url

    return url_path_append(auth_url, "/v3")


def fix_auth_url_version_prefix(auth_url):
    """Fix up the auth url if an invalid or no version prefix was given.

    Fix the URL to say v3 in this case and add version if it is
    missing entirely. This should be smarter and use discovery.
    Until version discovery is implemented we need this method to get
    everything working.
    """
    auth_url = _augment_url_with_version(auth_url)

    url_fixed = False
    if has_in_url_path(auth_url, ["/v2.0"]):
        url_fixed = True
        auth_url = url_path_replace(auth_url, "/v2.0", "/v3", 1)

    return auth_url, url_fixed


def clean_up_auth_url(auth_url):
    """Clean up the auth url to extract the exact Keystone URL"""

    # NOTE(mnaser): This drops the query and fragment because we're only
    #               trying to extract the Keystone URL.
    scheme, netloc, path, query, fragment = urlparse.urlsplit(auth_url)
    return urlparse.urlunsplit((
        scheme, netloc, re.sub(r'/auth.*', '', path), '', ''))


def get_token_auth_plugin(auth_url, token, project_id=None, domain_name=None):
    if domain_name:
        return v3_auth.Token(auth_url=auth_url,
                             token=token,
                             domain_name=domain_name,
                             reauthenticate=False)
    else:
        return v3_auth.Token(auth_url=auth_url,
                             token=token,
                             project_id=project_id,
                             reauthenticate=False)


def get_project_list(*args, **kwargs):
    is_federated = kwargs.get('is_federated', False)
    sess = kwargs.get('session') or get_session()
    auth_url, _ = fix_auth_url_version_prefix(kwargs['auth_url'])
    auth = token_endpoint.Token(auth_url, kwargs['token'])
    client = get_keystone_client().Client(session=sess, auth=auth)

    if get_keystone_version() < 3:
        projects = client.tenants.list()
    elif is_federated:
        projects = client.federation.projects.list()
    else:
        projects = client.projects.list(user=kwargs.get('user_id'))

    projects.sort(key=lambda project: project.name.lower())
    return projects


def default_services_region(service_catalog, request=None,
                            ks_endpoint=None):
    """Return the default service region.

    Order of precedence:
    1. 'services_region' cookie value
    2. Matching endpoint in DEFAULT_SERVICE_REGIONS
    3. '*' key in DEFAULT_SERVICE_REGIONS
    4. First valid region from catalog

    In each case the value must also be present in available_regions or
    we move to the next level of precedence.
    """
    if service_catalog:
        available_regions = [get_endpoint_region(endpoint) for service
                             in service_catalog for endpoint
                             in service.get('endpoints', [])
                             if (service.get('type') is not None and
                                 service.get('type') != 'identity')]
        if not available_regions:
            # this is very likely an incomplete keystone setup
            LOG.warning('No regions could be found excluding identity.')
            available_regions = [get_endpoint_region(endpoint) for service
                                 in service_catalog for endpoint
                                 in service.get('endpoints', [])]

            if not available_regions:
                # if there are no region setup for any service endpoint,
                # this is a critical problem and it's not clear how this occurs
                LOG.error('No regions can be found in the service catalog.')
                return None

        region_options = []
        if request:
            region_options.append(request.COOKIES.get('services_region'))
        if ks_endpoint:
            default_service_regions = settings.DEFAULT_SERVICE_REGIONS
            region_options.append(default_service_regions.get(ks_endpoint))
        region_options.append(settings.DEFAULT_SERVICE_REGIONS.get('*'))

        for region in region_options:
            if region in available_regions:
                return region
        return available_regions[0]
    return None


def set_response_cookie(response, cookie_name, cookie_value):
    """Common function for setting the cookie in the response.

    Provides a common policy of setting cookies for last used project
    and region, can be reused in other locations.

    This method will set the cookie to expire in 365 days.
    """
    now = timezone.now()
    expire_date = now + datetime.timedelta(days=365)
    response.set_cookie(cookie_name, cookie_value, expires=expire_date)


def get_endpoint_region(endpoint):
    """Common function for getting the region from endpoint.

    In Keystone V3, region has been deprecated in favor of
    region_id.

    This method provides a way to get region that works for both
    Keystone V2 and V3.
    """
    return endpoint.get('region_id') or endpoint.get('region')


def using_cookie_backed_sessions():
    engine = settings.SESSION_ENGINE
    return "signed_cookies" in engine


def get_admin_roles():
    """Common function for getting the admin roles from settings

    :return:
      Set object including all admin roles.
      If there is no role, this will return empty::

        {
            "foo", "bar", "admin"
        }

    """
    admin_roles = {role.lower() for role
                   in settings.OPENSTACK_KEYSTONE_ADMIN_ROLES}
    return admin_roles


def get_role_permission(role):
    """Common function for getting the permission froms arg

    This format is 'openstack.roles.xxx' and 'xxx' is a real role name.

    :returns:
        String like "openstack.roles.admin"
        If role is None, this will return None.

    """
    return "openstack.roles.%s" % role.lower()


def get_admin_permissions():
    """Common function for getting the admin permissions from settings

    This format is 'openstack.roles.xxx' and 'xxx' is a real role name.

    :returns:
       Set object including all admin permission.
       If there is no permission, this will return empty::

        {
            "openstack.roles.foo",
            "openstack.roles.bar",
            "openstack.roles.admin"
        }

    """
    return {get_role_permission(role) for role in get_admin_roles()}


def get_client_ip(request):
    """Return client ip address using SECURE_PROXY_ADDR_HEADER variable.

    If not present or not defined on settings then REMOTE_ADDR is used.

    :param request: Django http request object.
    :type request: django.http.HttpRequest

    :returns: Possible client ip address
    :rtype: string
    """
    _SECURE_PROXY_ADDR_HEADER = settings.SECURE_PROXY_ADDR_HEADER
    if _SECURE_PROXY_ADDR_HEADER:
        return request.META.get(
            _SECURE_PROXY_ADDR_HEADER,
            request.META.get('REMOTE_ADDR')
        )
    return request.META.get('REMOTE_ADDR')


def store_initial_k2k_session(auth_url, request, scoped_auth_ref,
                              unscoped_auth_ref):
    """Stores session variables if there are k2k service providers

    This stores variables related to Keystone2Keystone federation. This
    function gets skipped if there are no Keystone service providers.
    An unscoped token to the identity provider keystone gets stored
    so that it can be used to do federated login into the service
    providers when switching keystone providers.
    The settings file can be configured to set the display name
    of the local (identity provider) keystone by setting
    KEYSTONE_PROVIDER_IDP_NAME. The KEYSTONE_PROVIDER_IDP_ID settings
    variable is used for comparison against the service providers.
    It should not conflict with any of the service provider ids.

    :param auth_url: base token auth url
    :param request: Django http request object
    :param scoped_auth_ref: Scoped Keystone access info object
    :param unscoped_auth_ref: Unscoped Keystone access info object
    """
    keystone_provider_id = request.session.get('keystone_provider_id', None)
    if keystone_provider_id:
        return None

    providers = getattr(scoped_auth_ref, 'service_providers', None)
    if providers:
        providers = getattr(providers, '_service_providers', None)

    if providers:
        keystone_idp_name = settings.KEYSTONE_PROVIDER_IDP_NAME
        keystone_idp_id = settings.KEYSTONE_PROVIDER_IDP_ID
        keystone_identity_provider = {'name': keystone_idp_name,
                                      'id': keystone_idp_id}
        # (edtubill) We will use the IDs as the display names
        # We may want to be able to set display names in the future.
        keystone_providers = [
            {'name': provider_id, 'id': provider_id}
            for provider_id in providers]

        keystone_providers.append(keystone_identity_provider)

        # We treat the Keystone idp ID as None
        request.session['keystone_provider_id'] = keystone_idp_id
        request.session['keystone_providers'] = keystone_providers
        request.session['k2k_base_unscoped_token'] =\
            unscoped_auth_ref.auth_token
        request.session['k2k_auth_url'] = auth_url
