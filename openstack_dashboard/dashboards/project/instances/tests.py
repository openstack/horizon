# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

import collections
import json
import logging
from unittest import mock

from django.conf import settings
from django import http
import django.test
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.http import urlencode
from novaclient import api_versions

from horizon import exceptions
from horizon import forms
from horizon.workflows import views
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances import console
from openstack_dashboard.dashboards.project.instances import tables
from openstack_dashboard.dashboards.project.instances import tabs
from openstack_dashboard.dashboards.project.instances import workflows
from openstack_dashboard.test import helpers
from openstack_dashboard.views import get_url_with_pagination


INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'
INDEX_URL = reverse('horizon:project:instances:index')
SEC_GROUP_ROLE_PREFIX = \
    workflows.update_instance.INSTANCE_SEC_GROUP_SLUG + "_role_"
AVAILABLE = api.cinder.VOLUME_STATE_AVAILABLE
VOLUME_SEARCH_OPTS = dict(status=AVAILABLE, bootable=True)
VOLUME_BOOTABLE_SEARCH_OPTS = dict(bootable=True)
SNAPSHOT_SEARCH_OPTS = dict(status=AVAILABLE)


class InstanceTestBase(helpers.ResetImageAPIVersionMixin,
                       helpers.TestCase):
    def _assert_mock_image_list_detailed_calls(self):
        expected_calls = [
            mock.call(helpers.IsHttpRequest()),
            mock.call(
                helpers.IsHttpRequest(),
                filters={'visibility': 'community'}
            )
        ]
        self.mock_image_list_detailed.assert_has_calls(expected_calls, False)

    def _assert_mock_image_list_detailed_calls_double(self):
        expected_calls = [
            mock.call(helpers.IsHttpRequest()),
            mock.call(
                helpers.IsHttpRequest(),
                filters={'visibility': 'community'}
            ),
            mock.call(helpers.IsHttpRequest()),
            mock.call(
                helpers.IsHttpRequest(),
                filters={'visibility': 'community'}
            )
        ]
        self.mock_image_list_detailed.assert_has_calls(expected_calls, False)

    def setUp(self):
        super().setUp()
        if api.glance.VERSIONS.active < 2:
            self.versioned_images = self.images
            self.versioned_snapshots = self.snapshots
        else:
            self.versioned_images = self.imagesV2
            self.versioned_snapshots = self.snapshotsV2


class InstanceTableTestMixin(object):

    def _mock_glance_image_list_detailed(self, image_list):
        self.mock_image_list_detailed.side_effect = [
            [image_list, False, False],
            [[], False, False],
        ]

    def _check_glance_image_list_detailed(self, count=None):
        if count is None:
            count = 2
        self.mock_image_list_detailed.assert_has_calls([
            mock.call(helpers.IsHttpRequest(),
                      filters={'is_public': True, 'status': 'active'}),
            mock.call(helpers.IsHttpRequest(),
                      filters={'property-owner_id': self.tenant.id,
                               'status': 'active'}),
        ])
        self.assertEqual(count, self.mock_image_list_detailed.call_count)

    def _mock_neutron_network_and_port_list(self):
        self.mock_network_list.side_effect = [
            self.networks.list()[:1],
            self.networks.list()[1:],
            self.networks.list()[:1],
            self.networks.list()[1:],
        ]
        self.mock_port_list_with_trunk_types.return_value = self.ports.list()

    def _check_neutron_network_and_port_list(self):
        self.assertEqual(4, self.mock_network_list.call_count)
        self.mock_network_list.assert_has_calls([
            mock.call(helpers.IsHttpRequest(), tenant_id=self.tenant.id,
                      shared=False),
            mock.call(helpers.IsHttpRequest(), shared=True),
            mock.call(helpers.IsHttpRequest(), tenant_id=self.tenant.id,
                      shared=False),
            mock.call(helpers.IsHttpRequest(), shared=True),
        ])
        self.assertEqual(len(self.networks.list()),
                         self.mock_port_list_with_trunk_types.call_count)
        self.mock_port_list_with_trunk_types(
            [mock.call(helpers.IsHttpRequest(),
                       network_id=net.id,
                       tenant_id=self.tenant.id)
             for net in self.networks.list()])

    def _mock_nova_lists(self):
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_keypair_list.return_value = self.keypairs.list()
        self.mock_security_group_list.return_value = \
            self.security_groups.list()
        self.mock_availability_zone_list.return_value = \
            self.availability_zones.list()
        self.mock_server_group_list.return_value = self.server_groups.list()

    def _check_nova_lists(self, flavor_count=None):
        if flavor_count is None:
            flavor_count = 1
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_flavor_list, flavor_count,
            mock.call(helpers.IsHttpRequest()))
        self.mock_keypair_list.assert_called_once_with(helpers.IsHttpRequest())
        self.mock_security_group_list.assert_called_once_with(
            helpers.IsHttpRequest())
        self.mock_availability_zone_list.assert_called_once_with(
            helpers.IsHttpRequest())
        self.mock_server_group_list.assert_called_once_with(
            helpers.IsHttpRequest())

    def _mock_nova_glance_neutron_lists(self):
        self._mock_nova_lists()
        self._mock_glance_image_list_detailed(
            self.versioned_images.list())
        self._mock_neutron_network_and_port_list()

    def _check_nova_glance_neutron_lists(self, return_value=True,
                                         flavor_count=None,
                                         image_count=None):
        self._check_nova_lists(flavor_count=flavor_count)
        self._check_glance_image_list_detailed(count=image_count)
        self._check_neutron_network_and_port_list()


