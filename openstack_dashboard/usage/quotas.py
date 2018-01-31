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
}

NOVA_NETWORK_QUOTA_FIELDS = {
    "floating_ips",
    "fixed_ips",
    "security_groups",
    "security_group_rules",
}

NOVA_QUOTA_FIELDS = NOVA_COMPUTE_QUOTA_FIELDS | NOVA_NETWORK_QUOTA_FIELDS

CINDER_QUOTA_FIELDS = {"volumes",
                       "snapshots",
                       "gigabytes"}

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
    "metadata_items": _('Metadata Items'),
    "cores": _('VCPUs'),
    "instances": _('Instances'),
    "injected_files": _('Injected Files'),
    "injected_file_content_bytes": _('Injected File Content Bytes'),
    "ram": _('RAM (MB)'),
    "floating_ips": _('Floating IPs'),
    "fixed_ips": _('Fixed IPs'),
    "security_groups": _('Security Groups'),
    "security_group_rules": _('Security Group Rules'),
    "key_pairs": _('Key Pairs'),
    "injected_file_path_bytes": _('Injected File Path Bytes'),
    "volumes": _('Volumes'),
    "snapshots": _('Volume Snapshots'),
    "gigabytes": _('Total Size of Volumes and Snapshots (GB)'),
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

    def get(self, key, default=None):
        return self.usages.get(key, default)

    def add_quota(self, quota):
        """Adds an internal tracking reference for the given quota."""
        if quota.limit is None or quota.limit == -1:
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


def _get_quota_data(request, tenant_mode=True, disabled_quotas=None,
                    tenant_id=None):
    quotasets = []
    if not tenant_id:
        tenant_id = request.user.tenant_id
    if disabled_quotas is None:
        disabled_quotas = get_disabled_quotas(request)

    qs = base.QuotaSet()

    if NOVA_QUOTA_FIELDS - disabled_quotas:
        if tenant_mode:
            quotasets.append(nova.tenant_quota_get(request, tenant_id))
        else:
            quotasets.append(nova.default_quota_get(request, tenant_id))

    if CINDER_QUOTA_FIELDS - disabled_quotas:
        try:
            if tenant_mode:
                quotasets.append(cinder.tenant_quota_get(request, tenant_id))
            else:
                quotasets.append(cinder.default_quota_get(request, tenant_id))
        except cinder.cinder_exception.ClientException:
            disabled_quotas.update(CINDER_QUOTA_FIELDS)
            msg = _("Unable to retrieve volume limit information.")
            exceptions.handle(request, msg)

    for quota in itertools.chain(*quotasets):
        if quota.name not in disabled_quotas:
            qs[quota.name] = quota.limit
    return qs


@profiler.trace
def get_default_quota_data(request, disabled_quotas=None, tenant_id=None):
    return _get_quota_data(request,
                           tenant_mode=False,
                           disabled_quotas=disabled_quotas,
                           tenant_id=tenant_id)


@profiler.trace
def get_tenant_quota_data(request, disabled_quotas=None, tenant_id=None):
    qs = _get_quota_data(request,
                         tenant_mode=True,
                         disabled_quotas=disabled_quotas,
                         tenant_id=tenant_id)

    # TODO(jpichon): There is no API to get the default system quotas
    # in Neutron (cf. LP#1204956), so for now handle tenant quotas here.
    # This should be handled in _get_quota_data() eventually.

    # TODO(amotoki): Purge this tricky usage.
    # openstack_dashboard/dashboards/identity/projects/views.py
    # calls get_tenant_quota_data directly and it expects
    # neutron data is not returned.
    if not disabled_quotas:
        return qs

    # Check if neutron is enabled by looking for network
    if not (NEUTRON_QUOTA_FIELDS - disabled_quotas):
        return qs

    tenant_id = tenant_id or request.user.tenant_id
    neutron_quotas = neutron.tenant_quota_get(request, tenant_id)

    if 'floating_ips' in disabled_quotas:
        if 'floatingip' not in disabled_quotas:
            # Rename floatingip to floating_ips since that's how it's
            # expected in some places (e.g. Security & Access' Floating IPs)
            fips_quota = neutron_quotas.get('floatingip').limit
            qs.add(base.QuotaSet({'floating_ips': fips_quota}))

    if 'security_groups' in disabled_quotas:
        if 'security_group' not in disabled_quotas:
            # Rename security_group to security_groups since that's how it's
            # expected in some places (e.g. Security & Access' Security Groups)
            sec_quota = neutron_quotas.get('security_group').limit
            qs.add(base.QuotaSet({'security_groups': sec_quota}))

    if 'network' in disabled_quotas:
        for item in qs.items:
            if item.name == 'networks':
                qs.items.remove(item)
                break
    else:
        net_quota = neutron_quotas.get('network').limit
        qs.add(base.QuotaSet({'networks': net_quota}))

    if 'subnet' in disabled_quotas:
        for item in qs.items:
            if item.name == 'subnets':
                qs.items.remove(item)
                break
    else:
        net_quota = neutron_quotas.get('subnet').limit
        qs.add(base.QuotaSet({'subnets': net_quota}))

    if 'router' in disabled_quotas:
        for item in qs.items:
            if item.name == 'routers':
                qs.items.remove(item)
                break
    else:
        router_quota = neutron_quotas.get('router').limit
        qs.add(base.QuotaSet({'routers': router_quota}))

    return qs


