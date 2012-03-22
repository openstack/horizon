from django import http
from django.core import urlresolvers
from mox import IsA

from horizon import api
from horizon.tests.base_tests import BaseHorizonTests


class FlavorsTests(BaseHorizonTests):
    def test_create_new_flavor_when_none_exist(self):
        # Set admin role
        self.setActiveUser(token=self.token.id,
                   username=self.user.name,
                   tenant_id=self.tenant.id,
                   service_catalog=self.request.user.service_catalog,
                   roles=[{'name': 'admin'}])

        self.mox.StubOutWithMock(api, 'flavor_list')
        # no pre-existing flavors
        api.flavor_list(IsA(http.HttpRequest)).AndReturn([])
        self.mox.ReplayAll()

        resp = self.client.get(
            urlresolvers.reverse('horizon:syspanel:flavors:create'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "syspanel/flavors/create.html")
