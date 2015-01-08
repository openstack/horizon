from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.settings import dashboard


class Multisettings(horizon.Panel):
    name = _("Multisettings")
    slug = "multisettings"


dashboard.Settings.register(Multisettings)
