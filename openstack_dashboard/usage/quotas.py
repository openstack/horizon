# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from collections import defaultdict
import itertools
import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon.utils.memoized import memoized

from openstack_dashboard.api import base
from openstack_dashboard.api import cinder
from openstack_dashboard.api import neutron
from openstack_dashboard.api import nova
from openstack_dashboard.contrib.developer.profiler import api as profiler
from openstack_dashboard.utils import futurist_utils


LOG = logging.getLogger(__name__)


NOVA_COMPUTE_QUOTA_FIELDS = {
    "metadata_items",
    "cores",
    "instances",
    "injected_files",
    "injected_file_content_bytes",
    "injected_file_path_bytes",
    "ram",
    "key_pairs",
    "server_groups",
    "server_group_members",
}

# We no longer supports nova-network, so network related quotas from nova
# are not considered.
NOVA_QUOTA_FIELDS = NOVA_COMPUTE_QUOTA_FIELDS

NOVA_QUOTA_LIMIT_MAP = {
    'instances': {
        'limit': 'maxTotalInstances',
        'usage': 'totalInstancesUsed'
    },
    'cores': {
        'limit': 'maxTotalCores',
        'usage': 'totalCoresUsed'
    },
    'ram': {
        'limit': 'maxTotalRAMSize',
        'usage': 'totalRAMUsed'
    },
    'key_pairs': {
        'limit': 'maxTotalKeypairs',
        'usage': None
    },
}

CINDER_QUOTA_FIELDS = {"volumes",
                       "snapshots",
                       "gigabytes"}

CINDER_QUOTA_LIMIT_MAP = {
    'volumes': {'usage': 'totalVolumesUsed',
                'limit': 'maxTotalVolumes'},
    'gigabytes': {'usage': 'totalGigabytesUsed',
                  'limit': 'maxTotalVolumeGigabytes'},
    'snapshots': {'usage': 'totalSnapshotsUsed',
                  'limit': 'maxTotalSnapshots'},
}

NEUTRON_QUOTA_FIELDS = {"network",
                        "subnet",
                        "port",
                        "router",
                        "floatingip",
                        "security_group",
                        "security_group_rule",
                        }

QUOTA_FIELDS = NOVA_QUOTA_FIELDS | CINDER_QUOTA_FIELDS | NEUTRON_QUOTA_FIELDS

QUOTA_NAMES = {
    # nova
    "metadata_items": _('Metadata Items'),
    "cores": _('VCPUs'),
    "instances": _('Instances'),
    "injected_files": _('Injected Files'),
    "injected_file_content_bytes": _('Injected File Content Bytes'),
    "ram": _('RAM (MB)'),
    "key_pairs": _('Key Pairs'),
    "injected_file_path_bytes": _('Injected File Path Bytes'),
    # cinder
    "volumes": _('Volumes'),
    "snapshots": _('Volume Snapshots'),
    "gigabytes": _('Total Size of Volumes and Snapshots (GB)'),
    # neutron
    "network": _("Networks"),
    "subnet": _("Subnets"),
    "port": _("Ports"),
    "router": _("Routers"),
    "floatingip": _('Floating IPs'),
    "security_group": _("Security Groups"),
    "security_group_rule": _("Security Group Rules")
}


