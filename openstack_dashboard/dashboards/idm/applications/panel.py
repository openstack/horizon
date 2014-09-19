from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.idm import dashboard


class Applications(horizon.Panel):
    name = _("Applications")
    slug = "applications"


dashboard.Idm.register(Applications)
