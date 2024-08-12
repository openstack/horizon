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
        memory = inventories.get('MEMORY_MB')
        disk = inventories.get('DISK_GB')
        p['inventories'] = inventories
        p['usages'] = usages
        p['aggregates'] = resource_provider_aggregates(request, p['uuid'])
        p['traits'] = resource_provider_traits(request, p['uuid'])

        p['vcpus_used'] = usages.get('VCPU')
        # Reserved:
        # The actual amount of the resource that the provider can accommodate
        # Total:
        # Overall capacity
        if vcpus is not None:
            p.update(vcpus_reserved=vcpus['reserved'],
                     vcpus=vcpus['total'],
                     vcpus_ar=vcpus['allocation_ratio'],
                     vcpus_capacity=int(p['vcpus_ar'] * p['vcpus']))
        else:
            p.update(vcpus_reserved=None, vcpus=None,
                     vcpus_ar=None, vcpus_capacity=None)

        p['pcpus_used'] = usages.get('PCPU')
        if pcpus is not None:
            p.update(pcpus_reserved=pcpus['reserved'],
                     pcpus=pcpus['total'],
                     pcpus_ar=pcpus['allocation_ratio'],
                     pcpus_capacity=int(p['pcpus_ar'] * p['pcpus']))
        else:
            p.update(pcpus_reserved=None, pcpus=None,
                     pcpus_ar=None, pcpus_capacity=None)

        p['memory_mb_used'] = usages.get('MEMORY_MB')
        if memory is not None:
            p.update(memory_mb_reserved=memory['reserved'],
                     memory_mb=memory['total'],
                     memory_mb_ar=memory['allocation_ratio'],
                     memory_mb_capacity=p['memory_mb_ar'] * p['memory_mb'])
        else:
            p.update(memory_mb_reserved=None, memory_mb=None,
                     memory_mb_ar=None, memory_mb_capacity=None)

        p['disk_gb_used'] = usages.get('DISK_GB')
        if disk is not None:
            p.update(disk_gb_reserved=disk['reserved'],
                     disk_gb=disk['total'],
                     disk_gb_ar=disk['allocation_ratio'],
                     disk_gb_capacity=p['disk_gb_ar'] * p['disk_gb'])
        else:
            p.update(disk_gb_reserved=None, disk_gb=None,
                     disk_gb_ar=None, disk_gb_capacity=None)

    return providers
