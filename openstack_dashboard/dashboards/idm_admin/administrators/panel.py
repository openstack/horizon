from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.idm_admin import dashboard


class Administrators(horizon.Panel):
    name = _("Administrators")
    slug = "administrators"


dashboard.Idm_Admin.register(Administrators)
