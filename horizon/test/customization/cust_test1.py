from django.utils.translation import ugettext_lazy as _  # noqa

import horizon
from horizon import base

# Rename "cats" to "wildcats", ignore if panel doesn't exist
try:
    cats = horizon.get_dashboard("cats")
    cats.name = _("WildCats")
except base.NotRegistered:
    cats = None

# Disable tigers panel, ignore if panel doesn't exist
if cats:
    try:
        tigers = cats.get_panel("tigers")
        cats.unregister(tigers.__class__)
    except base.NotRegistered:
        pass

# Remove dogs dashboard, ignore if dashboard doesn't exist
try:
    dogs = horizon.get_dashboard("dogs")
    horizon.unregister(dogs.__class__)
except base.NotRegistered:
    pass
