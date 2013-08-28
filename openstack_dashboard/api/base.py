# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from collections import Sequence  # noqa
import logging

from django.conf import settings  # noqa

from horizon import exceptions


__all__ = ('APIResourceWrapper', 'APIDictWrapper',
           'get_service_from_catalog', 'url_for',)


LOG = logging.getLogger(__name__)


class APIVersionManager(object):
    """ Object to store and manage API versioning data and utility methods. """

    SETTINGS_KEY = "OPENSTACK_API_VERSIONS"

    def __init__(self, service_type, preferred_version=None):
        self.service_type = service_type
        self.preferred = preferred_version
        self._active = None
        self.supported = {}

    @property
    def active(self):
        if self._active is None:
            self.get_active_version()
        return self._active

    def load_supported_version(self, version, data):
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
        self._active = key
        return self.supported[self._active]


class APIResourceWrapper(object):
    """ Simple wrapper for api objects

        Define _attrs on the child class and pass in the
        api object as the only argument to the constructor
    """
    _attrs = []

    def __init__(self, apiresource):
        self._apiresource = apiresource

    def __getattr__(self, attr):
        if attr in self._attrs:
            # __getattr__ won't find properties
            return self._apiresource.__getattribute__(attr)
        else:
            msg = ('Attempted to access unknown attribute "%s" on '
                   'APIResource object of type "%s" wrapping resource of '
                   'type "%s".') % (attr, self.__class__,
                                    self._apiresource.__class__)
            LOG.debug(exceptions.error_color(msg))
            raise AttributeError(attr)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                             dict((attr, getattr(self, attr))
                                  for attr in self._attrs
                                  if hasattr(self, attr)))


class APIDictWrapper(object):
    """ Simple wrapper for api dictionaries

        Some api calls return dictionaries.  This class provides identical
        behavior as APIResourceWrapper, except that it will also behave as a
        dictionary, in addition to attribute accesses.

        Attribute access is the preferred method of access, to be
        consistent with api resource objects from novaclient.
    """
    def __init__(self, apidict):
        self._apidict = apidict

    def __getattr__(self, attr):
        try:
            return self._apidict[attr]
        except KeyError:
            msg = 'Unknown attribute "%(attr)s" on APIResource object ' \
                  'of type "%(cls)s"' % {'attr': attr, 'cls': self.__class__}
            LOG.debug(exceptions.error_color(msg))
            raise AttributeError(msg)

    def __getitem__(self, item):
        try:
            return self.__getattr__(item)
        except AttributeError as e:
            # caller is expecting a KeyError
            raise KeyError(e)

    def get(self, item, default=None):
        try:
            return self.__getattr__(item)
        except AttributeError:
            return default

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self._apidict)


class Quota(object):
    """Wrapper for individual limits in a quota."""
    def __init__(self, name, limit):
        self.name = name
        self.limit = limit

    def __repr__(self):
        return "<Quota: (%s, %s)>" % (self.name, self.limit)


class QuotaSet(Sequence):
    """
    Wrapper for client QuotaSet objects which turns the individual quotas
    into Quota objects for easier handling/iteration.

    `QuotaSet` objects support a mix of `list` and `dict` methods; you can use
    the bracket notiation (`qs["my_quota"] = 0`) to add new quota values, and
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
        '''Merge another QuotaSet into this one. Existing quotas are
        not overriden.'''
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
            if service['type'] == service_type:
                return service
    return None


def get_version_from_service(service):
    if service:
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
    identity_version = get_version_from_service(service)
    for endpoint in service['endpoints']:
        # ignore region for identity
        if service['type'] == 'identity' or region == endpoint['region']:
            try:
                if identity_version < 3:
                    return endpoint[endpoint_type]
                else:
                    interface = \
                        ENDPOINT_TYPE_TO_INTERFACE.get(endpoint_type, '')
                    if endpoint['interface'] == interface:
                        return endpoint['url']
            except (IndexError, KeyError):
                return None
    return None


def url_for(request, service_type, endpoint_type=None):
    endpoint_type = endpoint_type or getattr(settings,
                                             'OPENSTACK_ENDPOINT_TYPE',
                                             'publicURL')
    fallback_endpoint_type = getattr(settings, 'SECONDARY_ENDPOINT_TYPE', None)

    catalog = request.user.service_catalog
    service = get_service_from_catalog(catalog, service_type)
    if service:
        url = get_url_for_service(service,
                                  request.user.services_region,
                                  endpoint_type)
        if not url and fallback_endpoint_type:
            url = get_url_for_service(service,
                                      request.user.services_region,
                                      fallback_endpoint_type)
        if url:
            return url
    raise exceptions.ServiceCatalogException(service_type)


def is_service_enabled(request, service_type, service_name=None):
    service = get_service_from_catalog(request.user.service_catalog,
                                       service_type)
    if service:
        region = request.user.services_region
        for endpoint in service['endpoints']:
            # ignore region for identity
            if service['type'] == 'identity' or \
               endpoint['region'] == region:
                if service_name:
                    return service['name'] == service_name
                else:
                    return True
    return False
