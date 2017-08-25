# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from collections import OrderedDict

import uuid

import mock

from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:admin:instances:index')
INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'


class InstanceViewTest(test.BaseAdminViewTests):
    @test.create_mocks({
        api.nova: ['flavor_list', 'server_list_paged', 'extension_supported'],
        api.keystone: ['tenant_list'],
        api.glance: ['image_list_detailed_by_ids'],
    })
    def test_index(self):
        servers = self.servers.list()
        # TODO(vmarkov) instances_img_ids should be in test_data
        instances_img_ids = [instance.image.get('id') for instance in
                             servers if isinstance(instance.image, dict)]
        self.mock_extension_supported.return_value = True
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_image_list_detailed_by_ids.return_value = self.images.list()
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_server_list_paged.return_value = [servers, False, False]

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        instances = res.context['table'].data
        self.assertItemsEqual(instances, servers)

        self.mock_extension_supported.assert_has_calls([
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('Shelve', test.IsHttpRequest())] * 4)
        self.assertEqual(12, self.mock_extension_supported.call_count)
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_image_list_detailed_by_ids.assert_called_once_with(
            test.IsHttpRequest(), instances_img_ids)
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest())
        search_opts = {'marker': None, 'paginate': True, 'all_tenants': True}
        self.mock_server_list_paged.assert_called_once_with(
            test.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)

    @test.create_mocks({
        api.nova: ['flavor_list', 'flavor_get', 'server_list_paged',
                   'extension_supported'],
        api.keystone: ['tenant_list'],
        api.glance: ['image_list_detailed_by_ids'],
    })
    def test_index_flavor_list_exception(self):
        servers = self.servers.list()
        flavors = self.flavors.list()
        instances_img_ids = [instance.image.get('id') for instance in
                             servers if hasattr(instance, 'image')]
        full_flavors = OrderedDict([(f.id, f) for f in flavors])
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_extension_supported.return_value = True
        self.mock_flavor_list.side_effect = self.exceptions.nova
        self.mock_tenant_list.return_value = [self.tenants.list(), False]

        def _get_full_flavor(request, id):
            return full_flavors[id]
        self.mock_flavor_get.side_effect = _get_full_flavor

        self.mock_image_list_detailed_by_ids.return_value = self.images.list()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        instances = res.context['table'].data
        self.assertItemsEqual(instances, servers)

        search_opts = {'marker': None, 'paginate': True, 'all_tenants': True}
        self.mock_server_list_paged.assert_called_once_with(
            test.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_extension_supported.assert_has_calls([
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('Shelve', test.IsHttpRequest())] * 4)
        self.assertEqual(12, self.mock_extension_supported.call_count)
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_flavor_get.assert_has_calls(
            [mock.call(test.IsHttpRequest(), s.flavor['id']) for s in servers])
        self.assertEqual(len(servers), self.mock_flavor_get.call_count)
        self.mock_image_list_detailed_by_ids.assert_called_once_with(
            test.IsHttpRequest(), instances_img_ids)

    @test.create_mocks({
        api.nova: ['flavor_list', 'flavor_get', 'server_list_paged',
                   'extension_supported'],
        api.keystone: ['tenant_list'],
        api.glance: ['image_list_detailed_by_ids'],
    })
    def test_index_flavor_get_exception(self):
        servers = self.servers.list()
        instances_img_ids = [instance.image.get('id') for instance in
                             servers if hasattr(instance, 'image')]
        # UUIDs generated using indexes are unlikely to match
        # any of existing flavor ids and are guaranteed to be deterministic.
        for i, server in enumerate(servers):
            server.flavor['id'] = str(uuid.UUID(int=i))

        self.mock_image_list_detailed_by_ids.return_value = self.images.list()
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_extension_supported.return_value = True
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_flavor_get.side_effect = self.exceptions.nova

        res = self.client.get(INDEX_URL)
        instances = res.context['table'].data
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        # Since error messages produced for each instance are identical,
        # there will be only one error message for all instances
        # (messages de-duplication).
        self.assertMessageCount(res, error=1)
        self.assertItemsEqual(instances, servers)

        self.mock_image_list_detailed_by_ids.assert_called_once_with(
            test.IsHttpRequest(), instances_img_ids)
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest())
        search_opts = {'marker': None, 'paginate': True, 'all_tenants': True}
        self.mock_server_list_paged.assert_called_once_with(
            test.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_extension_supported.assert_has_calls([
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('Shelve', test.IsHttpRequest())] * 4)
        self.assertEqual(12, self.mock_extension_supported.call_count)
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_flavor_get.assert_has_calls(
            [mock.call(test.IsHttpRequest(), s.flavor['id']) for s in servers])
        self.assertEqual(len(servers), self.mock_flavor_get.call_count)

    @test.create_mocks({
        api.nova: ['server_list_paged', 'flavor_list'],
        api.keystone: ['tenant_list'],
        api.glance: ['image_list_detailed_by_ids'],
    })
    def test_index_server_list_exception(self):
        self.mock_server_list_paged.side_effect = self.exceptions.nova
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_image_list_detailed_by_ids.return_value = self.images.list()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertEqual(len(res.context['instances_table'].data), 0)

        search_opts = {'marker': None, 'paginate': True, 'all_tenants': True}
        self.mock_server_list_paged.assert_called_once_with(
            test.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_image_list_detailed_by_ids.assert_called_once_with(
            test.IsHttpRequest(), [])
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({api.nova: ['server_get', 'flavor_get',
                                   'extension_supported'],
                        api.network: ['servers_update_addresses'],
                        api.keystone: ['tenant_get']})
    def test_ajax_loading_instances(self):
        server = self.servers.first()
        self.mock_server_get.return_value = server
        self.mock_extension_supported.return_value = True
        self.mock_flavor_get.return_value = self.flavors.first()
        self.mock_tenant_get.return_value = self.tenants.first()
        self.mock_servers_update_addresses.return_value = None

        url = (INDEX_URL +
               "?action=row_update&table=instances&obj_id=" + server.id)

        res = self.client.get(url, {},
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertTemplateUsed(res, "horizon/common/_data_table_row.html")
        self.assertContains(res, "test_tenant", 1, 200)
        self.assertContains(res, "instance-host", 1, 200)
        # two instances of name, other name comes from row data-display
        self.assertContains(res, "server_1", 2, 200)
        self.assertContains(res, "10.0.0.1", 1, 200)
        self.assertContains(res, "RAM</th><td>512MB", 1, 200)
        self.assertContains(res, "VCPUs</th><td>1", 1, 200)
        self.assertContains(res, "Size</th><td>0 GB", 1, 200)
        self.assertContains(res, "Active", 1, 200)
        self.assertContains(res, "Running", 1, 200)

        self.mock_server_get.assert_called_once_with(
            test.IsHttpRequest(), server.id)
        self.mock_extension_supported.assert_has_calls([
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('Shelve', test.IsHttpRequest())])
        self.assertEqual(3, self.mock_extension_supported.call_count)
        self.mock_flavor_get.assert_called_once_with(
            test.IsHttpRequest(), server.flavor['id'])
        self.mock_tenant_get.assert_called_once_with(
            test.IsHttpRequest(), server.tenant_id, admin=True)
        self.mock_servers_update_addresses.assert_called_once_with(
            test.IsHttpRequest(), [server])

    @test.create_mocks({
        api.nova: ['flavor_list', 'server_list_paged', 'extension_supported'],
        api.keystone: ['tenant_list'],
        api.glance: ['image_list_detailed_by_ids'],
    })
    def test_index_options_before_migrate(self):
        servers = self.servers.list()
        instances_img_ids = [instance.image.get('id') for instance in
                             servers if hasattr(instance, 'image')]
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_image_list_detailed_by_ids.return_value = self.images.list()
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_server_list_paged.return_value = [
            self.servers.list(), False, False]
        self.mock_extension_supported.return_value = True
        res = self.client.get(INDEX_URL)
        self.assertContains(res, "instances__migrate")
        self.assertNotContains(res, "instances__confirm")
        self.assertNotContains(res, "instances__revert")

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_image_list_detailed_by_ids.assert_called_once_with(
            test.IsHttpRequest(), instances_img_ids)
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest())
        search_opts = {'marker': None, 'paginate': True, 'all_tenants': True}
        self.mock_server_list_paged.assert_called_once_with(
            test.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_extension_supported.assert_has_calls([
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('Shelve', test.IsHttpRequest())] * 4)
        self.assertEqual(12, self.mock_extension_supported.call_count)

    @test.create_mocks({
        api.nova: ['flavor_list', 'server_list_paged', 'extension_supported'],
        api.keystone: ['tenant_list'],
        api.glance: ['image_list_detailed_by_ids'],
    })
    def test_index_options_after_migrate(self):
        servers = self.servers.list()
        server1 = servers[0]
        server1.status = "VERIFY_RESIZE"
        server2 = servers[2]
        server2.status = "VERIFY_RESIZE"
        instances_img_ids = [instance.image.get('id') for instance in
                             servers if hasattr(instance, 'image')]
        self.mock_tenant_list.return_value = [self.tenants.list(), False]
        self.mock_image_list_detailed_by_ids.return_value = self.images.list()
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_extension_supported.return_value = True
        self.mock_server_list_paged.return_value = [servers, False, False]

        res = self.client.get(INDEX_URL)
        self.assertContains(res, "instances__confirm")
        self.assertContains(res, "instances__revert")
        self.assertNotContains(res, "instances__migrate")

        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_image_list_detailed_by_ids.assert_called_once_with(
            test.IsHttpRequest(), instances_img_ids)
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_extension_supported.assert_has_calls([
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('Shelve', test.IsHttpRequest())] * 4)
        self.assertEqual(12, self.mock_extension_supported.call_count)
        search_opts = {'marker': None, 'paginate': True, 'all_tenants': True}
        self.mock_server_list_paged.assert_called_once_with(
            test.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)

    @test.create_mocks({api.nova: ['service_list',
                                   'server_get']})
    def test_instance_live_migrate_get(self):
        server = self.servers.first()
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        self.mock_server_get.return_value = server
        self.mock_service_list.return_value = compute_services

        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'admin/instances/live_migrate.html')

        self.mock_server_get.assert_called_once_with(
            test.IsHttpRequest(), server.id)
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')

    @test.create_mocks({api.nova: ['server_get']})
    def test_instance_live_migrate_get_server_get_exception(self):
        server = self.servers.first()
        self.mock_server_get.side_effect = self.exceptions.nova

        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            test.IsHttpRequest(), server.id)

    @test.create_mocks({api.nova: ['service_list',
                                   'server_get']})
    def test_instance_live_migrate_list_host_get_exception(self):
        server = self.servers.first()
        self.mock_server_get.return_value = server
        self.mock_service_list.side_effect = self.exceptions.nova

        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            test.IsHttpRequest(), server.id)
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')

    @test.create_mocks({api.nova: ['service_list',
                                   'server_get']})
    def test_instance_live_migrate_list_host_without_current(self):
        server = self.servers.first()
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        self.mock_server_get.return_value = server
        self.mock_service_list.return_value = compute_services

        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.get(url)

        self.assertContains(
            res, "<option value=\"devstack001\">devstack001</option>")
        self.assertContains(
            res, "<option value=\"devstack002\">devstack002</option>")
        self.assertNotContains(
            res, "<option value=\"instance-host\">instance-host</option>")

        self.mock_server_get.assert_called_once_with(
            test.IsHttpRequest(), server.id)
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')

    @test.create_mocks({api.nova: ['service_list',
                                   'server_get',
                                   'server_live_migrate']})
    def test_instance_live_migrate_post(self):
        server = self.servers.first()
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        host = compute_services[0].host

        self.mock_server_get.return_value = server
        self.mock_service_list.return_value = compute_services
        self.mock_server_live_migrate.return_value = []

        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.post(url, {'host': host, 'instance_id': server.id})

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            test.IsHttpRequest(), server.id)
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')
        self.mock_server_live_migrate.assert_called_once_with(
            test.IsHttpRequest(), server.id, host,
            block_migration=False,
            disk_over_commit=False)

    @test.create_mocks({api.nova: ['service_list',
                                   'server_get',
                                   'server_live_migrate']})
    def test_instance_live_migrate_auto_sched(self):
        server = self.servers.first()
        host = "AUTO_SCHEDULE"
        self.mock_server_get.return_value = server
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        self.mock_service_list.return_value = compute_services
        self.mock_server_live_migrate.return_value = []

        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.post(url, {'host': host, 'instance_id': server.id})

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            test.IsHttpRequest(), server.id)
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')
        self.mock_server_live_migrate(
            test.IsHttpRequest(), server.id, None,
            block_migration=False,
            disk_over_commit=False)

    @test.create_mocks({api.nova: ['service_list',
                                   'server_get',
                                   'server_live_migrate']})
    def test_instance_live_migrate_post_api_exception(self):
        server = self.servers.first()
        compute_services = [s for s in self.services.list()
                            if s.binary == 'nova-compute']
        host = compute_services[0].host

        self.mock_server_get.return_value = server
        self.mock_service_list.return_value = compute_services
        self.mock_server_live_migrate.side_effect = self.exceptions.nova

        url = reverse('horizon:admin:instances:live_migrate',
                      args=[server.id])
        res = self.client.post(url, {'host': host, 'instance_id': server.id})

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            test.IsHttpRequest(), server.id)
        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')
        self.mock_server_live_migrate.assert_called_once_with(
            test.IsHttpRequest(), server.id, host,
            block_migration=False,
            disk_over_commit=False)

    @test.create_mocks({api.nova: ['server_get']})
    def test_instance_details_exception(self):
        server = self.servers.first()
        self.mock_server_get.side_effect = self.exceptions.nova

        url = reverse('horizon:admin:instances:detail',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            test.IsHttpRequest(), server.id)

    @test.update_settings(FILTER_DATA_FIRST={'admin.instances': True})
    def test_index_with_admin_filter_first(self):
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        instances = res.context['table'].data
        self.assertItemsEqual(instances, [])

    @test.create_mocks({
        api.nova: ['flavor_list',
                   'flavor_get',
                   'server_list_paged',
                   'extension_supported'],
        api.keystone: ['tenant_list'],
        api.glance: ['image_list_detailed_by_ids'],
    })
    def _test_servers_paginate_do(self,
                                  marker,
                                  servers,
                                  has_more,
                                  has_prev):
        flavors = self.flavors.list()
        tenants = self.tenants.list()
        images = self.images.list()
        # UUID indices are unique and are guaranteed being deterministic.
        for i, server in enumerate(servers):
            server.flavor['id'] = str(uuid.UUID(int=i))

        self.mock_server_list_paged.return_value = [
            servers, has_more, has_prev]
        self.mock_extension_supported.return_value = True
        self.mock_flavor_list.return_value = flavors
        self.mock_image_list_detailed_by_ids.return_value = images
        self.mock_tenant_list.return_value = [tenants, False]
        self.mock_flavor_get.side_effect = self.exceptions.nova

        if marker:
            url = "?".join([INDEX_URL, "marker={}".format(marker)])
        else:
            url = INDEX_URL
        res = self.client.get(url)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertEqual(res.status_code, 200)

        self.mock_extension_supported.assert_has_calls([
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('AdminActions', test.IsHttpRequest()),
            mock.call('Shelve', test.IsHttpRequest())])
        self.assertEqual(3, self.mock_extension_supported.call_count)
        self.mock_tenant_list.assert_called_once_with(test.IsHttpRequest())
        self.mock_image_list_detailed_by_ids.assert_called_once_with(
            test.IsHttpRequest(),
            [server.image.id for server in servers])
        self.mock_flavor_list.assert_called_once_with(test.IsHttpRequest())
        search_opts = {'marker': marker, 'paginate': True, 'all_tenants': True}
        self.mock_server_list_paged.assert_called_once_with(
            test.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_flavor_get.assert_has_calls(
            [mock.call(test.IsHttpRequest(), s.flavor['id']) for s in servers])
        self.assertEqual(len(servers), self.mock_flavor_get.call_count)

        return res

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_severs_index_paginated(self):
        size = settings.API_RESULT_PAGE_SIZE
        mox_servers = self.servers.list()

        # get first page
        expected_servers = mox_servers[:size]
        res = self._test_servers_paginate_do(
            marker=None,
            servers=expected_servers,
            has_more=True,
            has_prev=False)
        servers = res.context['table'].data
        self.assertItemsEqual(servers, expected_servers)

        # get second page
        expected_servers = mox_servers[size:2 * size]
        marker = expected_servers[0].id
        res = self._test_servers_paginate_do(
            marker=marker,
            servers=expected_servers,
            has_more=True,
            has_prev=True)
        servers = res.context['table'].data
        self.assertItemsEqual(servers, expected_servers)

        # get last page
        expected_servers = mox_servers[-size:]
        marker = expected_servers[0].id
        res = self._test_servers_paginate_do(
            marker=marker,
            servers=expected_servers,
            has_more=False,
            has_prev=True)
        servers = res.context['table'].data
        self.assertItemsEqual(servers, expected_servers)

    @override_settings(API_RESULT_PAGE_SIZE=1)
    def test_servers_index_paginated_prev(self):
        size = settings.API_RESULT_PAGE_SIZE
        mox_servers = self.servers.list()

        # prev from some page
        expected_servers = mox_servers[size:2 * size]
        marker = mox_servers[0].id

        res = self._test_servers_paginate_do(
            marker=marker,
            servers=expected_servers,
            has_more=False,
            has_prev=True)
        servers = res.context['table'].data
        self.assertItemsEqual(servers, expected_servers)

        # back to first page
        expected_servers = mox_servers[:size]
        marker = mox_servers[0].id
        res = self._test_servers_paginate_do(
            marker=marker,
            servers=expected_servers,
            has_more=True,
            has_prev=False)
        servers = res.context['table'].data
        self.assertItemsEqual(servers, expected_servers)
