from collections import defaultdict
import itertools

from horizon import exceptions
from horizon.utils.memoized import memoized

from openstack_dashboard.api import nova, cinder, network
from openstack_dashboard.api.base import is_service_enabled, QuotaSet

NOVA_QUOTA_FIELDS = ("metadata_items",
                     "cores",
                     "instances",
                     "injected_files",
                     "injected_file_content_bytes",
                     "ram",
                     "floating_ips",
                     "fixed_ips",
                     "security_groups",
                     "security_group_rules",)

CINDER_QUOTA_FIELDS = ("volumes",
                       "gigabytes",)

QUOTA_FIELDS = NOVA_QUOTA_FIELDS + CINDER_QUOTA_FIELDS


class QuotaUsage(dict):
    """ Tracks quota limit, used, and available for a given set of quotas."""

    def __init__(self):
        self.usages = defaultdict(dict)

    def __getitem__(self, key):
        return self.usages[key]

    def __setitem__(self, key, value):
        raise NotImplemented("Directly setting QuotaUsage values is not "
                             "supported. Please use the add_quota and "
                             "tally methods.")

    def __repr__(self):
        return repr(dict(self.usages))

    def add_quota(self, quota):
        """ Adds an internal tracking reference for the given quota. """
        if quota.limit is None or quota.limit == -1:
            # Handle "unlimited" quotas.
            self.usages[quota.name]['quota'] = float("inf")
            self.usages[quota.name]['available'] = float("inf")
        else:
            self.usages[quota.name]['quota'] = int(quota.limit)

    def tally(self, name, value):
        """ Adds to the "used" metric for the given quota. """
        value = value or 0  # Protection against None.
        # Start at 0 if this is the first value.
        if 'used' not in self.usages[name]:
            self.usages[name]['used'] = 0
        # Increment our usage and update the "available" metric.
        self.usages[name]['used'] += int(value)  # Fail if can't coerce to int.
        self.update_available(name)

    def update_available(self, name):
        """ Updates the "available" metric for the given quota. """
        available = self.usages[name]['quota'] - self.usages[name]['used']
        if available < 0:
            available = 0
        self.usages[name]['available'] = available


def _get_quota_data(request, method_name, disabled_quotas=None,
                    tenant_id=None):
    quotasets = []
    if not tenant_id:
        tenant_id = request.user.tenant_id
    quotasets.append(getattr(nova, method_name)(request, tenant_id))
    qs = QuotaSet()
    if disabled_quotas is None:
        disabled_quotas = get_disabled_quotas(request)
    if 'volumes' not in disabled_quotas:
        quotasets.append(getattr(cinder, method_name)(request, tenant_id))
    for quota in itertools.chain(*quotasets):
        if quota.name not in disabled_quotas:
            qs[quota.name] = quota.limit
    return qs


def get_default_quota_data(request, disabled_quotas=None, tenant_id=None):
    return _get_quota_data(request,
                           "default_quota_get",
                           disabled_quotas=disabled_quotas,
                           tenant_id=tenant_id)


def get_tenant_quota_data(request, disabled_quotas=None, tenant_id=None):
    return _get_quota_data(request,
                           "tenant_quota_get",
                           disabled_quotas=disabled_quotas,
                           tenant_id=tenant_id)


def get_disabled_quotas(request):
    disabled_quotas = []
    if not is_service_enabled(request, 'volume'):
        disabled_quotas.extend(CINDER_QUOTA_FIELDS)
    return disabled_quotas


@memoized
def tenant_quota_usages(request):
    # Get our quotas and construct our usage object.
    disabled_quotas = get_disabled_quotas(request)

    usages = QuotaUsage()
    for quota in get_tenant_quota_data(request,
                                       disabled_quotas=disabled_quotas):
        usages.add_quota(quota)

    # Get our usages.
    floating_ips = network.tenant_floating_ip_list(request)
    flavors = dict([(f.id, f) for f in nova.flavor_list(request)])
    instances = nova.server_list(request)
    # Fetch deleted flavors if necessary.
    missing_flavors = [instance.flavor['id'] for instance in instances
                       if instance.flavor['id'] not in flavors]
    for missing in missing_flavors:
        if missing not in flavors:
            try:
                flavors[missing] = nova.flavor_get(request, missing)
            except:
                flavors[missing] = {}
                exceptions.handle(request, ignore=True)

    usages.tally('instances', len(instances))
    usages.tally('floating_ips', len(floating_ips))

    if 'volumes' not in disabled_quotas:
        volumes = cinder.volume_list(request)
        usages.tally('gigabytes', sum([int(v.size) for v in volumes]))
        usages.tally('volumes', len(volumes))

    # Sum our usage based on the flavors of the instances.
    for flavor in [flavors[instance.flavor['id']] for instance in instances]:
        usages.tally('cores', getattr(flavor, 'vcpus', None))
        usages.tally('ram', getattr(flavor, 'ram', None))

    # Initialise the tally if no instances have been launched yet
    if len(instances) == 0:
        usages.tally('cores', 0)
        usages.tally('ram', 0)

    return usages
