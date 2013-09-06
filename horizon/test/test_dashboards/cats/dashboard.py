import horizon


class CuteGroup(horizon.PanelGroup):
    slug = "cute"
    name = "Cute Cats"
    panels = ('kittens',)


class FierceGroup(horizon.PanelGroup):
    slug = "fierce"
    name = "Fierce Cats"
    panels = ("tigers",)


class Cats(horizon.Dashboard):
    name = "Cats"
    slug = "cats"
    panels = (CuteGroup, FierceGroup)
    default_panel = 'kittens'


horizon.register(Cats)
