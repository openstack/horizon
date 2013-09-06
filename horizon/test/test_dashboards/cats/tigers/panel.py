import horizon

from horizon.test.test_dashboards.cats import dashboard


class Tigers(horizon.Panel):
    name = "Tigers"
    slug = "tigers"
    permissions = ("horizon.test",)


dashboard.Cats.register(Tigers)
