from django import http
from django.core.urlresolvers import reverse
from mox import IsA

from horizon import api
from horizon import test


class FlavorsTests(test.BaseAdminViewTests):
    def test_create_new_flavor_when_none_exist(self):
        flavor = self.flavors.first()
        eph = getattr(flavor, 'OS-FLV-EXT-DATA:ephemeral')
        self.mox.StubOutWithMock(api.nova, 'flavor_list')
        self.mox.StubOutWithMock(api.nova, 'flavor_create')

        # no pre-existing flavors
        api.nova.flavor_list(IsA(http.HttpRequest)).AndReturn([])
        api.nova.flavor_create(IsA(http.HttpRequest),
                               flavor.name,
                               flavor.ram,
                               flavor.vcpus,
                               flavor.disk,
                               1,  # Flavor id 1 because there are no others.
                               ephemeral=eph).AndReturn(flavor)
        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:flavors:create')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "syspanel/flavors/create.html")

        data = {'name': flavor.name,
                'vcpus': flavor.vcpus,
                'memory_mb': flavor.ram,
                'disk_gb': flavor.disk,
                'eph_gb': eph}
        resp = self.client.post(url, data)
        self.assertRedirectsNoFollow(resp,
                                     reverse("horizon:syspanel:flavors:index"))

    def test_edit_flavor(self):
        flavors = self.flavors.list()
        flavor = self.flavors.first()
        next_id = int(max(flavors, key=lambda f: f.id).id) + 1
        eph = getattr(flavor, 'OS-FLV-EXT-DATA:ephemeral')
        self.mox.StubOutWithMock(api.nova, 'flavor_list')
        self.mox.StubOutWithMock(api.nova, 'flavor_get')
        self.mox.StubOutWithMock(api.nova, 'flavor_delete')
        self.mox.StubOutWithMock(api.nova, 'flavor_create')

        # GET
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)

        # POST
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)
        api.nova.flavor_delete(IsA(http.HttpRequest), int(flavor.id))
        api.nova.flavor_list(IsA(http.HttpRequest)) \
                .AndReturn(flavors)
        api.nova.flavor_create(IsA(http.HttpRequest),
                               flavor.name,
                               flavor.ram,
                               flavor.vcpus + 1,
                               flavor.disk,
                               next_id,
                               ephemeral=eph).AndReturn(flavor)
        self.mox.ReplayAll()

        url = reverse('horizon:syspanel:flavors:edit', args=[flavor.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "syspanel/flavors/edit.html")

        data = {'flavor_id': flavor.id,
                'name': flavor.name,
                'vcpus': flavor.vcpus + 1,
                'memory_mb': flavor.ram,
                'disk_gb': flavor.disk,
                'eph_gb': eph}
        resp = self.client.post(url, data)
        self.assertRedirectsNoFollow(resp,
                                     reverse("horizon:syspanel:flavors:index"))
