from django.utils.translation import ugettext_lazy as _

import horizon


class Idm_Admin(horizon.Dashboard):
    name = _(" ")
    slug = "idm_admin"
    panels = ('notify',)  # Add your panels here.
    default_panel = 'notify'  # Specify the slug of the dashboard's default panel.


horizon.register(Idm_Admin)
