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
from openstack_dashboard.utils import settings as setting_utils


def _quota_exceeded(request, quota):
    usages = quotas.tenant_quota_usages(request, targets=(quota, ))
    available = usages.get(quota, {}).get('available', 1)
    return available <= 0


def get_context(request, context=None):
    """Returns common context data for network topology views."""
    if context is None:
        context = {}

    context['launch_instance_allowed'] = policy.check(
        (("compute", "os_compute_api:servers:create"),), request)
    context['instance_quota_exceeded'] = _quota_exceeded(request, 'instances')
    context['create_network_allowed'] = policy.check(
        (("network", "create_network"),), request)
    context['network_quota_exceeded'] = _quota_exceeded(request, 'network')
    context['create_router_allowed'] = (
        setting_utils.get_dict_config('OPENSTACK_NEUTRON_NETWORK',
                                      'enable_router') and
        policy.check((("network", "create_router"),), request))
    context['router_quota_exceeded'] = _quota_exceeded(request, 'router')
    context['console_type'] = settings.CONSOLE_TYPE
    context['show_ng_launch'] = (
        base.is_service_enabled(request, 'compute') and
        settings.LAUNCH_INSTANCE_NG_ENABLED)
    context['show_legacy_launch'] = (
        base.is_service_enabled(request, 'compute') and
        settings.LAUNCH_INSTANCE_LEGACY_ENABLED)
    return context
