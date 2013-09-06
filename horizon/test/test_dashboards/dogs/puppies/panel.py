import horizon

from horizon.test.test_dashboards.dogs import dashboard


class Puppies(horizon.Panel):
    name = "Puppies"
    slug = "puppies"


dashboard.Dogs.register(Puppies)
