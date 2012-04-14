from django.utils.translation import ugettext_lazy as _

import horizon

from horizon.dashboards.syspanel import dashboard


class Volumes(horizon.Panel):
    name = _("Volumes")
    slug = "volumes"
    permissions = ('openstack.services.volume',)


dashboard.Syspanel.register(Volumes)
