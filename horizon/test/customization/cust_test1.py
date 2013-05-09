from django.utils.translation import ugettext_lazy as _

import horizon

# Rename "cats" to "wildcats"
cats = horizon.get_dashboard("cats")
cats.name = _("WildCats")

# Disable tigers panel
tigers = cats.get_panel("tigers")
cats.unregister(tigers.__class__)

# Remove dogs dashboard
dogs = horizon.get_dashboard("dogs")
horizon.unregister(dogs.__class__)