class QuotaUsage(dict):
    """Tracks quota limit, used, and available for a given set of quotas."""

    def __init__(self):
        self.usages = defaultdict(dict)

    def __contains__(self, key):
        return key in self.usages

    def __getitem__(self, key):
        return self.usages[key]

    def __setitem__(self, key, value):
        raise NotImplementedError("Directly setting QuotaUsage values is not "
                                  "supported. Please use the add_quota and "
                                  "tally methods.")

    def __repr__(self):
        return repr(dict(self.usages))

    def __bool__(self):
        return bool(self.usages)

    def get(self, key, default=None):
        return self.usages.get(key, default)

    def add_quota(self, quota):
        """Adds an internal tracking reference for the given quota."""
        if quota.limit in (None, -1, float('inf')):
            # Handle "unlimited" quotas.
            self.usages[quota.name]['quota'] = float("inf")
            self.usages[quota.name]['available'] = float("inf")
        else:
            self.usages[quota.name]['quota'] = int(quota.limit)

    def tally(self, name, value):
        """Adds to the "used" metric for the given quota."""
        value = value or 0  # Protection against None.
        # Start at 0 if this is the first value.
        if 'used' not in self.usages[name]:
            self.usages[name]['used'] = 0
        # Increment our usage and update the "available" metric.
        self.usages[name]['used'] += int(value)  # Fail if can't coerce to int.
        self.update_available(name)

    def update_available(self, name):
        """Updates the "available" metric for the given quota."""
        quota = self.usages.get(name, {}).get('quota', float('inf'))
        available = quota - self.usages[name]['used']
        if available < 0:
            available = 0
        self.usages[name]['available'] = available


@profiler.trace
def get_default_quota_data(request, disabled_quotas=None, tenant_id=None):
    quotasets = []
    if not tenant_id:
        tenant_id = request.user.tenant_id
    if disabled_quotas is None:
        disabled_quotas = get_disabled_quotas(request)

    if NOVA_QUOTA_FIELDS - disabled_quotas:
        quotasets.append(nova.default_quota_get(request, tenant_id))

    if CINDER_QUOTA_FIELDS - disabled_quotas:
        try:
            quotasets.append(cinder.default_quota_get(request, tenant_id))
        except cinder.cinder_exception.ClientException:
            disabled_quotas.update(CINDER_QUOTA_FIELDS)
            msg = _("Unable to retrieve volume quota information.")
            exceptions.handle(request, msg)

    if NEUTRON_QUOTA_FIELDS - disabled_quotas:
        try:
            quotasets.append(neutron.default_quota_get(request,
                                                       tenant_id=tenant_id))
        except Exception:
            disabled_quotas.update(NEUTRON_QUOTA_FIELDS)
            msg = _('Unable to retrieve Neutron quota information.')
            exceptions.handle(request, msg)

    qs = base.QuotaSet()
    for quota in itertools.chain(*quotasets):
        if quota.name not in disabled_quotas and quota.name in QUOTA_FIELDS:
            qs[quota.name] = quota.limit
    return qs


@profiler.trace
def get_tenant_quota_data(request, disabled_quotas=None, tenant_id=None):
    quotasets = []
    if not tenant_id:
        tenant_id = request.user.tenant_id
    if disabled_quotas is None:
        disabled_quotas = get_disabled_quotas(request)

    if NOVA_QUOTA_FIELDS - disabled_quotas:
        quotasets.append(nova.tenant_quota_get(request, tenant_id))

    if CINDER_QUOTA_FIELDS - disabled_quotas:
        try:
            quotasets.append(cinder.tenant_quota_get(request, tenant_id))
        except cinder.cinder_exception.ClientException:
            disabled_quotas.update(CINDER_QUOTA_FIELDS)
            msg = _("Unable to retrieve volume limit information.")
            exceptions.handle(request, msg)

    if NEUTRON_QUOTA_FIELDS - disabled_quotas:
        quotasets.append(neutron.tenant_quota_get(request, tenant_id))

    qs = base.QuotaSet()
    for quota in itertools.chain(*quotasets):
        if quota.name not in disabled_quotas and quota.name in QUOTA_FIELDS:
            qs[quota.name] = quota.limit
    return qs


