#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from django.conf import settings

from openstack_dashboard.api import base
from openstack_dashboard import policy
from openstack_dashboard.usage import quotas


def _quota_exceeded(request, quota):
    usages = quotas.tenant_quota_usages(request, targets=(quota, ))
    available = usages.get(quota, {}).get('available', 1)
    return available <= 0


def get_context(request, context=None):
    """Returns common context data for network topology views."""
    if context is None:
        context = {}

    network_config = getattr(settings, 'OPENSTACK_NEUTRON_NETWORK', {})

    context['launch_instance_allowed'] = policy.check(
        (("compute", "os_compute_api:servers:create"),), request)
    context['instance_quota_exceeded'] = _quota_exceeded(request, 'instances')
    context['create_network_allowed'] = policy.check(
        (("network", "create_network"),), request)
    context['network_quota_exceeded'] = _quota_exceeded(request, 'networks')
    context['create_router_allowed'] = (
        network_config.get('enable_router', True) and
        policy.check((("network", "create_router"),), request))
    context['router_quota_exceeded'] = _quota_exceeded(request, 'routers')
    context['console_type'] = getattr(settings, 'CONSOLE_TYPE', 'AUTO')
    context['show_ng_launch'] = (
        base.is_service_enabled(request, 'compute') and
        getattr(settings, 'LAUNCH_INSTANCE_NG_ENABLED', True))
    context['show_legacy_launch'] = (
        base.is_service_enabled(request, 'compute') and
        getattr(settings, 'LAUNCH_INSTANCE_LEGACY_ENABLED', False))
    return context
