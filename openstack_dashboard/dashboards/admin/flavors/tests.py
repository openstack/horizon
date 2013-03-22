from django import http
from django.core.urlresolvers import reverse
from mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test
from novaclient.v1_1 import flavors


class FlavorsTests(test.BaseAdminViewTests):
    @test.create_stubs({api.nova: ('flavor_list', 'flavor_create'), })
    def test_create_new_flavor_when_none_exist(self):
        flavor = self.flavors.first()
        eph = getattr(flavor, 'OS-FLV-EXT-DATA:ephemeral')

        # no pre-existing flavors
        api.nova.flavor_create(IsA(http.HttpRequest),
                               flavor.name,
                               flavor.ram,
                               flavor.vcpus,
                               flavor.disk,
                               swap=flavor.swap,
                               ephemeral=eph).AndReturn(flavor)
        api.nova.flavor_list(IsA(http.HttpRequest))
        self.mox.ReplayAll()

        url = reverse('horizon:admin:flavors:create')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "admin/flavors/create.html")

        data = {'name': flavor.name,
                'vcpus': flavor.vcpus,
                'memory_mb': flavor.ram,
                'disk_gb': flavor.disk,
                'swap_mb': flavor.swap,
                'eph_gb': eph}
        resp = self.client.post(url, data)
        self.assertRedirectsNoFollow(resp,
                                     reverse("horizon:admin:flavors:index"))

    # keeping the 2 edit tests separate to aid debug breaks
    @test.create_stubs({api.nova: ('flavor_list',
                                   'flavor_create',
                                   'flavor_delete',
                                   'flavor_get_extras',
                                   'flavor_get'), })
    def test_edit_flavor(self):
        flavor = self.flavors.first()  # has no extra specs
        eph = getattr(flavor, 'OS-FLV-EXT-DATA:ephemeral')
        extra_specs = getattr(flavor, 'extra_specs')
        new_flavor = flavors.Flavor(flavors.FlavorManager(None),
                                    {'id':
                                     "cccccccc-cccc-cccc-cccc-cccccccccccc",
                                     'name': flavor.name,
                                     'vcpus': flavor.vcpus + 1,
                                     'disk': flavor.disk,
                                     'ram': flavor.ram,
                                     'swap': 0,
                                     'OS-FLV-EXT-DATA:ephemeral': eph,
                                     'extra_specs': extra_specs})
        # GET
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)

        # POST
        api.nova.flavor_list(IsA(http.HttpRequest))
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)
        api.nova.flavor_get_extras(IsA(http.HttpRequest), flavor.id, raw=True)\
           .AndReturn(extra_specs)
        api.nova.flavor_delete(IsA(http.HttpRequest), flavor.id)
        api.nova.flavor_create(IsA(http.HttpRequest),
                               new_flavor.name,
                               new_flavor.ram,
                               new_flavor.vcpus,
                               new_flavor.disk,
                               swap=flavor.swap,
                               ephemeral=eph).AndReturn(new_flavor)
        self.mox.ReplayAll()

        # get_test
        url = reverse('horizon:admin:flavors:edit', args=[flavor.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "admin/flavors/edit.html")

        # post test
        data = {'flavor_id': flavor.id,
                'name': flavor.name,
                'vcpus': flavor.vcpus + 1,
                'memory_mb': flavor.ram,
                'disk_gb': flavor.disk,
                'swap_mb': flavor.swap,
                'eph_gb': eph}
        resp = self.client.post(url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp,
                                    reverse("horizon:admin:flavors:index"))

    @test.create_stubs({api.nova: ('flavor_list',
                                   'flavor_create',
                                   'flavor_delete',
                                   'flavor_get_extras',
                                   'flavor_extra_set',
                                   'flavor_get'), })
    def test_edit_flavor_with_extra_specs(self):
        flavor = self.flavors.list()[1]  # the second element has extra specs
        eph = getattr(flavor, 'OS-FLV-EXT-DATA:ephemeral')
        extra_specs = getattr(flavor, 'extra_specs')
        new_vcpus = flavor.vcpus + 1
        new_flavor = flavors.Flavor(flavors.FlavorManager(None),
                                    {'id':
                                     "cccccccc-cccc-cccc-cccc-cccccccccccc",
                                    'name': flavor.name,
                                    'vcpus': new_vcpus,
                                    'disk': flavor.disk,
                                    'ram': flavor.ram,
                                    'swap': flavor.swap,
                                    'OS-FLV-EXT-DATA:ephemeral': eph,
                                    'extra_specs': extra_specs})
        # GET
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)

        # POST
        api.nova.flavor_list(IsA(http.HttpRequest))
        api.nova.flavor_get(IsA(http.HttpRequest), flavor.id).AndReturn(flavor)
        api.nova.flavor_get_extras(IsA(http.HttpRequest), flavor.id, raw=True)\
           .AndReturn(extra_specs)
        api.nova.flavor_delete(IsA(http.HttpRequest), flavor.id)
        api.nova.flavor_create(IsA(http.HttpRequest),
                               flavor.name,
                               flavor.ram,
                               new_vcpus,
                               flavor.disk,
                               swap=flavor.swap,
                               ephemeral=eph).AndReturn(new_flavor)
        api.nova.flavor_extra_set(IsA(http.HttpRequest),
                                  new_flavor.id,
                                  extra_specs)
        self.mox.ReplayAll()

        #get_test
        url = reverse('horizon:admin:flavors:edit', args=[flavor.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "admin/flavors/edit.html")

        #post test
        data = {'flavor_id': flavor.id,
                'name': flavor.name,
                'vcpus': new_vcpus,
                'memory_mb': flavor.ram,
                'disk_gb': flavor.disk,
                'swap_mb': flavor.swap,
                'eph_gb': eph}
        resp = self.client.post(url, data)
        self.assertNoFormErrors(resp)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(resp,
                                    reverse("horizon:admin:flavors:index"))

    @test.create_stubs({api.nova: ('flavor_list',
                                   'flavor_get'), })
    def test_edit_flavor_set_invalid_name(self):
        flavor_a = self.flavors.list()[0]
        flavor_b = self.flavors.list()[1]
        eph = getattr(flavor_a, 'OS-FLV-EXT-DATA:ephemeral')
        invalid_flavor_name = "m1.tiny()"

        # GET
        api.nova.flavor_get(IsA(http.HttpRequest),
                            flavor_a.id).AndReturn(flavor_a)

        # POST
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.flavor_get(IsA(http.HttpRequest),
                            flavor_a.id).AndReturn(flavor_a)
        self.mox.ReplayAll()

        # get_test
        url = reverse('horizon:admin:flavors:edit', args=[flavor_a.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "admin/flavors/edit.html")

        # post test
        data = {'flavor_id': flavor_a.id,
                'name': invalid_flavor_name,
                'vcpus': flavor_a.vcpus + 1,
                'memory_mb': flavor_a.ram,
                'disk_gb': flavor_a.disk,
                'swap_mb': flavor_a.swap,
                'eph_gb': eph}
        resp = self.client.post(url, data)
        self.assertFormErrors(resp, 1, 'Name may only contain letters, '
                              'numbers, underscores, periods and hyphens.')

    @test.create_stubs({api.nova: ('flavor_list',
                                   'flavor_get'), })
    def test_edit_flavor_set_existing_name(self):
        flavor_a = self.flavors.list()[0]
        flavor_b = self.flavors.list()[1]
        eph = getattr(flavor_a, 'OS-FLV-EXT-DATA:ephemeral')

        # GET
        api.nova.flavor_get(IsA(http.HttpRequest),
                            flavor_a.id).AndReturn(flavor_a)

        # POST
        api.nova.flavor_list(IsA(http.HttpRequest)) \
            .AndReturn(self.flavors.list())
        api.nova.flavor_get(IsA(http.HttpRequest),
                            flavor_a.id).AndReturn(flavor_a)
        self.mox.ReplayAll()

        # get_test
        url = reverse('horizon:admin:flavors:edit', args=[flavor_a.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "admin/flavors/edit.html")

        # post test
        data = {'flavor_id': flavor_a.id,
                'name': flavor_b.name,
                'vcpus': flavor_a.vcpus + 1,
                'memory_mb': flavor_a.ram,
                'disk_gb': flavor_a.disk,
                'swap_mb': flavor_a.swap,
                'eph_gb': eph}
        resp = self.client.post(url, data)
        self.assertFormErrors(resp, 1, 'The name &quot;m1.massive&quot; '
                              'is already used by another flavor.')