@profiler.trace
def get_disabled_quotas(request):
    disabled_quotas = set([])

    # Cinder
    if not cinder.is_volume_service_enabled(request):
        disabled_quotas.update(CINDER_QUOTA_FIELDS)

    # Neutron
    if not base.is_service_enabled(request, 'network'):
        disabled_quotas.update(NEUTRON_QUOTA_FIELDS)
    else:
        # Remove the nova network quotas
        disabled_quotas.update(['floating_ips', 'fixed_ips'])

        if neutron.is_extension_supported(request, 'security-group'):
            # If Neutron security group is supported, disable Nova quotas
            disabled_quotas.update(['security_groups', 'security_group_rules'])
        else:
            # If Nova security group is used, disable Neutron quotas
            disabled_quotas.update(['security_group', 'security_group_rule'])

        if not neutron.is_router_enabled(request):
            disabled_quotas.update(['router', 'floatingip'])

        try:
            if not neutron.is_quotas_extension_supported(request):
                disabled_quotas.update(NEUTRON_QUOTA_FIELDS)
        except Exception:
            LOG.exception("There was an error checking if the Neutron "
                          "quotas extension is enabled.")

    # Nova
    if not (base.is_service_enabled(request, 'compute') and
            nova.can_set_quotas()):
        disabled_quotas.update(NOVA_QUOTA_FIELDS)

    # There appear to be no glance quota fields currently
    return disabled_quotas


def _add_usage_if_quota_enabled(usage, name, value, disabled_quotas):
    if name in disabled_quotas:
        return
    usage.tally(name, value)


@profiler.trace
def _get_tenant_compute_usages(request, usages, disabled_quotas, tenant_id):
    enabled_compute_quotas = NOVA_COMPUTE_QUOTA_FIELDS - disabled_quotas
    if not enabled_compute_quotas:
        return

    # Unlike the other services it can be the case that nova is enabled but
    # doesn't support quotas, in which case we still want to get usage info,
    # so don't rely on '"instances" in disabled_quotas' as elsewhere
    if not base.is_service_enabled(request, 'compute'):
        return

    if tenant_id and tenant_id != request.user.project_id:
        # all_tenants is required when querying about any project the user is
        # not currently scoped to
        instances, has_more = nova.server_list(
            request, search_opts={'tenant_id': tenant_id, 'all_tenants': True})
    else:
        instances, has_more = nova.server_list(request)

    _add_usage_if_quota_enabled(usages, 'instances', len(instances),
                                disabled_quotas)

    if {'cores', 'ram'} - disabled_quotas:
        # Fetch deleted flavors if necessary.
        flavors = dict([(f.id, f) for f in nova.flavor_list(request)])
        missing_flavors = [instance.flavor['id'] for instance in instances
                           if instance.flavor['id'] not in flavors]
        for missing in missing_flavors:
            if missing not in flavors:
                try:
                    flavors[missing] = nova.flavor_get(request, missing)
                except Exception:
                    flavors[missing] = {}
                    exceptions.handle(request, ignore=True)

        # Sum our usage based on the flavors of the instances.
        for flavor in [flavors[instance.flavor['id']]
                       for instance in instances]:
            _add_usage_if_quota_enabled(
                usages, 'cores', getattr(flavor, 'vcpus', None),
                disabled_quotas)
            _add_usage_if_quota_enabled(
                usages, 'ram', getattr(flavor, 'ram', None),
                disabled_quotas)

        # Initialize the tally if no instances have been launched yet
        if len(instances) == 0:
            _add_usage_if_quota_enabled(usages, 'cores', 0, disabled_quotas)
            _add_usage_if_quota_enabled(usages, 'ram', 0, disabled_quotas)


