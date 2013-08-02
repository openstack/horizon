from django.utils.translation import ugettext_lazy as _  # noqa

import horizon

from horizon.test.test_dashboards.cats import dashboard


class Kittens(horizon.Panel):
    name = _("Kittens")
    slug = "kittens"
    permissions = ("horizon.test",)


dashboard.Cats.register(Kittens)