class InstanceTableTests(InstanceTestBase, InstanceTableTestMixin):

    @helpers.create_mocks({
        api.nova: (
            'flavor_list',
            'server_list_paged',
            'tenant_absolute_limits',
            'is_feature_available',
        ),
        api.glance: ('image_list_detailed',),
        api.neutron: (
            'floating_ip_simple_associate_supported',
            'floating_ip_supported',
        ),
        api.network: (
            'servers_update_addresses',
        ),
        api.cinder: ('volume_list',),
    }, stop_mock=False)
    # NOTE: _get_index() and _check_get_index() are used as pair
    # and the test logic will be placed between these calls,
    # so we cannot stop mocking when exiting this method.
    def _get_index(self, use_servers_update_address=True):
        servers = self.servers.list()
        self.mock_is_feature_available.return_value = True
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = \
            (self.images.list(), False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_tenant_absolute_limits.return_value = \
            self.limits['absolute']
        self.mock_floating_ip_supported.return_value = True
        self.mock_floating_ip_simple_associate_supported.return_value = True
        return self.client.get(INDEX_URL)

    def _check_get_index(self, use_servers_update_address=True,
                         multiplier=5):
        expected_feature_count = 2 * multiplier
        expected_fip_supported_count = 2 * multiplier
        expected_simple_fip_supported = 1 * multiplier

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_feature_available, expected_feature_count,
            mock.call(helpers.IsHttpRequest(), 'locked_attribute'))
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        if use_servers_update_address:
            servers = self.servers.list()
            self.mock_servers_update_addresses.assert_called_once_with(
                helpers.IsHttpRequest(), servers)
        else:
            self.assertEqual(0, self.mock_servers_update_addresses.call_count)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_absolute_limits, 2,
            mock.call(helpers.IsHttpRequest(), reserved=True))
        if expected_fip_supported_count is None:
            expected_fip_supported_count = 8
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_supported, expected_fip_supported_count,
            mock.call(helpers.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_simple_associate_supported,
            expected_simple_fip_supported,
            mock.call(helpers.IsHttpRequest()))

    def test_index(self):
        res = self._get_index()

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        instances = res.context['instances_table'].data

        self.assertCountEqual(instances, self.servers.list())
        self.assertNotContains(res, "Launch Instance (Quota exceeded)")
        self._check_get_index()

    @override_settings(OPENSTACK_INSTANCE_RETRIEVE_IP_ADDRESSES=False)
    def test_index_without_servers_update_addresses(self):
        res = self._get_index(use_servers_update_address=False)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        instances = res.context['instances_table'].data

        self.assertCountEqual(instances, self.servers.list())
        self.assertNotContains(res, "Launch Instance (Quota exceeded)")
        self._check_get_index(use_servers_update_address=False)

    @helpers.create_mocks({
        api.nova: ('server_list_paged',
                   'tenant_absolute_limits',
                   'flavor_list'),
        api.glance: ('image_list_detailed',),
        api.cinder: ('volume_list',),
    })
    def test_index_server_list_exception(self):
        search_opts = {'marker': None, 'paginate': True}
        flavors = self.flavors.list()
        images = self.images.list()
        self.mock_flavor_list.return_value = flavors
        self.mock_image_list_detailed.return_value = (images, False, False)
        self.mock_server_list_paged.side_effect = self.exceptions.nova
        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        self.assertEqual(len(res.context['instances_table'].data), 0)
        self.assertMessageCount(res, error=1)
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_absolute_limits, 2,
            mock.call(helpers.IsHttpRequest(), reserved=True))

    @helpers.create_mocks({
        api.nova: ('flavor_list',
                   'server_list_paged',
                   'flavor_get',
                   'tenant_absolute_limits',
                   'is_feature_available',),
        api.glance: ('image_list_detailed',),
        api.neutron: ('floating_ip_simple_associate_supported',
                      'floating_ip_supported',),
        api.network: ('servers_update_addresses',),
        api.cinder: ('volume_list',),
    })
    def test_index_flavor_list_exception(self):
        servers = self.servers.list()
        search_opts = {'marker': None, 'paginate': True}

        self.mock_is_feature_available.return_value = True
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_flavor_list.side_effect = self.exceptions.nova
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']
        self.mock_floating_ip_supported.return_value = True
        self.mock_floating_ip_simple_associate_supported.return_value = True

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        instances = res.context['instances_table'].data

        self.assertCountEqual(instances, self.servers.list())

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_feature_available, 10,
            mock.call(helpers.IsHttpRequest(), 'locked_attribute'))
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_absolute_limits, 2,
            mock.call(helpers.IsHttpRequest(), reserved=True))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_supported, 10,
            mock.call(helpers.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_simple_associate_supported, 5,
            mock.call(helpers.IsHttpRequest()))

    @helpers.create_mocks({
        api.nova: ('flavor_list',
                   'server_list_paged',
                   'tenant_absolute_limits',
                   'is_feature_available',),
        api.glance: ('image_list_detailed',),
        api.neutron: ('floating_ip_simple_associate_supported',
                      'floating_ip_supported',),
        api.network: ('servers_update_addresses',),
        api.cinder: ('volume_list',),
    })
    def _test_index_with_instance_booted_from_volume(
            self, volume_image_metadata, expected_image_name):
        servers = self.servers.list()
        volume_server = servers[0]
        # Override the server is booted from a volume.
        volume_server.image = ""
        # NOTE(amotoki): openstack_dashboard.api.nova.server_list should return
        # a list of api.nova.Server instances, but the current test code
        # returns a list of novaclient.v2.servers.Server instances.
        # This leads to a situation that image_name property of api.nova.Server
        # is not handled in our test case properly.
        # TODO(amotoki): Refactor test_data/nova_data.py to use api.nova.Server
        # (horizon API wrapper class).
        volume_server = api.nova.Server(volume_server, self.request)
        servers[0] = volume_server

        volumes = self.cinder_volumes.list()
        # 3rd volume in the list is attached to server with ID 1.
        volume = volumes[2]
        volume.volume_image_metadata = volume_image_metadata

        self.mock_is_feature_available.return_value = True
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']
        self.mock_floating_ip_supported.return_value = True
        self.mock_floating_ip_simple_associate_supported.return_value = True
        self.mock_volume_list.return_value = volumes

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        instances = res.context['instances_table'].data
        self.assertEqual(len(instances), len(servers))
        if expected_image_name:
            self.assertContains(res, expected_image_name)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_feature_available, 10,
            mock.call(helpers.IsHttpRequest(), 'locked_attribute'))
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_absolute_limits, 2,
            mock.call(helpers.IsHttpRequest(), reserved=True))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_supported, 10,
            mock.call(helpers.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_simple_associate_supported, 5,
            mock.call(helpers.IsHttpRequest()))
        self.mock_volume_list.assert_called_once_with(helpers.IsHttpRequest())

        return instances

    def test_index_with_instance_booted_from_volume(self):
        base_image = self.images.get(name='private_image')
        image_metadata = {
            "image_id": base_image.id
        }
        servers = self._test_index_with_instance_booted_from_volume(
            image_metadata, expected_image_name=base_image.name)
        self.assertEqual(base_image.name, servers[0].image.name)

    def test_index_with_instance_booted_from_volume_no_image_info(self):
        # Borrowed from bug #1834747
        image_metadata = {
            'hw_qemu_guest_agent': 'yes',
            'hw_vif_multiqueue_enabled': 'true',
            'os_require_quiesce': 'yes',
        }
        servers = self._test_index_with_instance_booted_from_volume(
            image_metadata, expected_image_name=None)
        self.assertEqual('', servers[0].image)

    def test_index_with_console_link(self):
        res = self._get_index()

        instances_table = res.context['instances_table']
        instances = res.context['instances_table'].data
        console_link_rendered = False
        for instance in instances:
            for action in instances_table.get_row_actions(instance):
                if isinstance(action, tables.ConsoleLink):
                    console_link_rendered = True
                    break
            if console_link_rendered:
                break
            self.assertTrue(console_link_rendered)
        self._check_get_index(multiplier=6)

    @django.test.utils.override_settings(CONSOLE_TYPE=None)
    def test_index_without_console_link(self):
        res = self._get_index()

        instances_table = res.context['instances_table']
        instances = res.context['instances_table'].data
        for instance in instances:
            for action in instances_table.get_row_actions(instance):
                self.assertNotIsInstance(action, tables.ConsoleLink)
        self._check_get_index(multiplier=10)

    @helpers.create_mocks({api.nova: ('server_list_paged',
                                      'flavor_list',
                                      'server_delete',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_delete_instance(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_delete.return_value = None
        formData = {'action': 'instances__delete__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        self.mock_server_delete.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_list_paged',
                                      'flavor_list',
                                      'server_delete',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_delete_instance_error_state(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = 'ERROR'

        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_delete.return_value = None

        formData = {'action': 'instances__delete__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()
        self.mock_server_delete.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_list_paged',
                                      'flavor_list',
                                      'server_delete',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_delete_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_delete.side_effect = self.exceptions.nova

        formData = {'action': 'instances__delete__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()
        self.mock_server_delete.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_pause',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_pause_instance(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_pause.return_value = None

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()
        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_pause.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_pause',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_pause_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_pause.side_effect = self.exceptions.nova

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()
        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_pause.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_unpause',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_unpause_instance(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "PAUSED"
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_unpause.return_value = None

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_unpause.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_unpause',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_unpause_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "PAUSED"

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_unpause.side_effect = self.exceptions.nova

        formData = {'action': 'instances__pause__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_unpause.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_reboot',
                                      'server_list_paged',
                                      'flavor_list',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_reboot_instance(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_reboot.return_value = None

        formData = {'action': 'instances__reboot__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_reboot.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, soft_reboot=False)

    @helpers.create_mocks({api.nova: ('server_reboot',
                                      'server_list_paged',
                                      'flavor_list',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_reboot_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_reboot.side_effect = self.exceptions.nova

        formData = {'action': 'instances__reboot__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_reboot.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, soft_reboot=False)

    @helpers.create_mocks({api.nova: ('server_reboot',
                                      'server_list_paged',
                                      'flavor_list',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_soft_reboot_instance(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_reboot.return_value = None

        formData = {'action': 'instances__soft_reboot__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_reboot.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, soft_reboot=True)

    @helpers.create_mocks({api.nova: ('server_suspend',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_suspend_instance(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_suspend.return_value = None

        formData = {'action': 'instances__suspend__%s' % server.id}
        url = get_url_with_pagination(
            self.request, 'next', 'prev', 'horizon:project:instances:index')
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(
            helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_suspend.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @django.test.utils.override_settings(API_RESULT_PAGE_SIZE=2)
    @helpers.create_mocks({api.nova: ('server_suspend',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_suspend_instance_if_placed_on_2nd_page(self):
        page_size = settings.API_RESULT_PAGE_SIZE
        servers = self.servers.list()[:3]

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [
            servers[page_size:], False, True]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_suspend.return_value = None

        self.request.GET['marker'] = servers[-2].id
        params = "=".join([tables.InstancesTable._meta.pagination_param,
                           servers[page_size - 1].id])
        url = "?".join([reverse('horizon:project:instances:index'),
                        params])
        formData = {'action': 'instances__suspend__%s' % servers[-1].id}

        self.client.post(url, formData)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts={'marker': servers[page_size - 1].id,
                         'paginate': True})
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers[page_size:])
        self.mock_server_suspend.assert_called_once_with(
            helpers.IsHttpRequest(), servers[-1].id)

    @helpers.create_mocks({api.nova: ('server_suspend',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_suspend_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_suspend.side_effect = self.exceptions.nova

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_suspend.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_resume',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_resume_instance(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "SUSPENDED"

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_resume.return_value = None

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_resume.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_resume',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available'),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_resume_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "SUSPENDED"

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_resume.side_effect = self.exceptions.nova

        formData = {'action': 'instances__suspend__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_resume.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_shelve',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_shelve_instance(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_shelve.return_value = None
        formData = {'action': 'instances__shelve__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_shelve.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_shelve',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_shelve_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_shelve.side_effect = self.exceptions.nova

        formData = {'action': 'instances__shelve__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_shelve.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_unshelve',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_unshelve_instance(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "SHELVED_OFFLOADED"

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_unshelve.return_value = None

        formData = {'action': 'instances__shelve__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_unshelve.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_unshelve',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_unshelve_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "SHELVED_OFFLOADED"

        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_unshelve.side_effect = self.exceptions.nova

        formData = {'action': 'instances__shelve__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_unshelve.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_lock',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_lock_instance(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_is_feature_available.return_value = True
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_lock.return_value = None
        formData = {'action': 'instances__lock__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), 'locked_attribute')
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_lock.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_lock',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_lock_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]

        self.mock_is_feature_available.return_value = True
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_lock.side_effect = self.exceptions.nova

        formData = {'action': 'instances__lock__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), 'locked_attribute')
        self.mock_flavor_list.assert_called_once_with(
            helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_lock.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_unlock',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available'),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_unlock_instance(self):
        servers = self.servers.list()
        server = servers[0]
        self.mock_is_feature_available.return_value = True
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_unlock.return_value = None
        formData = {'action': 'instances__unlock__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), 'locked_attribute')
        self.mock_flavor_list.assert_called_once_with(
            helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_unlock.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_unlock',
                                      'server_list_paged',
                                      'flavor_list',
                                      'is_feature_available'),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_unlock_instance_exception(self):
        servers = self.servers.list()
        server = servers[0]
        self.mock_is_feature_available.return_value = True
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_server_unlock.side_effect = self.exceptions.nova

        formData = {'action': 'instances__unlock__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), 'locked_attribute')
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_server_unlock.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)


class InstanceDetailTests(InstanceTestBase):

    @helpers.create_mocks({
        api.nova: (
            "server_get",
            "instance_volumes_list",
            "flavor_get",
            "flavor_list",
            'is_feature_available',
        ),
        api.neutron: (
            "server_security_groups",
            "floating_ip_simple_associate_supported",
            "floating_ip_supported"
        ),
        api.network: ('servers_update_addresses',),
    })
    def _get_instance_details(self, server, qs=None,
                              flavor_return=None, volumes_return=None,
                              security_groups_return=None,
                              flavor_exception=False, nova_api_ge_2_47=False):

        url = reverse('horizon:project:instances:detail', args=[server.id])
        if qs:
            url += qs

        if flavor_return is None:
            flavor_return = self.flavors.first()

        if volumes_return is None:
            volumes_return = []

        if security_groups_return is None:
            security_groups_return = self.security_groups.list()

        self.mock_server_get.return_value = server
        self.mock_servers_update_addresses.return_value = None
        self.mock_instance_volumes_list.return_value = volumes_return
        if flavor_exception:
            self.mock_flavor_get.side_effect = self.exceptions.nova
        else:
            self.mock_flavor_get.return_value = flavor_return
        self.mock_server_security_groups.return_value = security_groups_return
        self.mock_floating_ip_simple_associate_supported.return_value = True
        self.mock_floating_ip_supported.return_value = True
        self.mock_is_feature_available.return_value = True

        res = self.client.get(url)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), mock.ANY)
        self.mock_instance_volumes_list.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        if nova_api_ge_2_47:
            self.mock_flavor_list.assert_called_once_with(
                helpers.IsHttpRequest())
        else:
            self.mock_flavor_get.assert_called_once_with(
                helpers.IsHttpRequest(), server.flavor['id'])
        self.mock_server_security_groups.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_floating_ip_simple_associate_supported \
            .assert_called_once_with(helpers.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_supported, 2,
            mock.call(helpers.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_feature_available, 2,
            mock.call(helpers.IsHttpRequest(), 'locked_attribute'))

        return res

    @helpers.create_mocks({api.neutron: ['is_extension_supported']})
    def test_instance_details_volumes(self):
        server = self.servers.first()
        volumes = [self.nova_volumes.list()[1]]
        security_groups = self.security_groups.list()

        self.mock_is_extension_supported.return_value = False

        res = self._get_instance_details(
            server, volumes_return=volumes,
            security_groups_return=security_groups)

        self.assertCountEqual(res.context['instance'].volumes, volumes)
        self.mock_is_extension_supported.assert_called_once_with(
            helpers.IsHttpRequest(), 'mac-learning')

    @helpers.create_mocks({api.neutron: ['is_extension_supported']})
    def test_instance_details_volume_sorting(self):
        server = self.servers.first()
        volumes = self.nova_volumes.list()[1:3]
        security_groups = self.security_groups.list()

        self.mock_is_extension_supported.return_value = False

        res = self._get_instance_details(
            server, volumes_return=volumes,
            security_groups_return=security_groups)

        self.assertCountEqual(res.context['instance'].volumes, volumes)
        self.assertEqual(res.context['instance'].volumes[0].device,
                         "/dev/hda")
        self.assertEqual(res.context['instance'].volumes[1].device,
                         "/dev/hdk")
        self.mock_is_extension_supported.assert_called_once_with(
            helpers.IsHttpRequest(), 'mac-learning')

    @helpers.create_mocks({api.neutron: ['is_extension_supported']})
    def test_instance_details_metadata(self):
        server = self.servers.first()

        self.mock_is_extension_supported.return_value = False

        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("overview").get_id())
        res = self._get_instance_details(server, qs)

        self.assertContains(res, '<dd class="word-wrap">keyName</dd>', 1)
        self.assertContains(res, "<dt>someMetaLabel</dt>", 1)
        self.assertContains(res, "<dd>someMetaData</dd>", 1)
        self.assertContains(res, "<dt>some&lt;b&gt;html&lt;/b&gt;label</dt>",
                            1)
        self.assertContains(res, "<dd>&lt;!--</dd>", 1)
        self.assertContains(res, "<dt>empty</dt>", 1)
        self.assertContains(res, "<dd><em>N/A</em></dd>", 1)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_extension_supported, 2,
            mock.call(helpers.IsHttpRequest(), 'mac-learning'))

    @helpers.create_mocks({api.neutron: ['is_extension_supported']})
    def test_instance_details_fault(self):
        server = self.servers.first()

        self.mock_is_extension_supported.return_value = False

        server.status = 'ERROR'
        server.fault = {"message": "NoValidHost",
                        "code": 500,
                        "details": "No valid host was found. \n  "
                                   "File \"/mnt/stack/nova/nova/"
                                   "scheduler/filter_scheduler.py\", "
                                   "line 105, in schedule_run_instance\n    "
                                   "raise exception.NoValidHost"
                                   "(reason=\"\")\n",
                        "created": "2013-10-07T00:08:32Z"}

        res = self._get_instance_details(server)
        self.assertCountEqual(res.context['instance'].fault, server.fault)
        self.mock_is_extension_supported.assert_called_once_with(
            helpers.IsHttpRequest(), 'mac-learning')

    @helpers.create_mocks({console: ['get_console'],
                           api.neutron: ['is_extension_supported']})
    def test_instance_details_console_tab(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/vncserver'
        CONSOLE_TITLE = '&title=%s(%s)' % (server.name, server.id)
        CONSOLE_URL = CONSOLE_OUTPUT + CONSOLE_TITLE

        self.mock_get_console.return_value = ('VNC', CONSOLE_URL)
        self.mock_is_extension_supported.return_value = False

        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("console").get_id())
        res = self._get_instance_details(server, qs)
        self.assertIn(tabs.ConsoleTab, res.context_data['tab_group'].tabs)
        self.assertTemplateUsed(res,
                                'project/instances/_detail_console.html')
        console_tab_rendered = False
        for tab in res.context_data['tab_group'].get_loaded_tabs():
            if isinstance(tab, tabs.ConsoleTab):
                console_tab_rendered = True
                break
        self.assertTrue(console_tab_rendered)
        self.mock_get_console.assert_called_once_with(
            mock.ANY, 'AUTO', server)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_extension_supported, 2,
            mock.call(helpers.IsHttpRequest(), 'mac-learning'))

    @django.test.utils.override_settings(CONSOLE_TYPE=None)
    @helpers.create_mocks({api.neutron: ['is_extension_supported']})
    def test_instance_details_console_tab_deactivated(self):
        server = self.servers.first()

        self.mock_is_extension_supported.return_value = False

        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        self.assertIsNone(tg.get_tab("console"))
        res = self._get_instance_details(server)
        self.assertTemplateNotUsed(res,
                                   'project/instances/_detail_console.html')
        for tab in res.context_data['tab_group'].get_loaded_tabs():
            self.assertNotIsInstance(tab, tabs.ConsoleTab)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_extension_supported, 2,
            mock.call(helpers.IsHttpRequest(), 'mac-learning'))

    @helpers.create_mocks({api.nova: ('server_get',)})
    def test_instance_details_exception(self):
        server = self.servers.first()

        self.mock_server_get.side_effect = self.exceptions.nova

        url = reverse('horizon:project:instances:detail',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_server_get.assert_called_once_with(helpers.IsHttpRequest(),
                                                     server.id)

    @helpers.create_mocks({api.nova: ("server_get",)})
    def test_instance_details_unauthorized(self):
        server = self.servers.first()

        url = reverse('horizon:admin:instances:detail',
                      args=[server.id])

        # Avoid the log message in the test
        # when unauthorized exception will be logged
        logging.disable(logging.ERROR)
        res = self.client.get(url)
        logging.disable(logging.NOTSET)

        self.assertEqual(403, res.status_code)
        self.assertEqual(0, self.mock_server_get.call_count)

    @helpers.create_mocks({api.neutron: ['is_extension_supported']})
    def test_instance_details_flavor_not_found(self):
        server = self.servers.first()
        self.mock_is_extension_supported.return_value = False
        res = self._get_instance_details(server, flavor_exception=True)
        self.assertTemplateUsed(res,
                                'project/instances/_detail_overview.html')
        self.assertContains(res, "Not available")
        self.mock_is_extension_supported.assert_called_once_with(
            helpers.IsHttpRequest(), 'mac-learning')

    @helpers.create_mocks({api.neutron: ['is_extension_supported']})
    def test_instance_details_nova_api_ge_2_47(self):
        server = self.servers.first()
        server.flavor = {
            'original_name': 'm1.tiny',
        }
        self.mock_is_extension_supported.return_value = False
        res = self._get_instance_details(server, nova_api_ge_2_47=True)
        self.assertTemplateUsed(res,
                                'project/instances/_detail_overview.html')
        self.mock_is_extension_supported.assert_called_once_with(
            helpers.IsHttpRequest(), 'mac-learning')

    @helpers.create_mocks({api.nova: ['server_console_output'],
                           api.neutron: ['is_extension_supported']})
    def test_instance_log(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = 'output'

        self.mock_server_console_output.return_value = CONSOLE_OUTPUT
        self.mock_is_extension_supported.return_value = False

        url = reverse('horizon:project:instances:console',
                      args=[server.id])
        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("log").get_id())
        res = self.client.get(url + qs)

        self.assertNoMessages()
        self.assertIsInstance(res, http.HttpResponse)
        self.assertContains(res, CONSOLE_OUTPUT)
        self.mock_server_console_output.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, tail_length=None)
        self.mock_is_extension_supported.assert_called_once_with(
            helpers.IsHttpRequest(), 'mac-learning')

    @helpers.create_mocks({api.nova: ['server_console_output'],
                           api.neutron: ['is_extension_supported']})
    def test_instance_log_exception(self):
        server = self.servers.first()

        self.mock_server_console_output.side_effect = self.exceptions.nova
        self.mock_is_extension_supported.return_value = False

        url = reverse('horizon:project:instances:console',
                      args=[server.id])
        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        qs = "?%s=%s" % (tg.param_name, tg.get_tab("log").get_id())
        res = self.client.get(url + qs)

        self.assertContains(res, "Unable to get log for")
        self.mock_server_console_output.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, tail_length=None)
        self.mock_is_extension_supported.assert_called_once_with(
            helpers.IsHttpRequest(), 'mac-learning')

    @helpers.create_mocks({api.neutron: ['is_extension_supported']})
    def test_instance_log_invalid_input(self):
        server = self.servers.first()
        self.mock_is_extension_supported.return_value = False

        url = reverse('horizon:project:instances:console',
                      args=[server.id])
        tg = tabs.InstanceDetailTabs(self.request, instance=server)
        for length in ["-5", "x"]:
            qs = "?%s=%s&length=%s" % (tg.param_name,
                                       tg.get_tab("log").get_id(),
                                       length)
            res = self.client.get(url + qs)

            self.assertContains(res, "Unable to get log for")

        self.mock_is_extension_supported.assert_called_once_with(
            helpers.IsHttpRequest(), 'mac-learning')

    @helpers.create_mocks({api.nova: ['server_get'],
                           console: ['get_console']})
    def test_instance_auto_console(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/vncserver'
        CONSOLE_TITLE = '&title=%s(%s)' % (server.name, server.id)
        CONSOLE_URL = CONSOLE_OUTPUT + CONSOLE_TITLE

        self.mock_server_get.return_value = server
        self.mock_get_console.return_value = ('VNC', CONSOLE_URL)

        url = reverse('horizon:project:instances:auto_console',
                      args=[server.id])
        res = self.client.get(url)
        redirect = CONSOLE_URL
        self.assertRedirectsNoFollow(res, redirect)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_get_console.assert_called_once_with(
            mock.ANY, 'AUTO', server)

    @helpers.create_mocks({api.nova: ['server_get'],
                           console: ['get_console']})
    def test_instance_vnc_error(self):
        server = self.servers.first()
        self.mock_server_get.return_value = server
        self.mock_get_console.side_effect = exceptions.NotAvailable('console')

        url = reverse('horizon:project:instances:vnc',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_get_console.assert_called_once_with(
            mock.ANY, 'VNC', server)

    @helpers.create_mocks({api.nova: ['server_get'],
                           console: ['get_console']})
    def test_instance_spice(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/spiceserver'
        CONSOLE_TITLE = '&title=%s(%s)' % (server.name, server.id)
        CONSOLE_URL = CONSOLE_OUTPUT + CONSOLE_TITLE

        self.mock_server_get.return_value = server
        self.mock_get_console.return_value = ('SPICE', CONSOLE_URL)

        url = reverse('horizon:project:instances:spice',
                      args=[server.id])
        res = self.client.get(url)
        redirect = CONSOLE_URL
        self.assertRedirectsNoFollow(res, redirect)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_get_console.assert_called_once_with(
            mock.ANY, 'SPICE', server)

    @helpers.create_mocks({api.nova: ['server_get'],
                           console: ['get_console']})
    def test_instance_spice_exception(self):
        server = self.servers.first()
        self.mock_server_get.return_value = server
        self.mock_get_console.side_effect = exceptions.NotAvailable('console')

        url = reverse('horizon:project:instances:spice',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_get_console.assert_called_once_with(
            mock.ANY, 'SPICE', server)

    @helpers.create_mocks({api.nova: ['server_get'],
                           console: ['get_console']})
    def test_instance_rdp(self):
        server = self.servers.first()
        CONSOLE_OUTPUT = '/rdpserver'
        CONSOLE_TITLE = '&title=%s(%s)' % (server.name, server.id)
        CONSOLE_URL = CONSOLE_OUTPUT + CONSOLE_TITLE

        self.mock_server_get.return_value = server
        self.mock_get_console.return_value = ('RDP', CONSOLE_URL)

        url = reverse('horizon:project:instances:rdp',
                      args=[server.id])
        res = self.client.get(url)
        redirect = CONSOLE_URL
        self.assertRedirectsNoFollow(res, redirect)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_get_console.assert_called_once_with(
            mock.ANY, 'RDP', server)

    @helpers.create_mocks({api.nova: ['server_get'],
                           console: ['get_console']})
    def test_instance_rdp_exception(self):
        server = self.servers.first()

        self.mock_server_get.return_value = server
        self.mock_get_console.side_effect = exceptions.NotAvailable('console')

        url = reverse('horizon:project:instances:rdp',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_get_console.assert_called_once_with(
            mock.ANY, 'RDP', server)


class InstanceTests(InstanceTestBase):

    @helpers.create_mocks({api.nova: ('server_get',
                                      'snapshot_create'),
                           api.glance: ('image_list_detailed',)})
    def test_create_instance_snapshot(self):
        server = self.servers.first()

        self.mock_server_get.return_value = server
        self.mock_snapshot_create.return_value = self.snapshots.first()
        self.mock_image_list_detailed.return_value = \
            (self.images.list(), False, False)

        formData = {'instance_id': server.id,
                    'method': 'CreateSnapshot',
                    'name': 'snapshot1'}
        url = reverse('horizon:project:images:snapshots:create',
                      args=[server.id])
        redir_url = reverse('horizon:project:images:index')
        res = self.client.post(url, formData)
        self.assertRedirects(res, redir_url)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_snapshot_create.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, "snapshot1")
        self.mock_image_list_detailed.assert_called_once_with(
            helpers.IsHttpRequest(), marker=None, paginate=True,
            reversed_order=False, sort_dir='asc', sort_key='name')

    @django.test.utils.override_settings(
        OPENSTACK_ENABLE_PASSWORD_RETRIEVE=False)
    def test_instances_index_retrieve_password_action_disabled(self):
        self. _test_instances_index_retrieve_password_action()

    @django.test.utils.override_settings(
        OPENSTACK_ENABLE_PASSWORD_RETRIEVE=True)
    def test_instances_index_retrieve_password_action_enabled(self):
        self._test_instances_index_retrieve_password_action()

    @helpers.create_mocks({
        api.nova: ('flavor_list',
                   'server_list_paged',
                   'tenant_absolute_limits',
                   'is_feature_available',),
        api.glance: ('image_list_detailed',),
        api.neutron: ('floating_ip_simple_associate_supported',
                      'floating_ip_supported',),
        api.network: ('servers_update_addresses',),
        api.cinder: ('volume_list',),
    })
    def _test_instances_index_retrieve_password_action(self):
        servers = self.servers.list()

        self.mock_is_feature_available.return_value = True
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']
        self.mock_floating_ip_supported.return_value = True
        self.mock_floating_ip_simple_associate_supported.return_value = True

        url = reverse('horizon:project:instances:index')
        res = self.client.get(url)
        for server in servers:
            _action_id = ''.join(["instances__row_",
                                  server.id,
                                  "__action_decryptpassword"])
            if settings.OPENSTACK_ENABLE_PASSWORD_RETRIEVE and \
                    server.status == "ACTIVE" and \
                    server.key_name is not None:
                self.assertContains(res, _action_id)
            else:
                self.assertNotContains(res, _action_id)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_feature_available, 10,
            mock.call(helpers.IsHttpRequest(), 'locked_attribute'))
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_absolute_limits, 2,
            mock.call(helpers.IsHttpRequest(), reserved=True))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_supported, 10,
            mock.call(helpers.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_simple_associate_supported, 5,
            mock.call(helpers.IsHttpRequest()))

    @helpers.create_mocks({api.nova: ('get_password',)})
    def test_decrypt_instance_password(self):
        server = self.servers.first()
        enc_password = "azerty"
        self.mock_get_password.return_value = enc_password
        url = reverse('horizon:project:instances:decryptpassword',
                      args=[server.id,
                            server.key_name])
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'project/instances/decryptpassword.html')
        self.mock_get_password.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('get_password',)})
    def test_decrypt_instance_get_exception(self):
        server = self.servers.first()
        keypair = self.keypairs.first()
        self.mock_get_password.side_effect = self.exceptions.nova
        url = reverse('horizon:project:instances:decryptpassword',
                      args=[server.id,
                            keypair])
        res = self.client.get(url)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_get_password.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    instance_update_get_stubs = {
        api.nova: ('server_get', 'is_feature_available'),
        api.neutron: ('security_group_list',
                      'server_security_groups',)}

    @helpers.create_mocks(instance_update_get_stubs)
    def test_instance_update_get(self):
        server = self.servers.first()

        self.mock_server_get.return_value = server
        self.mock_security_group_list.return_value = []
        self.mock_server_security_groups.return_value = []
        self.mock_is_feature_available.return_value = False

        url = reverse('horizon:project:instances:update', args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_security_group_list(helpers.IsHttpRequest(), tenant_id=None)
        self.mock_server_security_groups(helpers.IsHttpRequest(), server.id)
        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), "instance_description"
        )

    @helpers.create_mocks(instance_update_get_stubs)
    def test_instance_update_get_server_get_exception(self):
        server = self.servers.first()

        self.mock_server_get.side_effect = self.exceptions.nova

        url = reverse('horizon:project:instances:update',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    def _instance_update_post(self, server_id, server_name, secgroups):
        default_role_field_name = 'default_' + \
            workflows.update_instance.INSTANCE_SEC_GROUP_SLUG + '_role'
        formData = {'name': server_name,
                    default_role_field_name: 'member',
                    SEC_GROUP_ROLE_PREFIX + 'member': secgroups}
        url = reverse('horizon:project:instances:update',
                      args=[server_id])
        return self.client.post(url, formData)

    instance_update_post_stubs = {
        api.nova: ('server_get', 'server_update', 'is_feature_available'),
        api.neutron: ('security_group_list',
                      'server_security_groups',
                      'server_update_security_groups')}

    @helpers.create_mocks(instance_update_post_stubs)
    def test_instance_update_post(self):
        server = self.servers.first()
        secgroups = self.security_groups.list()[:3]

        server_groups = [secgroups[0], secgroups[1]]
        wanted_groups = [secgroups[1].id, secgroups[2].id]

        self.mock_server_get.return_value = server
        self.mock_is_feature_available.return_value = False
        self.mock_security_group_list.return_value = secgroups
        self.mock_server_security_groups.return_value = server_groups
        self.mock_server_update.return_value = server
        self.mock_server_update_security_groups.return_value = None

        res = self._instance_update_post(server.id, server.name, wanted_groups)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_security_group_list.assert_called_once_with(
            helpers.IsHttpRequest(), tenant_id=self.tenant.id)
        self.mock_server_security_groups.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_server_update.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, server.name, description=None)
        self.mock_server_update_security_groups.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, wanted_groups)
        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), "instance_description"
        )

    @helpers.create_mocks(instance_update_post_stubs)
    def test_instance_update_post_with_desc(self):
        server = self.servers.first()
        secgroups = self.security_groups.list()[:3]

        server_groups = [secgroups[0], secgroups[1]]
        test_description = 'test description'

        self.mock_server_get.return_value = server
        self.mock_is_feature_available.return_value = True
        self.mock_security_group_list.return_value = secgroups
        self.mock_server_security_groups.return_value = server_groups
        self.mock_server_update.return_value = server

        formData = {'name': server.name,
                    'description': test_description}
        url = reverse('horizon:project:instances:update',
                      args=[server.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_security_group_list.assert_called_once_with(
            helpers.IsHttpRequest(), tenant_id=self.tenant.id)
        self.mock_server_security_groups.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_server_update.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, server.name,
            description=test_description)
        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), "instance_description"
        )

    @helpers.create_mocks(instance_update_post_stubs)
    def test_instance_update_post_api_exception(self):
        server = self.servers.first()

        self.mock_server_get.return_value = server
        self.mock_is_feature_available.return_value = False
        self.mock_security_group_list.return_value = []
        self.mock_server_security_groups.return_value = []
        self.mock_server_update.side_effect = self.exceptions.nova
        self.mock_server_update_security_groups.return_value = None

        res = self._instance_update_post(server.id, server.name, [])
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_security_group_list.assert_called_once_with(
            helpers.IsHttpRequest(), tenant_id=self.tenant.id)
        self.mock_server_security_groups.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_server_update.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, server.name, description=None)
        self.mock_server_update_security_groups.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, [])
        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), "instance_description"
        )

    @helpers.create_mocks(instance_update_post_stubs)
    def test_instance_update_post_secgroup_api_exception(self):
        server = self.servers.first()

        self.mock_server_get.return_value = server
        self.mock_is_feature_available.return_value = False
        self.mock_security_group_list.return_value = []
        self.mock_server_security_groups.return_value = []
        self.mock_server_update.return_value = server
        self.mock_server_update_security_groups.side_effect = \
            self.exceptions.nova

        res = self._instance_update_post(server.id, server.name, [])
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_security_group_list.assert_called_once_with(
            helpers.IsHttpRequest(), tenant_id=self.tenant.id)
        self.mock_server_security_groups.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_server_update.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, server.name, description=None)
        self.mock_server_update_security_groups.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, [])
        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), "instance_description"
        )


class InstanceTests2(InstanceTestBase, InstanceTableTestMixin):

    @helpers.create_mocks({
        api.nova: ('flavor_list',
                   'server_list_paged',
                   'tenant_absolute_limits',
                   'is_feature_available',),
        api.glance: ('image_list_detailed',),
        api.neutron: ('floating_ip_simple_associate_supported',
                      'floating_ip_supported',),
        api.network: ('servers_update_addresses',),
        api.cinder: ('volume_list',),
    })
    def test_index_options_after_migrate(self):
        servers = self.servers.list()
        server = self.servers.first()
        server.status = "VERIFY_RESIZE"

        self.mock_is_feature_available.return_value = True
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']
        self.mock_floating_ip_supported.return_value = True
        self.mock_floating_ip_simple_associate_supported.return_value = True

        res = self.client.get(INDEX_URL)
        self.assertContains(res, "instances__confirm")
        self.assertContains(res, "instances__revert")

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_feature_available, 10,
            mock.call(helpers.IsHttpRequest(), 'locked_attribute'))
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_absolute_limits, 2,
            mock.call(helpers.IsHttpRequest(), reserved=True))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_supported, 10,
            mock.call(helpers.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_simple_associate_supported, 5,
            mock.call(helpers.IsHttpRequest()))

    @helpers.create_mocks({
        api.neutron: ('floating_ip_target_list_by_instance',
                      'tenant_floating_ip_list',
                      'floating_ip_disassociate',
                      'tenant_floating_ip_release'),
    })
    def _test_disassociate_floating_ip(self, is_release):
        servers = self.servers.list()
        server = servers[0]
        port = [p for p in self.ports.list() if p.device_id == server.id][0]
        fip_target = api.neutron.FloatingIpTarget(
            port, port['fixed_ips'][0]['ip_address'], server.name)
        fip = self.floating_ips.first()
        fip.port_id = port.id

        self.mock_floating_ip_target_list_by_instance.return_value = \
            [fip_target]
        self.mock_tenant_floating_ip_list.return_value = [fip]
        self.mock_floating_ip_disassociate.return_value = None
        self.mock_tenant_floating_ip_release.return_value = None

        url = reverse('horizon:project:instances:disassociate',
                      args=[server.id])
        form_data = {'fip': fip.id,
                     'is_release': is_release}
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_floating_ip_target_list_by_instance.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_tenant_floating_ip_list.assert_called_once_with(
            helpers.IsHttpRequest())
        if is_release:
            self.mock_floating_ip_disassociate.assert_not_called()
            self.mock_tenant_floating_ip_release.assert_called_once_with(
                helpers.IsHttpRequest(), fip.id)
        else:
            self.mock_floating_ip_disassociate.assert_called_once_with(
                helpers.IsHttpRequest(), fip.id)
            self.mock_tenant_floating_ip_release.assert_not_called()

    @helpers.create_mocks({api.neutron: ('floating_ip_disassociate',)})
    def test_disassociate_floating_ip(self):
        self._test_disassociate_floating_ip(is_release=False)

    @helpers.create_mocks({api.neutron: ('tenant_floating_ip_release',)})
    def test_disassociate_floating_ip_with_release(self):
        self._test_disassociate_floating_ip(is_release=True)

    def _populate_server_flavor_nova_api_ge_2_47(self, server):
        flavor_id = server.flavor['id']
        flavor = self.flavors.get(id=flavor_id)
        server.flavor = {
            'original_name': flavor.name,
            'vcpus': flavor.vcpus,
            'ram': flavor.ram,
            'swap': flavor.swap,
            'disk': flavor.disk,
            'ephemeral': flavor.ephemeral,
            'extra_specs': flavor.extra_specs,
        }
        return server

    @helpers.create_mocks({api.nova: ('server_get',
                                      'flavor_list',
                                      'tenant_absolute_limits',
                                      'is_feature_available')})
    def _test_instance_resize_get(self, server, nova_api_lt_2_47=False):
        self.mock_server_get.return_value = server
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']

        url = reverse('horizon:project:instances:resize', args=[server.id])
        res = self.client.get(url)

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.WorkflowView.template_name)
        self.assertEqual(res.context['workflow'].name,
                         workflows.ResizeInstance.name)
        self.assertContains(res, 'Disk Partition')

        step = workflow.get_step("flavor_choice")
        self.assertEqual(step.action.initial['old_flavor_name'],
                         self.flavors.first().name)

        step = workflow.get_step("setadvancedaction")
        self.assertEqual(step.action.fields['disk_config'].label,
                         'Disk Partition')
        self.assertQuerysetEqual(workflow.steps,
                                 ['<SetFlavorChoice: flavor_choice>',
                                  '<SetAdvanced: setadvancedaction>'],
                                 transform=repr)
        option = '<option value="%s">%s</option>'

        def is_original_flavor(server, flavor, nova_api_lt_2_47):
            if nova_api_lt_2_47:
                return flavor.id == server.flavor['id']
            else:
                return flavor.name == server.flavor['original_name']

        for flavor in self.flavors.list():
            if is_original_flavor(server, flavor, nova_api_lt_2_47):
                self.assertNotContains(res, option % (flavor.id, flavor.name))
            else:
                self.assertContains(res, option % (flavor.id, flavor.name))

        self.mock_server_get.assert_called_once_with(helpers.IsHttpRequest(),
                                                     server.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_flavor_list, 2,
            mock.call(helpers.IsHttpRequest()))
        self.mock_tenant_absolute_limits.assert_called_once_with(
            helpers.IsHttpRequest(), reserved=True)

    def test_instance_resize_get_nova_api_lt_2_47(self):
        server = self.servers.first()
        self._test_instance_resize_get(server, nova_api_lt_2_47=True)

    def test_instance_resize_get_nova_api_ge_2_47(self):
        server = self.servers.first()
        self._populate_server_flavor_nova_api_ge_2_47(server)
        self._test_instance_resize_get(server)

    @helpers.create_mocks({api.nova: ('server_get',)})
    def test_instance_resize_get_server_get_exception(self):
        server = self.servers.first()

        self.mock_server_get.side_effect = self.exceptions.nova

        url = reverse('horizon:project:instances:resize',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_get',
                                      'flavor_list',)})
    def test_instance_resize_get_flavor_list_exception(self):
        server = self.servers.first()
        self.mock_server_get.return_value = server
        self.mock_flavor_list.side_effect = self.exceptions.nova

        url = reverse('horizon:project:instances:resize',
                      args=[server.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(helpers.IsHttpRequest(),
                                                     server.id)
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())

    # TODO(amotoki): This is requred only when nova API <=2.46 is used.
    # Once server_get() uses nova API >=2.47 only, this test can be droppped.
    @helpers.create_mocks({api.nova: ('server_get',
                                      'flavor_list',
                                      'flavor_get',
                                      'tenant_absolute_limits',
                                      'is_feature_available')})
    def test_instance_resize_get_current_flavor_not_found(self):
        server = self.servers.first()
        self.mock_server_get.return_value = server
        self.mock_flavor_list.return_value = []
        self.mock_flavor_get.side_effect = self.exceptions.nova
        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']

        url = reverse('horizon:project:instances:resize', args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        self.mock_server_get.assert_called_once_with(helpers.IsHttpRequest(),
                                                     server.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_flavor_list, 2,
            mock.call(helpers.IsHttpRequest()))
        self.mock_flavor_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.flavor['id'])
        self.mock_tenant_absolute_limits.assert_called_once_with(
            helpers.IsHttpRequest(), reserved=True)

    def _instance_resize_post(self, server_id, flavor_id, disk_config):
        formData = {'flavor': flavor_id,
                    'default_role': 'member',
                    'disk_config': disk_config}
        url = reverse('horizon:project:instances:resize',
                      args=[server_id])
        return self.client.post(url, formData)

    instance_resize_post_stubs = {
        api.nova: ('server_get', 'server_resize',
                   'flavor_list', 'flavor_get',
                   'is_feature_available')}

    @helpers.create_mocks(instance_resize_post_stubs)
    def test_instance_resize_post(self):
        server = self.servers.first()
        flavors = [flavor for flavor in self.flavors.list()
                   if flavor.id != server.flavor['id']]
        flavor = flavors[0]

        self.mock_server_get.return_value = server
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_server_resize.return_value = []

        res = self._instance_resize_post(server.id, flavor.id, 'AUTO')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(helpers.IsHttpRequest(),
                                                     server.id)
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self.mock_server_resize.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, flavor.id, 'AUTO')

    @helpers.create_mocks(instance_resize_post_stubs)
    def test_instance_resize_post_api_exception(self):
        server = self.servers.first()
        flavors = [flavor for flavor in self.flavors.list()
                   if flavor.id != server.flavor['id']]
        flavor = flavors[0]

        self.mock_server_get.return_value = server
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_server_resize.side_effect = self.exceptions.nova

        res = self._instance_resize_post(server.id, flavor.id, 'AUTO')
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(helpers.IsHttpRequest(),
                                                     server.id)
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self.mock_server_resize.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, flavor.id, 'AUTO')

    @helpers.create_mocks({api.glance: ('image_list_detailed',),
                           api.nova: ('server_get',
                                      'is_feature_available',)})
    def test_rebuild_instance_get(self, expect_password_fields=True):
        server = self.servers.first()
        self._mock_glance_image_list_detailed(self.images.list())
        self.mock_is_feature_available.return_value = False
        self.mock_server_get.return_value = server

        url = reverse('horizon:project:instances:rebuild', args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'project/instances/rebuild.html')

        password_field_label = 'Rebuild Password'
        if expect_password_fields:
            self.assertContains(res, password_field_label)
        else:
            self.assertNotContains(res, password_field_label)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self._check_glance_image_list_detailed(count=4)
        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), "instance_description"
        )

    @django.test.utils.override_settings(
        OPENSTACK_HYPERVISOR_FEATURES={'can_set_password': False})
    def test_rebuild_instance_get_without_set_password(self):
        self.test_rebuild_instance_get(expect_password_fields=False)

    def _instance_rebuild_post(self, server_id, image_id,
                               password=None, confirm_password=None,
                               disk_config=None):
        form_data = {'instance_id': server_id,
                     'image': image_id,
                     'disk_config': disk_config}
        if password is not None:
            form_data.update(password=password)
        if confirm_password is not None:
            form_data.update(confirm_password=confirm_password)
        url = reverse('horizon:project:instances:rebuild',
                      args=[server_id])
        return self.client.post(url, form_data)

    instance_rebuild_post_stubs = {
        api.nova: ('server_get',
                   'server_rebuild',
                   'is_feature_available',),
        api.glance: ('image_list_detailed',)}

    @helpers.create_mocks(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_with_password(self):
        server = self.servers.first()
        image = self.images.first()
        password = 'testpass'

        self.mock_server_get.return_value = server
        self._mock_glance_image_list_detailed(self.images.list())
        self.mock_server_rebuild.return_value = []
        self.mock_is_feature_available.return_value = False

        res = self._instance_rebuild_post(server.id, image.id,
                                          password=password,
                                          confirm_password=password,
                                          disk_config='AUTO')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self._check_glance_image_list_detailed(count=4)
        self.mock_server_rebuild.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, image.id, password, 'AUTO',
            description=None)
        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), "instance_description"
        )

    @helpers.create_mocks(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_with_password_equals_none(self):
        server = self.servers.first()
        image = self.images.first()

        self.mock_server_get.return_value = server
        self._mock_glance_image_list_detailed(self.images.list())
        self.mock_server_rebuild.side_effect = self.exceptions.nova
        self.mock_is_feature_available.return_value = False

        res = self._instance_rebuild_post(server.id, image.id,
                                          password=None,
                                          confirm_password=None,
                                          disk_config='AUTO')
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self._check_glance_image_list_detailed(count=4)
        self.mock_server_rebuild.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, image.id, None, 'AUTO',
            description=None)
        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), "instance_description"
        )

    @helpers.create_mocks(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_password_do_not_match(self):
        server = self.servers.first()
        image = self.images.first()
        pass1 = 'somepass'
        pass2 = 'notsomepass'

        self.mock_server_get.return_value = server
        self._mock_glance_image_list_detailed(self.images.list())
        self.mock_is_feature_available.return_value = False

        res = self._instance_rebuild_post(server.id, image.id,
                                          password=pass1,
                                          confirm_password=pass2,
                                          disk_config='MANUAL')

        self.assertEqual(res.context['form'].errors['__all__'],
                         ["Passwords do not match."])

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self._check_glance_image_list_detailed(count=8)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_feature_available, 2,
            mock.call(helpers.IsHttpRequest(), 'instance_description'))

    @helpers.create_mocks(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_with_empty_string(self):
        server = self.servers.first()
        image = self.images.first()

        self.mock_server_get.return_value = server
        self._mock_glance_image_list_detailed(self.images.list())
        self.mock_server_rebuild.return_value = []
        self.mock_is_feature_available.return_value = False

        res = self._instance_rebuild_post(server.id, image.id,
                                          password='',
                                          confirm_password='',
                                          disk_config='AUTO')
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self._check_glance_image_list_detailed(count=4)
        self.mock_server_rebuild.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, image.id, None, 'AUTO',
            description=None)
        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), "instance_description"
        )

    @helpers.create_mocks(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_with_desc(self):
        server = self.servers.first()
        image = self.images.first()
        test_description = 'test description'

        self.mock_server_get.return_value = server
        self._mock_glance_image_list_detailed(self.images.list())
        self.mock_server_rebuild.return_value = []
        self.mock_is_feature_available.return_value = True

        form_data = {'instance_id': server.id,
                     'image': image.id,
                     'description': test_description}
        url = reverse('horizon:project:instances:rebuild',
                      args=[server.id])
        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self._check_glance_image_list_detailed(count=4)
        self.mock_server_rebuild.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, image.id, None, '',
            description=test_description)
        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), "instance_description"
        )

    @helpers.create_mocks(instance_rebuild_post_stubs)
    def test_rebuild_instance_post_api_exception(self):
        server = self.servers.first()
        image = self.images.first()
        password = 'testpass'

        self.mock_server_get.return_value = server
        self._mock_glance_image_list_detailed(self.images.list())
        self.mock_server_rebuild.side_effect = self.exceptions.nova
        self.mock_is_feature_available.return_value = False

        res = self._instance_rebuild_post(server.id, image.id,
                                          password=password,
                                          confirm_password=password,
                                          disk_config='AUTO')
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_server_get.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self._check_glance_image_list_detailed(count=4)
        self.mock_server_rebuild.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, image.id, password, 'AUTO',
            description=None)
        self.mock_is_feature_available.assert_called_once_with(
            helpers.IsHttpRequest(), "instance_description"
        )

    @django.test.utils.override_settings(API_RESULT_PAGE_SIZE=2)
    @helpers.create_mocks({
        api.nova: ('flavor_list',
                   'server_list_paged',
                   'tenant_absolute_limits',
                   'is_feature_available',),
        api.glance: ('image_list_detailed',),
        api.neutron: ('floating_ip_simple_associate_supported',
                      'floating_ip_supported',),
        api.network: ('servers_update_addresses',),
        api.cinder: ('volume_list',),
    })
    def test_index_form_action_with_pagination(self):
        # The form action on the next page should have marker
        # object from the previous page last element.
        page_size = settings.API_RESULT_PAGE_SIZE
        servers = self.servers.list()[:3]

        self.mock_is_feature_available.return_value = True
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)

        self.mock_server_list_paged.side_effect = [
            [servers[:page_size], True, False],
            [servers[page_size:], False, False]
        ]
        self.mock_servers_update_addresses.return_value = None

        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']
        self.mock_floating_ip_supported.return_value = True
        self.mock_floating_ip_simple_associate_supported.return_value = True

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, INDEX_TEMPLATE)
        # get first page with 2 items
        self.assertEqual(len(res.context['instances_table'].data), page_size)

        # update INDEX_URL with marker object
        params = "=".join([tables.InstancesTable._meta.pagination_param,
                           servers[page_size - 1].id])
        next_page_url = "?".join([reverse('horizon:project:instances:index'),
                                  params])
        form_action = 'action="%s"' % next_page_url

        res = self.client.get(next_page_url)
        # get next page with remaining items (item 3)
        self.assertEqual(len(res.context['instances_table'].data), 1)
        # ensure that marker object exists in form action
        self.assertContains(res, form_action, count=1)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_feature_available, 6,
            mock.call(helpers.IsHttpRequest(), 'locked_attribute'))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_flavor_list, 2,
            mock.call(helpers.IsHttpRequest()))
        self._assert_mock_image_list_detailed_calls_double()

        self.mock_server_list_paged.assert_has_calls([
            mock.call(helpers.IsHttpRequest(),
                      sort_dir='desc',
                      search_opts={'marker': None, 'paginate': True}),
            mock.call(helpers.IsHttpRequest(),
                      sort_dir='desc',
                      search_opts={'marker': servers[page_size - 1].id,
                                   'paginate': True}),
        ])
        self.assertEqual(2, self.mock_server_list_paged.call_count)
        self.mock_servers_update_addresses.assert_has_calls([
            mock.call(helpers.IsHttpRequest(), servers[:page_size]),
            mock.call(helpers.IsHttpRequest(), servers[page_size:]),
        ])
        self.assertEqual(2, self.mock_servers_update_addresses.call_count)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_tenant_absolute_limits, 4,
            mock.call(helpers.IsHttpRequest(), reserved=True))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_supported, 6,
            mock.call(helpers.IsHttpRequest()))
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_floating_ip_simple_associate_supported, 3,
            mock.call(helpers.IsHttpRequest()))

    @django.test.utils.override_settings(API_RESULT_PAGE_SIZE=2)
    @helpers.create_mocks({api.nova: ('server_list_paged',
                                      'flavor_list',
                                      'server_delete',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_delete_instance_with_pagination(self):
        # Instance should be deleted from the next page.

        page_size = settings.API_RESULT_PAGE_SIZE
        servers = self.servers.list()[:3]
        server = servers[-1]

        self.mock_server_list_paged.return_value = [
            servers[page_size:], False, True]
        self.mock_servers_update_addresses.return_value = None
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_delete.return_value = None

        # update INDEX_URL with marker object
        params = "=".join([tables.InstancesTable._meta.pagination_param,
                           servers[page_size - 1].id])
        next_page_url = "?".join([reverse('horizon:project:instances:index'),
                                  params])
        formData = {'action': 'instances__delete__%s' % server.id}
        res = self.client.post(next_page_url, formData)

        self.assertRedirectsNoFollow(res, next_page_url)
        self.assertMessageCount(info=1)

        search_opts = {'marker': servers[page_size - 1].id, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers[page_size:])
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        self.mock_server_delete.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    class SimpleFile(object):
        def __init__(self, name, data, size):
            self.name = name
            self.data = data
            self._size = size

        def read(self):
            return self.data

    def _server_rescue_post(self, server_id, image_id,
                            password=None):
        form_data = {'instance_id': server_id,
                     'image': image_id}
        if password is not None:
            form_data["password"] = password
        url = reverse('horizon:project:instances:rescue',
                      args=[server_id])
        return self.client.post(url, form_data)

    @helpers.create_mocks({api.nova: ('server_rescue',),
                           api.glance: ('image_list_detailed',)})
    def test_rescue_instance_post(self):
        server = self.servers.first()
        image = self.images.first()
        password = 'testpass'
        self._mock_glance_image_list_detailed(self.images.list())
        self.mock_server_rescue.return_value = []
        res = self._server_rescue_post(server.id, image.id,
                                       password=password)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self._check_glance_image_list_detailed(count=4)
        self.mock_server_rescue.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, image=image.id,
            password=password)

    @helpers.create_mocks({api.nova: ('server_list_paged',
                                      'flavor_list',
                                      'server_unrescue',),
                           api.glance: ('image_list_detailed',),
                           api.network: ('servers_update_addresses',),
                           api.cinder: ('volume_list',)})
    def test_unrescue_instance(self):
        servers = self.servers.list()
        server = servers[0]
        server.status = "RESCUE"

        self.mock_server_list_paged.return_value = [servers, False, False]
        self.mock_servers_update_addresses.return_value = None
        self.mock_flavor_list.return_value = self.flavors.list()
        self.mock_image_list_detailed.return_value = (self.images.list(),
                                                      False, False)
        self.mock_server_unrescue.return_value = None

        formData = {'action': 'instances__unrescue__%s' % server.id}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

        search_opts = {'marker': None, 'paginate': True}
        self.mock_server_list_paged.assert_called_once_with(
            helpers.IsHttpRequest(),
            sort_dir='desc',
            search_opts=search_opts)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), servers)
        self.mock_flavor_list.assert_called_once_with(helpers.IsHttpRequest())
        self._assert_mock_image_list_detailed_calls()

        self.mock_server_unrescue.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)