# TOOD(amotoki): Do not use neutron specific quota field names.
# At now, quota names from nova-network are used in the dashboard code,
# but get_disabled_quotas() returns quota names from neutron API.
# It is confusing and makes the code complicated. They should be push away.
# Check Identity Project panel and System Defaults panel too.
@profiler.trace
def get_disabled_quotas(request, targets=None):
    if targets:
        candidates = set(targets)
    else:
        candidates = QUOTA_FIELDS

    # We no longer supports nova network, so we always disable
    # network related nova quota fields.
    disabled_quotas = set()

    # Cinder
    if candidates & CINDER_QUOTA_FIELDS:
        if not cinder.is_volume_service_enabled(request):
            disabled_quotas.update(CINDER_QUOTA_FIELDS)

    # Neutron
    if not (candidates & NEUTRON_QUOTA_FIELDS):
        pass
    elif not base.is_service_enabled(request, 'network'):
        disabled_quotas.update(NEUTRON_QUOTA_FIELDS)
    else:
        if ({'security_group', 'security_group_rule'} & candidates and
                not neutron.is_extension_supported(request, 'security-group')):
            disabled_quotas.update(['security_group', 'security_group_rule'])

        if ({'router', 'floatingip'} & candidates and
                not neutron.is_router_enabled(request)):
            disabled_quotas.update(['router', 'floatingip'])

        try:
            if not neutron.is_quotas_extension_supported(request):
                disabled_quotas.update(NEUTRON_QUOTA_FIELDS)
        except Exception:
            LOG.exception("There was an error checking if the Neutron "
                          "quotas extension is enabled.")

    # Nova
    if candidates & NOVA_QUOTA_FIELDS:
        if not (base.is_service_enabled(request, 'compute') and
                nova.can_set_quotas()):
            disabled_quotas.update(NOVA_QUOTA_FIELDS)

    enabled_quotas = candidates - disabled_quotas
    disabled_quotas = set(QUOTA_FIELDS) - enabled_quotas

    # There appear to be no glance quota fields currently
    return disabled_quotas


def _add_limit_and_usage(usages, name, limit, usage, disabled_quotas):
    if name not in disabled_quotas:
        usages.add_quota(base.Quota(name, limit))
        if usage is not None:
            usages.tally(name, usage)


def _add_limit_and_usage_neutron(usages, name, quota_name,
                                 detail, disabled_quotas):
    if quota_name in disabled_quotas:
        return
    usages.add_quota(base.Quota(name, detail['limit']))
    usages.tally(name, detail['used'] + detail['reserved'])


@profiler.trace
def _get_tenant_compute_usages(request, usages, disabled_quotas, tenant_id):
    enabled_compute_quotas = NOVA_COMPUTE_QUOTA_FIELDS - disabled_quotas
    if not enabled_compute_quotas:
        return

    if not base.is_service_enabled(request, 'compute'):
        return

    try:
        limits = nova.tenant_absolute_limits(request, reserved=True,
                                             tenant_id=tenant_id)
    except nova.nova_exceptions.ClientException:
        msg = _("Unable to retrieve compute limit information.")
        exceptions.handle(request, msg)

    for quota_name, limit_keys in NOVA_QUOTA_LIMIT_MAP.items():
        if limit_keys['usage']:
            usage = limits[limit_keys['usage']]
        else:
            usage = None
        _add_limit_and_usage(usages, quota_name,
                             limits[limit_keys['limit']],
                             usage,
                             disabled_quotas)


@profiler.trace
def _get_tenant_network_usages(request, usages, disabled_quotas, tenant_id):
    enabled_quotas = NEUTRON_QUOTA_FIELDS - disabled_quotas
    if not enabled_quotas:
        return

    if neutron.is_extension_supported(request, 'quota_details'):
        details = neutron.tenant_quota_detail_get(request, tenant_id)
        for quota_name in NEUTRON_QUOTA_FIELDS:
            if quota_name in disabled_quotas:
                continue
            detail = details[quota_name]
            usages.add_quota(base.Quota(quota_name, detail['limit']))
            usages.tally(quota_name, detail['used'] + detail['reserved'])
    else:
        _get_tenant_network_usages_legacy(
            request, usages, disabled_quotas, tenant_id)


