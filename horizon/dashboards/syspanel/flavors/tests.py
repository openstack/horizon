from django import http
from django.core import urlresolvers
from mox import IsA

from horizon import api
from horizon import test


class FlavorsTests(test.BaseAdminViewTests):
    def test_create_new_flavor_when_none_exist(self):
        self.mox.StubOutWithMock(api, 'flavor_list')
        # no pre-existing flavors
        api.flavor_list(IsA(http.HttpRequest)).AndReturn([])
        self.mox.ReplayAll()

        resp = self.client.get(
            urlresolvers.reverse('horizon:syspanel:flavors:create'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "syspanel/flavors/create.html")
