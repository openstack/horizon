from django.utils.translation import ugettext_lazy as _

import horizon


class Idm(horizon.Dashboard):
    name = _("Identity Manager")
    slug = "idm"
    panels = ('home', 'organizations', 'myApplications', 'users')  # Add your panels here.
    default_panel = 'home'  # Specify the slug of the dashboard's default panel.


horizon.register(Idm)
