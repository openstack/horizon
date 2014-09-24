from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.settings import dashboard


class Useremail(horizon.Panel):
    name = _("email")
    slug = "useremail"

dashboard.Settings.register(Useremail)
