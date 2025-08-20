from django.utils.translation import gettext_lazy as _
import horizon
from horizon import Panel


class Logging(Panel):
    name = _("Logging")
    slug = "logging"