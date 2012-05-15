from django.utils.translation import ugettext_lazy as _

import horizon

from horizon.tests.test_dashboards.cats import dashboard


class Tigers(horizon.Panel):
    name = _("Tigers")
    slug = "tigers"
    roles = ("admin",)


dashboard.Cats.register(Tigers)
