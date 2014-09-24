from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.settings import dashboard


class Cancelaccount(horizon.Panel):
    name = _("Cancel Account")
    slug = "cancelaccount"


dashboard.Settings.register(Cancelaccount)
