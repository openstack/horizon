from django.utils.translation import ugettext_lazy as _

import horizon


class Idm(horizon.Dashboard):
    name = _("Idm")
    slug = "idm"
    panels = ()  # Add your panels here.
    default_panel = ''  # Specify the slug of the dashboard's default panel.


horizon.register(Idm)
