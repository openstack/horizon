from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.idm_admin import dashboard


class Notify(horizon.Panel):
    name = _("Notify")
    slug = "notify"


dashboard.Idm_Admin.register(Notify)
