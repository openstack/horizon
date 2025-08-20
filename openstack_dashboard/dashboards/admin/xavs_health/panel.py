# panel.py
from django.utils.translation import gettext_lazy as _
import horizon

class XAVSHealth(horizon.Panel):
    name = _("XAVS Health")
    slug = "xavs_health"
    permissions = ('openstack.roles.admin',)
