from django.utils.translation import ugettext_lazy as _

import horizon

from horizon.tests.test_dashboards.cats import dashboard


class Kittens(horizon.Panel):
    name = _("Kittens")
    slug = "kittens"
    permissions = ("openstack.roles.admin",)


dashboard.Cats.register(Kittens)