def _get_neutron_quota_data(request, qs, disabled_quotas, tenant_id):
    tenant_id = tenant_id or request.user.tenant_id
    neutron_quotas = neutron.tenant_quota_get(request, tenant_id)

    for quota_name in NEUTRON_QUOTA_FIELDS:
        if quota_name not in disabled_quotas:
            quota_data = neutron_quotas.get(quota_name).limit
            qs.add(base.QuotaSet({quota_name: quota_data}))

    return qs


def _get_tenant_network_usages_legacy(request, usages, disabled_quotas,
                                      tenant_id):
    qs = base.QuotaSet()
    _get_neutron_quota_data(request, qs, disabled_quotas, tenant_id)
    for quota in qs:
        usages.add_quota(quota)

    resource_lister = {
        'network': (neutron.network_list, {'tenant_id': tenant_id}),
        'subnet': (neutron.subnet_list, {'tenant_id': tenant_id}),
        'port': (neutron.port_list, {'tenant_id': tenant_id}),
        'router': (neutron.router_list, {'tenant_id': tenant_id}),
        'floatingip': (neutron.tenant_floating_ip_list, {}),
    }

    for quota_name, lister_info in resource_lister.items():
        if quota_name not in disabled_quotas:
            lister = lister_info[0]
            kwargs = lister_info[1]
            try:
                resources = lister(request, **kwargs)
            except Exception:
                resources = []
            usages.tally(quota_name, len(resources))

    # Security groups have to be processed separately so that rules may be
    # processed in the same api call and in a single pass
    add_sg = 'security_group' not in disabled_quotas
    add_sgr = 'security_group_rule' not in disabled_quotas

    if add_sg or add_sgr:
        try:
            security_groups = neutron.security_group_list(request)
            num_rules = sum(len(group['security_group_rules'])
                            for group in security_groups)
        except Exception:
            security_groups = []
            num_rules = 0

    if add_sg:
        usages.tally('security_group', len(security_groups))

    if add_sgr:
        usages.tally('security_group_rule', num_rules)


@profiler.trace
def _get_tenant_volume_usages(request, usages, disabled_quotas, tenant_id):
    enabled_volume_quotas = CINDER_QUOTA_FIELDS - disabled_quotas
    if not enabled_volume_quotas:
        return

    try:
        limits = cinder.tenant_absolute_limits(request, tenant_id)
    except cinder.cinder_exception.ClientException:
        msg = _("Unable to retrieve volume limit information.")
        exceptions.handle(request, msg)

    for quota_name, limit_keys in CINDER_QUOTA_LIMIT_MAP.items():
        _add_limit_and_usage(usages, quota_name,
                             limits[limit_keys['limit']],
                             limits[limit_keys['usage']],
                             disabled_quotas)


@profiler.trace
@memoized
def tenant_quota_usages(request, tenant_id=None, targets=None):
    """Get our quotas and construct our usage object.

    :param tenant_id: Target tenant ID. If no tenant_id is provided,
        a the request.user.project_id is assumed to be used.
    :param targets: A tuple of quota names to be retrieved.
        If unspecified, all quota and usage information is retrieved.
    """
    if not tenant_id:
        tenant_id = request.user.project_id

    disabled_quotas = get_disabled_quotas(request, targets)
    usages = QuotaUsage()

    futurist_utils.call_functions_parallel(
        (_get_tenant_compute_usages,
         [request, usages, disabled_quotas, tenant_id]),
        (_get_tenant_network_usages,
         [request, usages, disabled_quotas, tenant_id]),
        (_get_tenant_volume_usages,
         [request, usages, disabled_quotas, tenant_id]))

    return usages


def enabled_quotas(request):
    """Returns the list of quotas available minus those that are disabled"""
    return QUOTA_FIELDS - get_disabled_quotas(request)
