from django.utils.translation import ugettext_lazy as _

import horizon

from horizon.tests.test_dashboards.dogs import dashboard


class Puppies(horizon.Panel):
    name = _("Puppies")
    slug = "puppies"


dashboard.Dogs.register(Puppies)
