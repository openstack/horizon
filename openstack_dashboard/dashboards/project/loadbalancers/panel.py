from django.conf import settings  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

import horizon

from openstack_dashboard.dashboards.project import dashboard


class LoadBalancer(horizon.Panel):
    name = _("Load Balancers")
    slug = "loadbalancers"
    permissions = ('openstack.services.network',)


network_config = (
    getattr(settings, 'OPENSTACK_NEUTRON_NETWORK', {}) or
    getattr(settings, 'OPENSTACK_QUANTUM_NETWORK', {})
)

if network_config.get('enable_lb'):
    dashboard.Project.register(LoadBalancer)
