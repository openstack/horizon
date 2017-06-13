# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
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

from collections import Sequence
import functools

from django.conf import settings

from horizon import exceptions

import semantic_version
import six


__all__ = ('APIResourceWrapper', 'APIDictWrapper',
           'get_service_from_catalog', 'url_for',)


@functools.total_ordering
class Version(object):
    def __init__(self, version):
        self.version = semantic_version.Version(str(version), partial=True)

    def __eq__(self, other):
        return self.version == Version(other).version

    def __lt__(self, other):
        return self.version < Version(other).version

    def __repr__(self):
        return "Version('%s')" % self.version

    def __str__(self):
        return str(self.version)

    def __hash__(self):
        return hash(str(self.version))


class APIVersionManager(object):
    """Object to store and manage API versioning data and utility methods."""

    SETTINGS_KEY = "OPENSTACK_API_VERSIONS"

    def __init__(self, service_type, preferred_version=None):
        self.service_type = service_type
        self.preferred = preferred_version
        self._active = None
        self.supported = {}
        # As a convenience, we can drop in a placeholder for APIs that we
        # have not yet needed to version. This is useful, for example, when
        # panels such as the admin metadata_defs wants to check the active
        # version even though it's not explicitly defined. Previously
        # this caused a KeyError.
        if self.preferred:
            self.supported[self.preferred] = {"version": self.preferred}

    @property
    def active(self):
        if self._active is None:
            self.get_active_version()
        return self._active

    def load_supported_version(self, version, data):
        version = Version(version)
        self.supported[version] = data

    def get_active_version(self):
        if self._active is not None:
            return self.supported[self._active]
        key = getattr(settings, self.SETTINGS_KEY, {}).get(self.service_type)
        if key is None:
            # TODO(gabriel): support API version discovery here; we'll leave
            # the setting in as a way of overriding the latest available
            # version.
            key = self.preferred
        version = Version(key)
        # Provide a helpful error message if the specified version isn't in the
        # supported list.
        if version not in self.supported:
            choices = ", ".join(str(k) for k in six.iterkeys(self.supported))
            msg = ('%s is not a supported API version for the %s service, '
                   ' choices are: %s' % (version, self.service_type, choices))
            raise exceptions.ConfigurationError(msg)
        self._active = version
        return self.supported[self._active]

    def clear_active_cache(self):
        self._active = None


class APIResourceWrapper(object):
    """Simple wrapper for api objects.

    Define _attrs on the child class and pass in the
    api object as the only argument to the constructor
    """
    _attrs = []
    _apiresource = None  # Make sure _apiresource is there even in __init__.

    def __init__(self, apiresource):
        self._apiresource = apiresource

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            if attr not in self._attrs:
                raise
            # __getattr__ won't find properties
            return getattr(self._apiresource, attr)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                             dict((attr, getattr(self, attr))
                                  for attr in self._attrs
                                  if hasattr(self, attr)))

    def to_dict(self):
        obj = {}
        for key in self._attrs:
            obj[key] = getattr(self._apiresource, key, None)
        return obj


class APIDictWrapper(object):
    """Simple wrapper for api dictionaries

    Some api calls return dictionaries.  This class provides identical
    behavior as APIResourceWrapper, except that it will also behave as a
    dictionary, in addition to attribute accesses.

    Attribute access is the preferred method of access, to be
    consistent with api resource objects from novaclient.
    """

    _apidict = {}  # Make sure _apidict is there even in __init__.

    def __init__(self, apidict):
        self._apidict = apidict

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            if attr not in self._apidict:
                raise
            return self._apidict[attr]

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except (AttributeError, TypeError) as e:
            # caller is expecting a KeyError
            raise KeyError(e)

    def __contains__(self, item):
        try:
            return hasattr(self, item)
        except TypeError:
            return False

    def get(self, item, default=None):
        try:
            return getattr(self, item)
        except (AttributeError, TypeError):
            return default

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self._apidict)

    def to_dict(self):
        return self._apidict


class Quota(object):
    """Wrapper for individual limits in a quota."""
    def __init__(self, name, limit):
        self.name = name
        self.limit = limit

    def __repr__(self):
        return "<Quota: (%s, %s)>" % (self.name, self.limit)