class InstanceAjaxTests(helpers.TestCase):
    @helpers.create_mocks({api.nova: ("server_get",
                                      "flavor_get",
                                      "is_feature_available",
                                      "tenant_absolute_limits"),
                           api.network: ('servers_update_addresses',)})
    def test_row_update(self):
        server = self.servers.first()
        instance_id = server.id
        flavor_id = server.flavor["id"]
        flavors = self.flavors.list()
        full_flavors = collections.OrderedDict([(f.id, f) for f in flavors])

        self.mock_is_feature_available.return_value = True
        self.mock_server_get.return_value = server
        self.mock_flavor_get.return_value = full_flavors[flavor_id]
        self.mock_servers_update_addresses.return_value = None
        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']

        params = {'action': 'row_update',
                  'table': 'instances',
                  'obj_id': instance_id,
                  }
        res = self.client.get('?'.join((INDEX_URL, urlencode(params))),
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(res, server.name)

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_feature_available, 2,
            mock.call(helpers.IsHttpRequest(), 'locked_attribute'))
        self.mock_server_get.assert_called_once_with(helpers.IsHttpRequest(),
                                                     instance_id)
        self.mock_flavor_get.assert_called_once_with(helpers.IsHttpRequest(),
                                                     flavor_id)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), [server])
        self.mock_tenant_absolute_limits.assert_called_once_with(
            helpers.IsHttpRequest(), reserved=True)

    @helpers.create_mocks({api.nova: ("server_get",
                                      "flavor_get",
                                      'is_feature_available',
                                      "tenant_absolute_limits"),
                           api.network: ('servers_update_addresses',)})
    def test_row_update_instance_error(self):
        server = self.servers.first()
        instance_id = server.id
        flavor_id = server.flavor["id"]
        flavors = self.flavors.list()
        full_flavors = collections.OrderedDict([(f.id, f) for f in flavors])

        server.status = 'ERROR'
        server.fault = {"message": "NoValidHost",
                        "code": 500,
                        "details": "No valid host was found. \n  "
                                   "File \"/mnt/stack/nova/nova/"
                                   "scheduler/filter_scheduler.py\", "
                                   "line 105, in schedule_run_instance\n    "
                                   "raise exception.NoValidHost"
                                   "(reason=\"\")\n",
                        "created": "2013-10-07T00:08:32Z"}

        self.mock_is_feature_available.return_value = True
        self.mock_server_get.return_value = server
        self.mock_flavor_get.return_value = full_flavors[flavor_id]
        self.mock_servers_update_addresses.return_value = None
        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']

        params = {'action': 'row_update',
                  'table': 'instances',
                  'obj_id': instance_id,
                  }
        res = self.client.get('?'.join((INDEX_URL, urlencode(params))),
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(res, server.name)
        self.assertTrue(res.has_header('X-Horizon-Messages'))
        messages = json.loads(res['X-Horizon-Messages'])
        self.assertEqual(len(messages), 1)
        # (Pdb) messages
        # [['error', 'Failed to launch instance "server_1": \
        # There is not enough capacity for this flavor in the \
        # selected availability zone. Try again later or select \
        # a different availability zone.', '']]
        self.assertEqual(messages[0][0], 'error')
        self.assertTrue(messages[0][1].startswith('Failed'))

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_feature_available, 2,
            mock.call(helpers.IsHttpRequest(), 'locked_attribute'))
        self.mock_server_get.assert_called_once_with(helpers.IsHttpRequest(),
                                                     instance_id)
        self.mock_flavor_get.assert_called_once_with(helpers.IsHttpRequest(),
                                                     flavor_id)
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), [server])
        self.mock_tenant_absolute_limits.assert_called_once_with(
            helpers.IsHttpRequest(), reserved=True)

    @helpers.create_mocks({api.nova: ("server_get",
                                      "flavor_get",
                                      'is_feature_available',
                                      "tenant_absolute_limits"),
                           api.network: ('servers_update_addresses',)})
    def test_row_update_flavor_not_found(self):
        server = self.servers.first()
        instance_id = server.id

        self.mock_is_feature_available.return_value = True
        self.mock_server_get.return_value = server
        self.mock_flavor_get.side_effect = self.exceptions.nova
        self.mock_servers_update_addresses.return_value = None
        self.mock_tenant_absolute_limits.return_value = self.limits['absolute']

        params = {'action': 'row_update',
                  'table': 'instances',
                  'obj_id': instance_id,
                  }
        res = self.client.get('?'.join((INDEX_URL, urlencode(params))),
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(res, server.name)
        self.assertContains(res, "Not available")

        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_is_feature_available, 2,
            mock.call(helpers.IsHttpRequest(), 'locked_attribute'))
        self.mock_server_get.assert_called_once_with(helpers.IsHttpRequest(),
                                                     instance_id)
        self.mock_flavor_get.assert_called_once_with(helpers.IsHttpRequest(),
                                                     server.flavor['id'])
        self.mock_servers_update_addresses.assert_called_once_with(
            helpers.IsHttpRequest(), [server])
        self.mock_tenant_absolute_limits.assert_called_once_with(
            helpers.IsHttpRequest(), reserved=True)


