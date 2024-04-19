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

from django.conf import settings
from keystoneauth1 import adapter
from keystoneauth1 import identity
from keystoneauth1 import session

from openstack_dashboard.api import base

from horizon.utils.memoized import memoized


class Adapter(adapter.LegacyJsonAdapter):
    def __init__(self, *args, **kwargs):
        self.api_version = kwargs.pop('api_version', None)
        super().__init__(*args, **kwargs)

    def request(self, url, method, **kwargs):
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        if self.api_version is not None:
            kwargs['headers']['OpenStack-API-Version'] = self.api_version
        resp, body = super().request(url, method, **kwargs)
        return resp, body


@memoized
def make_adapter(request):
    auth = identity.Token(
        auth_url=base.url_for(request, 'identity'),
        token=request.user.token.id,
        project_id=request.user.project_id,
        project_name=request.user.project_name,
        project_domain_name=request.user.domain_id,
    )
    verify = True
    if settings.OPENSTACK_SSL_NO_VERIFY:
        verify = False
    elif settings.OPENSTACK_SSL_CACERT:
        verify = settings.OPENSTACK_SSL_CACERT
    return Adapter(
        session.Session(auth=auth, verify=verify),
        api_version="placement 1.6",
    )


def _get_json(request, path):
    adapter = make_adapter(request)
    uri = base.url_for(request, 'placement') + path
    response, body = adapter.get(uri)
    return response.json()


def get_versions(request):
    versions = _get_json(request, '/')
    return versions


def resource_providers(request):
    providers = _get_json(request, '/resource_providers')
    return providers['resource_providers']


def get_providers_uuids(request):
    providers = resource_providers(request)
    return [p['uuid'] for p in providers]


def resource_provider_inventories(request, uuid):
    return _get_json(
        request, f'/resource_providers/{uuid}/inventories')['inventories']


def resource_provider_usages(request, uuid):
    return _get_json(request, f'/resource_providers/{uuid}/usages')['usages']


def resource_provider_aggregates(request, uuid):
    return _get_json(
        request, f'/resource_providers/{uuid}/aggregates')['aggregates']


def resource_provider_traits(request, uuid):
    return _get_json(request, f'/resource_providers/{uuid}/traits')['traits']


def get_providers(request):
    providers = resource_providers(request)
    for p in providers:
        inventories = resource_provider_inventories(request, p['uuid'])
        usages = resource_provider_usages(request, p['uuid'])
        vcpus = inventories.get('VCPU')
        pcpus = inventories.get('PCPU')
        p['inventories'] = inventories
        p['usages'] = usages
        p['aggregates'] = resource_provider_aggregates(request, p['uuid'])
        p['traits'] = resource_provider_traits(request, p['uuid'])
        p['vcpus_used'] = usages.get('VCPU')
        p['vcpus_reserved'] = vcpus['reserved'] if vcpus is not None else None
        p['vcpus'] = vcpus['total'] if vcpus is not None else None
        p['pcpus_used'] = usages.get('PCPU')
        p['pcpus_reserved'] = pcpus['reserved'] if pcpus is not None else None
        p['pcpus'] = pcpus['total'] if pcpus is not None else None
        p['memory_mb_used'] = usages['MEMORY_MB']
        p['memory_mb_reserved'] = inventories['MEMORY_MB']['reserved']
        p['memory_mb'] = inventories['MEMORY_MB']['total']
        p['disk_gb_used'] = usages['DISK_GB']
        p['disk_gb_reserved'] = inventories['DISK_GB']['reserved']
        p['disk_gb'] = inventories['DISK_GB']['total']
    return providers
