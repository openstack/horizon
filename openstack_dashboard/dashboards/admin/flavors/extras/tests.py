from django import http
from django.core.urlresolvers import reverse

from mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class FlavorExtrasTests(test.BaseAdminViewTests):

    @test.create_stubs({api.nova: ('flavor_get_extras',
                                   'flavor_get'), })
    def test_list_extras_when_none_exists(self):
        flavor = self.flavors.first()
        extras = [api.nova.FlavorExtraSpec(flavor.id, 'k1', 'v1')]

        # GET -- to determine correctness of output
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)
        api.nova.flavor_get_extras(IsA(http.HttpRequest),
                                 flavor.id).AndReturn(extras)
        self.mox.ReplayAll()
        url = reverse('horizon:admin:flavors:extras:index', args=[flavor.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "admin/flavors/extras/index.html")

    @test.create_stubs({api.nova: ('flavor_extra_set', ), })
    def test_extra_create_post(self):
        flavor = self.flavors.first()
        create_url = reverse('horizon:admin:flavors:extras:create',
                             args=[flavor.id])
        index_url = reverse('horizon:admin:flavors:extras:index',
                            args=[flavor.id])

        # GET to display the flavor_name
        api.nova.flavor_extra_set(IsA(http.HttpRequest),
                                  flavor.id,
                                  {'k1': 'v1'})
        self.mox.ReplayAll()

        data = {'flavor_id': flavor.id,
                'key': 'k1',
                'value': 'v1'}
        resp = self.client.post(create_url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp, index_url)

    @test.create_stubs({api.nova: ('flavor_get', ), })
    def test_extra_create_get(self):
        flavor = self.flavors.first()
        create_url = reverse('horizon:admin:flavors:extras:create',
                             args=[flavor.id])

        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)
        self.mox.ReplayAll()

        resp = self.client.get(create_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp,
                                'admin/flavors/extras/create.html')
