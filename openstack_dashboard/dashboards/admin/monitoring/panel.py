from django.utils.translation import gettext_lazy as _
import horizon
from horizon import Panel


class Monitoring(horizon.Panel):
    name = _("Monitoring")
    slug = "monitoring"
    # optional: policy rules, e.g. policy_rules = (("compute", "compute_extension:admin_actions"),)

class Logging(Panel):
    name = _("Logging")
    slug = "logging"