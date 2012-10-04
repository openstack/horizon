from django.utils.translation import ugettext_lazy as _

import horizon


class Dogs(horizon.Dashboard):
    name = _("Dogs")
    slug = "dogs"
    panels = ('puppies',)
    default_panel = 'puppies'


horizon.register(Dogs)
