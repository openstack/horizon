import horizon

from horizon.test.test_dashboards.cats import dashboard


class Kittens(horizon.Panel):
    name = "Kittens"
    slug = "kittens"
    permissions = ("horizon.test",)


dashboard.Cats.register(Kittens)
