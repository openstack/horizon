from django.utils.translation import ugettext_lazy as _

import horizon

from horizon.test.test_dashboards.cats import dashboard


class Tigers(horizon.Panel):
    name = _("Tigers")
    slug = "tigers"
    permissions = ("horizon.test",)


dashboard.Cats.register(Tigers)