class ConsoleManagerTests(helpers.ResetImageAPIVersionMixin, helpers.TestCase):

    def setup_consoles(self):
        # Need to refresh with mocks or will fail since mock do not detect
        # the api_call() as mocked.
        console.CONSOLES = collections.OrderedDict([
            ('VNC', api.nova.server_vnc_console),
            ('SPICE', api.nova.server_spice_console),
            ('RDP', api.nova.server_rdp_console),
            ('SERIAL', api.nova.server_serial_console)])

    def _get_console_vnc(self, server):
        console_mock = mock.Mock(spec=api.nova.VNCConsole)
        console_mock.url = '/VNC'
        self.mock_server_vnc_console.return_value = console_mock
        self.setup_consoles()

    @helpers.create_mocks({api.nova: ('server_vnc_console',)})
    def test_get_console_vnc(self):
        server = self.servers.first()
        self._get_console_vnc(server)
        url = '/VNC&title=%s(%s)' % (server.name, server.id)
        data = console.get_console(self.request, 'VNC', server)[1]
        self.assertEqual(data, url)
        self.mock_server_vnc_console.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    def _get_console_spice(self, server):
        console_mock = mock.Mock(spec=api.nova.SPICEConsole)
        console_mock.url = '/SPICE'
        self.mock_server_spice_console.return_value = console_mock
        self.setup_consoles()

    @helpers.create_mocks({api.nova: ('server_spice_console',)})
    def test_get_console_spice(self):
        server = self.servers.first()
        self._get_console_spice(server)
        url = '/SPICE&title=%s(%s)' % (server.name, server.id)
        data = console.get_console(self.request, 'SPICE', server)[1]
        self.assertEqual(data, url)
        self.mock_server_spice_console.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    def _get_console_rdp(self, server):
        console_mock = mock.Mock(spec=api.nova.RDPConsole)
        console_mock.url = '/RDP'
        self.mock_server_rdp_console.return_value = console_mock
        self.setup_consoles()

    @helpers.create_mocks({api.nova: ('server_rdp_console',)})
    def test_get_console_rdp(self):
        server = self.servers.first()
        self._get_console_rdp(server)
        url = '/RDP&title=%s(%s)' % (server.name, server.id)
        data = console.get_console(self.request, 'RDP', server)[1]
        self.assertEqual(data, url)
        self.mock_server_rdp_console.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    def _get_console_serial(self, server):
        console_mock = mock.Mock(spec=api.nova.SerialConsole)
        console_mock.url = '/SERIAL'
        self.mock_server_serial_console.return_value = console_mock
        self.setup_consoles()

    @helpers.create_mocks({api.nova: ('server_serial_console',)})
    def test_get_console_serial(self):
        server = self.servers.first()
        self._get_console_serial(server)
        url = '/SERIAL'
        data = console.get_console(self.request, 'SERIAL', server)[1]
        self.assertEqual(data, url)
        self.mock_server_serial_console.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_vnc_console',
                                      'server_spice_console',
                                      'server_rdp_console')})
    def test_get_console_auto_iterate_available(self):
        server = self.servers.first()

        console_mock = mock.Mock(spec=api.nova.RDPConsole)
        console_mock.url = '/RDP'

        self.mock_server_vnc_console.side_effect = self.exceptions.nova
        self.mock_server_spice_console.side_effect = self.exceptions.nova
        self.mock_server_rdp_console.return_value = console_mock

        self.setup_consoles()

        url = '/RDP&title=%s(%s)' % (server.name, server.id)
        data = console.get_console(self.request, 'AUTO', server)[1]
        self.assertEqual(data, url)

        self.mock_server_vnc_console.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_server_spice_console.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_server_rdp_console.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('server_vnc_console',
                                      'server_spice_console',
                                      'server_rdp_console',
                                      'server_serial_console')})
    def test_get_console_auto_iterate_serial_available(self):
        server = self.servers.first()

        console_mock = mock.Mock(spec=api.nova.SerialConsole)
        console_mock.url = '/SERIAL'

        self.mock_server_vnc_console.side_effect = self.exceptions.nova
        self.mock_server_spice_console.side_effect = self.exceptions.nova
        self.mock_server_rdp_console.side_effect = self.exceptions.nova
        self.mock_server_serial_console.return_value = console_mock

        self.setup_consoles()

        url = '/SERIAL'
        data = console.get_console(self.request, 'AUTO', server)[1]
        self.assertEqual(data, url)

        self.mock_server_vnc_console.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_server_spice_console.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_server_rdp_console.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_server_serial_console.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    def test_invalid_console_type_raise_value_error(self):
        self.assertRaises(exceptions.NotAvailable,
                          console.get_console, None, 'FAKE', None)

    @helpers.create_mocks({api.neutron: ('network_list_for_tenant',
                                         'port_list_with_trunk_types')})
    def test_interface_attach_get(self):
        server = self.servers.first()
        tenant_networks = [net for net in self.networks.list()
                           if not net['router:external']]
        net1 = tenant_networks[0]
        self.mock_network_list_for_tenant.return_value = tenant_networks
        ports = self.ports.list()
        # Pick up the first unbound port for check
        unbound_port = [p for p in ports if not p.device_owner][0]
        self.mock_port_list_with_trunk_types.return_value = ports

        url = reverse('horizon:project:instances:attach_interface',
                      args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res,
                                'project/instances/attach_interface.html')
        expected_label = (
            '%(port_name)s (%(ip_address)s) - %(net_name)s'
            % {'port_name': unbound_port.name_or_id,
               'ip_address': unbound_port.fixed_ips[0]['ip_address'],
               'net_name': net1.name_or_id}
        )
        self.assertContains(res, expected_label)
        self.mock_network_list_for_tenant.assert_has_calls([
            mock.call(helpers.IsHttpRequest(), self.tenant.id),
            mock.call(helpers.IsHttpRequest(), self.tenant.id),
        ])
        self.assertEqual(2, self.mock_network_list_for_tenant.call_count)
        self.mock_port_list_with_trunk_types.assert_called_once_with(
            helpers.IsHttpRequest(), tenant_id=self.tenant.id)

    @helpers.create_mocks({api.neutron: ('network_list_for_tenant',
                                         'port_list_with_trunk_types'),
                           api.nova: ('interface_attach',)})
    def _test_interface_attach_post(self, by_port=False):
        fixed_ip = '10.0.0.10'
        server = self.servers.first()
        network = self.networks.first()
        ports = self.ports.list()
        # Pick up the first unbound port for check
        unbound_port = [p for p in ports if not p.device_owner][0]

        self.mock_network_list_for_tenant.return_value = [network]
        self.mock_port_list_with_trunk_types.return_value = ports
        self.mock_interface_attach.return_value = None

        if by_port:
            form_data = {
                'instance_id': server.id,
                'specification_method': 'port',
                'port': unbound_port.id,
            }
        else:
            form_data = {
                'instance_id': server.id,
                'specification_method': 'network',
                'network': network.id,
                'fixed_ip': fixed_ip,
            }

        url = reverse('horizon:project:instances:attach_interface',
                      args=[server.id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_network_list_for_tenant.assert_has_calls([
            mock.call(helpers.IsHttpRequest(), self.tenant.id),
            mock.call(helpers.IsHttpRequest(), self.tenant.id),
        ])
        self.assertEqual(2, self.mock_network_list_for_tenant.call_count)
        self.mock_port_list_with_trunk_types.assert_called_once_with(
            helpers.IsHttpRequest(), tenant_id=self.tenant.id)
        if by_port:
            self.mock_interface_attach.assert_called_once_with(
                helpers.IsHttpRequest(), server.id,
                net_id=None, fixed_ip=None, port_id=unbound_port.id)
        else:
            self.mock_interface_attach.assert_called_once_with(
                helpers.IsHttpRequest(), server.id,
                net_id=network.id, fixed_ip=fixed_ip, port_id=None)

    def test_interface_attach_post_by_network(self):
        self._test_interface_attach_post()

    def test_interface_attach_post_by_port(self):
        self._test_interface_attach_post(by_port=True)

    @helpers.create_mocks({api.cinder: ('volume_list',)})
    def test_volume_attach_get(self):
        server = self.servers.first()

        self.mock_volume_list.return_value = self.cinder_volumes.list()

        url = reverse('horizon:project:instances:attach_volume',
                      args=[server.id])

        res = self.client.get(url)

        form = res.context['form']

        self.assertEqual(res.status_code, 200)
        self.assertFalse(form.fields['device'].required)
        self.assertIsInstance(form.fields['volume'].widget,
                              forms.ThemableSelectWidget)
        self.assertTemplateUsed(res,
                                'project/instances/attach_volume.html')
        self.mock_volume_list.assert_called_once_with(helpers.IsHttpRequest())

    @helpers.create_mocks({api.nova: ('instance_volume_attach',),
                           api.cinder: ('volume_list',)})
    def test_volume_attach_post(self):
        server = self.servers.first()
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_instance_volume_attach.return_value = None
        volume = self.cinder_volumes.list()[1]

        # note that 'device' is not passed
        form_data = {"volume": volume.id,
                     "instance_id": server.id}

        url = reverse('horizon:project:instances:attach_volume',
                      args=[server.id])

        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_volume_list.assert_called_once_with(helpers.IsHttpRequest())
        self.mock_instance_volume_attach.assert_called_once_with(
            helpers.IsHttpRequest(), volume.id, server.id, None)

    @mock.patch.object(api.cinder, 'volume_list')
    @mock.patch.object(api.cinder, 'volume_get')
    @mock.patch.object(api.nova, 'get_microversion', return_value='2.60')
    @mock.patch.object(api._nova, 'novaclient')
    def test_volume_attach_post_multiattach(
            self, mock_client, mock_get_microversion, mock_volume_get,
            mock_volume_list):
        # Tests that a multiattach volume must be attached with compute API
        # microversion 2.60 and the feature is supported.
        server = self.servers.first()
        volumes = self.cinder_volumes.list()
        volume = volumes[1]
        volume.multiattach = True
        mock_volume_list.return_value = volumes
        mock_volume_get.return_value = volume

        # note that 'device' is not passed
        form_data = {"volume": volume.id,
                     "instance_id": server.id}

        url = reverse('horizon:project:instances:attach_volume',
                      args=[server.id])

        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        mock_client.assert_called_once_with(mock.ANY, '2.60')

    @mock.patch.object(api.cinder, 'volume_list')
    @mock.patch.object(api.cinder, 'volume_get')
    @mock.patch.object(api.nova, 'get_microversion', return_value=None)
    @mock.patch.object(api._nova, 'novaclient')
    def test_volume_attach_post_multiattach_feature_not_available(
            self, mock_client, mock_get_microversion, mock_volume_get,
            mock_volume_list):
        # Tests that a multiattach volume must be attached with compute API
        # microversion 2.60 and the feature is not available.
        server = self.servers.first()
        volumes = self.cinder_volumes.list()
        volume = volumes[1]
        volume.multiattach = True
        mock_volume_list.return_value = volumes
        mock_volume_get.return_value = volume

        # note that 'device' is not passed
        form_data = {"volume": volume.id,
                     "instance_id": server.id}

        url = reverse('horizon:project:instances:attach_volume',
                      args=[server.id])

        self.client.post(url, form_data)
        # TODO(mriedem): Assert the actual error from the response but
        # the test helpers don't seem to handle this case.
        mock_client.assert_not_called()

    @helpers.create_mocks({
        api.cinder: ('volume_list',
                     'volume_get',),
        api.nova: ('get_microversion',),
        api._nova: ('novaclient',),
    })
    def test_multiattach_volume_attach_to_multple_server(self):
        # Tests that a multiattach volume must be attached with compute API
        # microversion 2.60 and the feature is not available.
        server1 = self.servers.list()[0]
        server2 = self.servers.list()[1]
        volumes = self.cinder_volumes.list()
        volume = volumes[1]
        volume.multiattach = True
        self.mock_volume_list.return_value = volumes
        self.mock_volume_get.return_value = volume
        self.mock_get_microversion.return_value = api_versions.APIVersion(
            '2.60')

        # note that 'device' is not passed
        form_data = {"volume": volume.id,
                     "instance_id": server1.id}

        url = reverse('horizon:project:instances:attach_volume',
                      args=[server1.id])

        s1 = self.client.post(url, form_data)
        self.assertNoFormErrors(s1)

        # note that device is not passed
        form_data = {"volume": volume.id,
                     "instance_id": server2.id}

        url = reverse('horizon:project:instances:attach_volume',
                      args=[server2.id])

        s2 = self.client.post(url, form_data)
        self.assertNoFormErrors(s2)
        self.mock_volume_list.assert_has_calls([
            mock.call(helpers.IsHttpRequest()),
            mock.call(helpers.IsHttpRequest())])
        self.assertEqual(self.mock_volume_list.call_count, 2)
        self.mock_volume_get.assert_has_calls([
            mock.call(helpers.IsHttpRequest(), volume.id)
        ])
        self.assertEqual(self.mock_volume_get.call_count, 2)
        self.mock_get_microversion.assert_has_calls([
            mock.call(helpers.IsHttpRequest(), 'multiattach')

        ])
        self.assertEqual(self.mock_get_microversion.call_count, 2)

    @helpers.create_mocks({api.nova: ('instance_volumes_list',)})
    def test_volume_detach_get(self):
        server = self.servers.first()

        self.mock_instance_volumes_list.return_value = \
            self.cinder_volumes.list()

        url = reverse('horizon:project:instances:detach_volume',
                      args=[server.id])

        res = self.client.get(url)
        form = res.context['form']

        self.assertIsInstance(form.fields['volume'].widget,
                              forms.ThemableSelectWidget)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                                'project/instances/detach_volume.html')
        self.mock_instance_volumes_list.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)

    @helpers.create_mocks({api.nova: ('instance_volumes_list',
                                      'instance_volume_detach')})
    def test_volume_detach_post(self):
        server = self.servers.first()
        volume = self.cinder_volumes.list()[1]

        self.mock_instance_volumes_list.return_value = \
            self.cinder_volumes.list()
        self.mock_instance_volume_detach.return_value = None

        form_data = {"volume": volume.id,
                     "instance_id": server.id}

        url = reverse('horizon:project:instances:detach_volume',
                      args=[server.id])

        res = self.client.post(url, form_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_instance_volumes_list.assert_called_once_with(
            helpers.IsHttpRequest(), server.id)
        self.mock_instance_volume_detach.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, volume.id)

    @helpers.create_mocks({api.neutron: ('port_list',)})
    def test_interface_detach_get(self):
        server = self.servers.first()
        self.mock_port_list.return_value = [self.ports.first()]

        url = reverse('horizon:project:instances:detach_interface',
                      args=[server.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res,
                                'project/instances/detach_interface.html')
        self.mock_port_list.assert_called_once_with(helpers.IsHttpRequest(),
                                                    device_id=server.id)

    @helpers.create_mocks({api.neutron: ('port_list',),
                           api.nova: ('interface_detach',)})
    def test_interface_detach_post(self):
        server = self.servers.first()
        port = self.ports.first()
        self.mock_port_list.return_value = [port]
        self.mock_interface_detach.return_value = None

        form_data = {'instance_id': server.id,
                     'port': port.id}

        url = reverse('horizon:project:instances:detach_interface',
                      args=[server.id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.mock_port_list.assert_called_once_with(helpers.IsHttpRequest(),
                                                    device_id=server.id)
        self.mock_interface_detach.assert_called_once_with(
            helpers.IsHttpRequest(), server.id, port.id)
