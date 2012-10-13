import uuid

from django import http
from django.core.urlresolvers import reverse
from mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class FlavorsTests(test.BaseAdminViewTests):
    def test_create_new_flavor_when_none_exist(self):
        flavor = self.flavors.first()
        eph = getattr(flavor, 'OS-FLV-EXT-DATA:ephemeral')
        self.mox.StubOutWithMock(api.nova, 'flavor_list')
        self.mox.StubOutWithMock(api.nova, 'flavor_create')

        # no pre-existing flavors
        api.nova.flavor_create(IsA(http.HttpRequest),
                               flavor.name,
                               flavor.ram,
                               flavor.vcpus,
                               flavor.disk,
                               IsA(uuid.uuid4()),
                               ephemeral=eph).AndReturn(flavor)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:flavors:create')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "admin/flavors/create.html")

        data = {'name': flavor.name,
                'vcpus': flavor.vcpus,
                'memory_mb': flavor.ram,
                'disk_gb': flavor.disk,
                'eph_gb': eph}
        resp = self.client.post(url, data)
        self.assertRedirectsNoFollow(resp,
                                     reverse("horizon:admin:flavors:index"))

    def test_edit_flavor(self):
        flavor = self.flavors.first()
        eph = getattr(flavor, 'OS-FLV-EXT-DATA:ephemeral')
        extras = {}
        self.mox.StubOutWithMock(api.nova, 'flavor_list')
        self.mox.StubOutWithMock(api.nova, 'flavor_get_extras')
        self.mox.StubOutWithMock(api.nova, 'flavor_get')
        self.mox.StubOutWithMock(api.nova, 'flavor_delete')
        self.mox.StubOutWithMock(api.nova, 'flavor_create')

        # GET
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)

        # POST
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)
        api.nova.flavor_get_extras(IsA(http.HttpRequest), int(flavor.id))\
           .AndReturn(extras)
        api.nova.flavor_delete(IsA(http.HttpRequest), int(flavor.id))
        api.nova.flavor_create(IsA(http.HttpRequest),
                               flavor.name,
                               flavor.ram,
                               flavor.vcpus + 1,
                               flavor.disk,
                               IsA(uuid.uuid4()),
                               ephemeral=eph).AndReturn(flavor)
        self.mox.ReplayAll()

        #get_test
        url = reverse('horizon:admin:flavors:edit', args=[flavor.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "admin/flavors/edit.html")

        #post test
        data = {'flavor_id': flavor.id,
                'name': flavor.name,
                'vcpus': flavor.vcpus + 1,
                'memory_mb': flavor.ram,
                'disk_gb': flavor.disk,
                'eph_gb': eph}
        resp = self.client.post(url, data)
        self.assertRedirectsNoFollow(resp,
                                    reverse("horizon:admin:flavors:index"))
