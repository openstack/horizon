from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.idm import dashboard


class Home(horizon.Panel):
    name = _("Home")
    slug = "home"


dashboard.Idm.register(Home)
