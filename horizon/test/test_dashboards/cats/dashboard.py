from django.utils.translation import ugettext_lazy as _

import horizon


class CuteGroup(horizon.PanelGroup):
    slug = "cute"
    name = _("Cute Cats")
    panels = ('kittens',)


class FierceGroup(horizon.PanelGroup):
    slug = "fierce"
    name = _("Fierce Cats")
    panels = ("tigers",)


class Cats(horizon.Dashboard):
    name = _("Cats")
    slug = "cats"
    panels = (CuteGroup, FierceGroup)
    default_panel = 'kittens'


horizon.register(Cats)
