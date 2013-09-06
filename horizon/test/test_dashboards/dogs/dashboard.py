import horizon


class Dogs(horizon.Dashboard):
    name = "Dogs"
    slug = "dogs"
    panels = ('puppies',)
    default_panel = 'puppies'


horizon.register(Dogs)
