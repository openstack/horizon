from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.idm import dashboard


class Organizations(horizon.Panel):
    name = _("Organizations")
    slug = "organizations"


dashboard.Idm.register(Organizations)
