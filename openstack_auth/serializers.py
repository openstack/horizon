# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import datetime
import json

from keystoneauth1.access import access
from keystoneauth1.access import service_catalog
from keystoneauth1.access import service_providers

from openstack_auth import user as auth_user


# The keys to identify serialized objects by.
TOKEN_KEYS = {'user', 'id', 'project', 'domain', 'roles', 'serviceCatalog'}
ACCESS_INFO_KEYS = {'_data', '_auth_token', '_service_catalog',
                    '_service_providers'}


def decode_datetime(data):
    return datetime.datetime.fromisoformat(data) if data else None


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        if o.__class__.__name__ == '__proxy__':
            return str(o)
        if isinstance(o, auth_user.Token):
            return o.__dict__
        if isinstance(o, access.AccessInfoV3):
            return o.__dict__
        if isinstance(o, service_catalog.ServiceCatalogV3):
            return o._catalog
        if isinstance(o, service_providers.ServiceProviders):
            return o._service_providers
        return super().default(o)


class JSONDecoder(json.JSONDecoder):
    def __init__(self, object_hook=None, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        if all(key in dct for key in TOKEN_KEYS):
            token = auth_user.Token()
            for key, value in dct.items():
                setattr(token, key, value)
            token.expires = decode_datetime(token.expires)
            token.user['password_expires_at'] = decode_datetime(
                token.user['password_expires_at'])
            return token
        if all(key in dct for key in ACCESS_INFO_KEYS):
            auth_info = access.AccessInfoV3(
                body=dct['_data'],
                auth_token=dct['_auth_token'],
            )
            for key, value in dct.items():
                setattr(auth_info, key, value)
            auth_info._service_catalog = service_catalog.ServiceCatalogV3(
                auth_info._service_catalog)
            providers = service_providers.ServiceProviders([])
            providers._service_providers = auth_info._service_providers
            auth_info._service_providers = providers
            return auth_info
        return dct


class HorizonSerializer:
    def dumps(self, obj):
        return json.dumps(
            obj, separators=(",", ":"), cls=JSONEncoder).encode("latin-1")

    def loads(self, data):
        return json.loads(data.decode("latin-1"), cls=JSONDecoder)