class QuotaSet(Sequence):
    """Wrapper for client QuotaSet objects.

    This turns the individual quotas into Quota objects
    for easier handling/iteration.

    `QuotaSet` objects support a mix of `list` and `dict` methods; you can use
    the bracket notation (`qs["my_quota"] = 0`) to add new quota values, and
    use the `get` method to retrieve a specific quota, but otherwise it
    behaves much like a list or tuple, particularly in supporting iteration.
    """
    def __init__(self, apiresource=None):
        self.items = []
        if apiresource:
            if hasattr(apiresource, '_info'):
                items = apiresource._info.items()
            else:
                items = apiresource.items()

            for k, v in items:
                if k == 'id':
                    continue
                self[k] = v

    def __setitem__(self, k, v):
        v = int(v) if v is not None else v
        q = Quota(k, v)
        self.items.append(q)

    def __getitem__(self, index):
        return self.items[index]

    def __add__(self, other):
        """Merge another QuotaSet into this one.

        Existing quotas are not overridden.
        """
        if not isinstance(other, QuotaSet):
            msg = "Can only add QuotaSet to QuotaSet, " \
                  "but received %s instead" % type(other)
            raise ValueError(msg)

        for item in other:
            if self.get(item.name).limit is None:
                self.items.append(item)
        return self

    def __len__(self):
        return len(self.items)

    def __repr__(self):
        return repr(self.items)

    def get(self, key, default=None):
        match = [quota for quota in self.items if quota.name == key]
        return match.pop() if len(match) else Quota(key, default)

    def add(self, other):
        return self.__add__(other)


def get_service_from_catalog(catalog, service_type):
    if catalog:
        for service in catalog:
            if 'type' not in service:
                continue
            if service['type'] == service_type:
                return service
    return None


def get_version_from_service(service):
    if service and service.get('endpoints'):
        endpoint = service['endpoints'][0]
        if 'interface' in endpoint:
            return 3
        else:
            return 2.0
    return 2.0


# Mapping of V2 Catalog Endpoint_type to V3 Catalog Interfaces
ENDPOINT_TYPE_TO_INTERFACE = {
    'publicURL': 'public',
    'internalURL': 'internal',
    'adminURL': 'admin',
}


def get_url_for_service(service, region, endpoint_type):
    if 'type' not in service:
        return None

    identity_version = get_version_from_service(service)
    service_endpoints = service.get('endpoints', [])
    available_endpoints = [endpoint for endpoint in service_endpoints
                           if region == _get_endpoint_region(endpoint)]
    """if we are dealing with the identity service and there is no endpoint
    in the current region, it is okay to use the first endpoint for any
    identity service endpoints and we can assume that it is global
    """
    if service['type'] == 'identity' and not available_endpoints:
        available_endpoints = [endpoint for endpoint in service_endpoints]

    for endpoint in available_endpoints:
        try:
            if identity_version < 3:
                return endpoint.get(endpoint_type)
            else:
                interface = \
                    ENDPOINT_TYPE_TO_INTERFACE.get(endpoint_type, '')
                if endpoint.get('interface') == interface:
                    return endpoint.get('url')
        except (IndexError, KeyError):
            """it could be that the current endpoint just doesn't match the
            type, continue trying the next one
            """
            pass
    return None


def url_for(request, service_type, endpoint_type=None, region=None):
    endpoint_type = endpoint_type or getattr(settings,
                                             'OPENSTACK_ENDPOINT_TYPE',
                                             'publicURL')
    fallback_endpoint_type = getattr(settings, 'SECONDARY_ENDPOINT_TYPE', None)

    catalog = request.user.service_catalog
    service = get_service_from_catalog(catalog, service_type)
    if service:
        if not region:
            region = request.user.services_region
        url = get_url_for_service(service,
                                  region,
                                  endpoint_type)
        if not url and fallback_endpoint_type:
            url = get_url_for_service(service,
                                      region,
                                      fallback_endpoint_type)
        if url:
            return url
    raise exceptions.ServiceCatalogException(service_type)


def is_service_enabled(request, service_type):
    service = get_service_from_catalog(request.user.service_catalog,
                                       service_type)
    if service:
        region = request.user.services_region
        for endpoint in service.get('endpoints', []):
            if 'type' not in service:
                continue
            # ignore region for identity
            if service['type'] == 'identity' or \
               _get_endpoint_region(endpoint) == region:
                return True
    return False


def _get_endpoint_region(endpoint):
    """Common function for getting the region from endpoint.

    In Keystone V3, region has been deprecated in favor of
    region_id.

    This method provides a way to get region that works for
    both Keystone V2 and V3.
    """
    return endpoint.get('region_id') or endpoint.get('region')
