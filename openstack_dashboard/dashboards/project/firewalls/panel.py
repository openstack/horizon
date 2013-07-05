from django.conf import settings  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

import horizon

from openstack_dashboard.dashboards.project import dashboard


class Firewall(horizon.Panel):
    name = _("Firewalls")
    slug = "firewalls"
    permissions = ('openstack.services.network',)


if getattr(settings,
           'OPENSTACK_NEUTRON_NETWORK',
           {}).get('enable_firewall', False):
    dashboard.Project.register(Firewall)