@profiler.trace
def _get_tenant_network_usages(request, usages, disabled_quotas, tenant_id):
    enabled_quotas = ((NOVA_NETWORK_QUOTA_FIELDS | NEUTRON_QUOTA_FIELDS)
                      - disabled_quotas)
    if not enabled_quotas:
        return

    # NOTE(amotoki): floatingip is Neutron quota and floating_ips is
    # Nova quota. We need to check both.
    if {'floatingip', 'floating_ips'} & enabled_quotas:
        floating_ips = []
        try:
            if neutron.floating_ip_supported(request):
                floating_ips = neutron.tenant_floating_ip_list(request)
        except Exception:
            pass
        usages.tally('floating_ips', len(floating_ips))

    if 'security_group' not in disabled_quotas:
        security_groups = []
        security_groups = neutron.security_group_list(request)
        usages.tally('security_groups', len(security_groups))

    if 'network' not in disabled_quotas:
        networks = neutron.network_list(request, tenant_id=tenant_id)
        usages.tally('networks', len(networks))

    if 'subnet' not in disabled_quotas:
        subnets = neutron.subnet_list(request, tenant_id=tenant_id)
        usages.tally('subnets', len(subnets))

    if 'router' not in disabled_quotas:
        routers = neutron.router_list(request, tenant_id=tenant_id)
        usages.tally('routers', len(routers))


@profiler.trace
def _get_tenant_volume_usages(request, usages, disabled_quotas, tenant_id):
    if CINDER_QUOTA_FIELDS - disabled_quotas:
        try:
            if tenant_id:
                opts = {'all_tenants': 1, 'project_id': tenant_id}
                volumes = cinder.volume_list(request, opts)
                snapshots = cinder.volume_snapshot_list(request, opts)
            else:
                volumes = cinder.volume_list(request)
                snapshots = cinder.volume_snapshot_list(request)
            volume_usage = sum([int(v.size) for v in volumes])
            snapshot_usage = sum([int(s.size) for s in snapshots])
            _add_usage_if_quota_enabled(
                usages, 'gigabytes', (snapshot_usage + volume_usage),
                disabled_quotas)
            _add_usage_if_quota_enabled(
                usages, 'volumes', len(volumes), disabled_quotas)
            _add_usage_if_quota_enabled(
                usages, 'snapshots', len(snapshots), disabled_quotas)
        except cinder.cinder_exception.ClientException:
            msg = _("Unable to retrieve volume limit information.")
            exceptions.handle(request, msg)


NETWORK_QUOTA_API_KEY_MAP = {
    'floating_ips': ['floatingip', 'floating_ips'],
    'security_groups': ['security_group', 'security_groups'],
    'security_group_rules': ['security_group_rule', 'security_group_rules'],
    # Singular form key is used as quota field in the Neutron API.
    # We convert it explicitly here.
    # NOTE(amotoki): It is better to be converted in the horizon API wrapper
    # layer. Ideally the REST APIs of back-end services are consistent.
    'networks': ['network'],
    'subnets': ['subnet'],
    'ports': ['port'],
    'routers': ['router'],
}


def _convert_targets_to_quota_keys(targets):
    quota_keys = set()
    for target in targets:
        if target in NETWORK_QUOTA_API_KEY_MAP:
            quota_keys.update(NETWORK_QUOTA_API_KEY_MAP[target])
            continue
        if target in QUOTA_FIELDS:
            quota_keys.add(target)
            continue
        raise ValueError('"%s" is not a valid quota field name.' % target)
    return quota_keys


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

    disabled_quotas = get_disabled_quotas(request)
    usages = QuotaUsage()

    if targets:
        enabled_quotas = set(QUOTA_FIELDS) - disabled_quotas
        enabled_quotas &= _convert_targets_to_quota_keys(targets)
        disabled_quotas = set(QUOTA_FIELDS) - enabled_quotas

    for quota in get_tenant_quota_data(request,
                                       disabled_quotas=disabled_quotas,
                                       tenant_id=tenant_id):
        usages.add_quota(quota)

    # Get our usages.
    _get_tenant_compute_usages(request, usages, disabled_quotas, tenant_id)
    _get_tenant_network_usages(request, usages, disabled_quotas, tenant_id)
    _get_tenant_volume_usages(request, usages, disabled_quotas, tenant_id)

    return usages


@profiler.trace
def tenant_limit_usages(request):
    # TODO(licostan): This method shall be removed from Quota module.
    # ProjectUsage/BaseUsage maybe used instead on volume/image dashboards.
    limits = {}

    try:
        if base.is_service_enabled(request, 'compute'):
            limits.update(nova.tenant_absolute_limits(request, reserved=True))
    except Exception:
        msg = _("Unable to retrieve compute limit information.")
        exceptions.handle(request, msg)

    if cinder.is_volume_service_enabled(request):
        try:
            limits.update(cinder.tenant_absolute_limits(request))
        except cinder.cinder_exception.ClientException:
            msg = _("Unable to retrieve volume limit information.")
            exceptions.handle(request, msg)

    return limits


def enabled_quotas(request):
    """Returns the list of quotas available minus those that are disabled"""
    return QUOTA_FIELDS - get_disabled_quotas(request)
