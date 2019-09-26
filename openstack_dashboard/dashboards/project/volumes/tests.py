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

import copy

import mock
import six

from django.conf import settings
from django.forms import widgets
from django.template.defaultfilters import slugify
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.http import urlunquote

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.dashboards.project.volumes \
    import tables as volume_tables
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


DETAIL_URL = ('horizon:project:volumes:detail')
INDEX_URL = reverse('horizon:project:volumes:index')
SEARCH_OPTS = dict(status=api.cinder.VOLUME_STATE_AVAILABLE)
ATTACHMENT_ID = '6061364b-6612-48a9-8fee-1a38fe072547'


class VolumeIndexViewTests(test.ResetImageAPIVersionMixin, test.TestCase):
    @test.create_mocks({
        api.nova: ['server_get', 'server_list'],
        api.cinder: ['volume_backup_supported',
                     'volume_snapshot_list',
                     'volume_list_paged',
                     'tenant_absolute_limits',
                     'group_list'],
    })
    def _test_index(self, with_attachments=False, with_groups=False):
        vol_snaps = self.cinder_volume_snapshots.list()
        volumes = self.cinder_volumes.list()
        if with_attachments:
            server = self.servers.first()
        else:
            for volume in volumes:
                volume.attachments = []

        self.mock_volume_backup_supported.return_value = False
        if with_groups:
            self.mock_group_list.return_value = self.cinder_groups.list()
            volumes = self.cinder_group_volumes.list()

        self.mock_volume_list_paged.return_value = [volumes, False, False]
        if with_attachments:
            self.mock_server_get.return_value = server

            self.mock_server_list.return_value = [self.servers.list(), False]
            self.mock_volume_snapshot_list.return_value = vol_snaps

        self.mock_tenant_absolute_limits.return_value = \
            self.cinder_limits['absolute']

        res = self.client.get(INDEX_URL)

        if with_attachments:
            self.mock_server_list.assert_called_once_with(test.IsHttpRequest(),
                                                          search_opts=None)
            self.mock_volume_snapshot_list.assert_called_once()

        if with_groups:
            self.mock_group_list.assert_called_once_with(test.IsHttpRequest(),
                                                         search_opts=None)

        self.mock_volume_backup_supported.assert_called_with(
            test.IsHttpRequest())
        self.mock_volume_list_paged.assert_called_once_with(
            test.IsHttpRequest(), marker=None, search_opts=None,
            sort_dir='desc', paginate=True)
        self.mock_tenant_absolute_limits.assert_called_with(
            test.IsHttpRequest())
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')

    def test_index_with_volume_attachments(self):
        self._test_index(True)

    def test_index_no_volume_attachments(self):
        self._test_index(False)

    def test_index_with_volume_groups(self):
        self._test_index(with_groups=True)

    @test.create_mocks({
        api.nova: ['server_get', 'server_list'],
        cinder: ['tenant_absolute_limits',
                 'volume_list_paged',
                 'volume_backup_supported',
                 'volume_snapshot_list'],
    })
    def _test_index_paginated(self, marker, sort_dir, volumes, url,
                              has_more, has_prev):
        backup_supported = True
        vol_snaps = self.cinder_volume_snapshots.list()
        server = self.servers.first()

        self.mock_volume_backup_supported.return_value = backup_supported
        self.mock_volume_list_paged.return_value = [volumes,
                                                    has_more, has_prev]
        self.mock_volume_snapshot_list.return_value = vol_snaps
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_server_get.return_value = server
        self.mock_tenant_absolute_limits.return_value = \
            self.cinder_limits['absolute']

        res = self.client.get(urlunquote(url))

        self.assertEqual(2, self.mock_volume_backup_supported.call_count)
        self.mock_volume_list_paged.assert_called_once_with(
            test.IsHttpRequest(), marker=marker, sort_dir=sort_dir,
            search_opts=None, paginate=True)
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=None)
        self.mock_tenant_absolute_limits.assert_called_with(
            test.IsHttpRequest())
        self.mock_server_list.assert_called_once_with(test.IsHttpRequest(),
                                                      search_opts=None)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')

        return res

    def ensure_attachments_exist(self, volumes):
        volumes = copy.copy(volumes)
        for volume in volumes:
            if not volume.attachments:
                volume.attachments.append({
                    "id": "1", "server_id": '1', "device": "/dev/hda",
                    "attachment_id": ATTACHMENT_ID})
        return volumes

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_index_paginated(self):
        volumes = self.ensure_attachments_exist(self.cinder_volumes.list())
        size = settings.API_RESULT_PAGE_SIZE

        # get first page
        expected_volumes = volumes[:size]
        url = INDEX_URL
        res = self._test_index_paginated(None, "desc", expected_volumes, url,
                                         True, False)
        result = res.context['volumes_table'].data
        self.assertItemsEqual(result, expected_volumes)

        # get second page
        expected_volumes = volumes[size:2 * size]
        marker = expected_volumes[0].id
        next = volume_tables.VolumesTable._meta.pagination_param
        url = "?".join([INDEX_URL, "=".join([next, marker])])
        res = self._test_index_paginated(marker, "desc", expected_volumes, url,
                                         True, True)
        result = res.context['volumes_table'].data
        self.assertItemsEqual(result, expected_volumes)

        # get last page
        expected_volumes = volumes[-size:]
        marker = expected_volumes[0].id
        next = volume_tables.VolumesTable._meta.pagination_param
        url = "?".join([INDEX_URL, "=".join([next, marker])])
        res = self._test_index_paginated(marker, "desc", expected_volumes, url,
                                         False, True)
        result = res.context['volumes_table'].data
        self.assertItemsEqual(result, expected_volumes)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_index_paginated_prev_page(self):
        volumes = self.ensure_attachments_exist(self.cinder_volumes.list())
        size = settings.API_RESULT_PAGE_SIZE

        # prev from some page
        expected_volumes = volumes[size:2 * size]
        marker = expected_volumes[0].id
        prev = volume_tables.VolumesTable._meta.prev_pagination_param
        url = "?".join([INDEX_URL, "=".join([prev, marker])])
        res = self._test_index_paginated(marker, "asc", expected_volumes, url,
                                         True, True)
        result = res.context['volumes_table'].data
        self.assertItemsEqual(result, expected_volumes)

        # back to first page
        expected_volumes = volumes[:size]
        marker = expected_volumes[0].id
        prev = volume_tables.VolumesTable._meta.prev_pagination_param
        url = "?".join([INDEX_URL, "=".join([prev, marker])])
        res = self._test_index_paginated(marker, "asc", expected_volumes, url,
                                         True, False)
        result = res.context['volumes_table'].data
        self.assertItemsEqual(result, expected_volumes)


class VolumeViewTests(test.ResetImageAPIVersionMixin, test.TestCase):
    def tearDown(self):
        for volume in self.cinder_volumes.list():
            # VolumeTableMixIn._set_volume_attributes mutates data
            # and cinder_volumes.list() doesn't deep copy
            for att in volume.attachments:
                if 'instance' in att:
                    del att['instance']
        super(VolumeViewTests, self).tearDown()

    @test.create_mocks({
        cinder: ['volume_create', 'volume_snapshot_list',
                 'volume_type_list', 'volume_type_default',
                 'volume_list', 'availability_zone_list',
                 'extension_supported', 'group_list'],
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_list_detailed'],
    })
    def test_create_volume(self):
        volume = self.cinder_volumes.first()
        volume_type = self.cinder_volume_types.first()
        az = self.cinder_availability_zones.first().zoneName
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'type': volume_type.name,
                    'size': 50,
                    'snapshot_source': '',
                    'availability_zone': az}

        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()
        self.mock_volume_snapshot_list.return_value = \
            self.cinder_volume_snapshots.list()
        self.mock_image_list_detailed.return_value = [[], False, False]
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_extension_supported.return_value = True
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_volume_create.return_value = volume
        self.mock_group_list.return_value = []

        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)

        redirect_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redirect_url)

        self.mock_volume_type_default.assert_called_once()
        self.mock_volume_type_list.assert_called_once()
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=SEARCH_OPTS)
        self.mock_availability_zone_list.assert_called_once()
        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_volume_list.assert_called_once_with(test.IsHttpRequest(),
                                                      search_opts=SEARCH_OPTS)
        self.mock_volume_create.assert_called_once_with(
            test.IsHttpRequest(), formData['size'], formData['name'],
            formData['description'], formData['type'], metadata={},
            snapshot_id=None, group_id=None, image_id=None,
            availability_zone=formData['availability_zone'], source_volid=None)
        self.mock_image_list_detailed.assert_called_with(
            test.IsHttpRequest(),
            filters={'visibility': 'shared', 'status': 'active'})
        self.mock_tenant_quota_usages.assert_called_once_with(
            test.IsHttpRequest(),
            targets=('volumes', 'gigabytes'))
        self.mock_group_list.assert_called_with(test.IsHttpRequest())

    @test.create_mocks({
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_list_detailed'],
        cinder: ['extension_supported',
                 'availability_zone_list',
                 'volume_list',
                 'volume_type_default',
                 'volume_type_list',
                 'volume_snapshot_list',
                 'volume_create',
                 'group_list'],
    })
    def test_create_volume_without_name(self):
        volume = self.cinder_volumes.first()
        volume_type = self.cinder_volume_types.first()
        az = self.cinder_availability_zones.first().zoneName
        formData = {'name': '',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'type': volume_type.name,
                    'size': 50,
                    'snapshot_source': '',
                    'availability_zone': az}

        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()
        self.mock_volume_snapshot_list.return_value = \
            self.cinder_volume_snapshots.list()
        self.mock_image_list_detailed.return_value = [self.images.list(),
                                                      False, False]
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()

        self.mock_extension_supported.return_value = True
        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_volume_create.return_value = volume
        self.mock_group_list.return_value = []

        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redirect_url)

        self.mock_volume_type_list.assert_called_once()
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=SEARCH_OPTS)
        self.mock_image_list_detailed.assert_called_with(
            test.IsHttpRequest(),
            filters={'visibility': 'shared', 'status': 'active'})
        self.mock_availability_zone_list.assert_called_once()
        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_volume_type_default.assert_called_once()
        self.mock_volume_list.assert_called_once()
        self.mock_volume_create.assert_called_once_with(
            test.IsHttpRequest(), formData['size'], formData['name'],
            formData['description'], formData['type'], metadata={},
            snapshot_id=None, group_id=None, image_id=None,
            availability_zone=formData['availability_zone'], source_volid=None)
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_list_detailed'],
        cinder: ['extension_supported',
                 'availability_zone_list',
                 'volume_list',
                 'volume_type_default',
                 'volume_type_list',
                 'volume_snapshot_list',
                 'volume_create',
                 'group_list'],
    })
    def test_create_volume_dropdown(self):
        volume = self.cinder_volumes.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 50,
                    'type': '',
                    'volume_source_type': 'no_source_type',
                    'snapshot_source': self.cinder_volume_snapshots.first().id,
                    'image_source': self.images.first().id}

        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_volume_snapshot_list.return_value = \
            self.cinder_volume_snapshots.list()
        self.mock_image_list_detailed.return_value = \
            [self.images.list(), False, False]
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()

        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_group_list.return_value = []

        self.mock_volume_create.return_value = volume

        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redirect_url)

        self.mock_volume_type_default.assert_called_once()
        self.mock_volume_type_list.assert_called_once()
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=SEARCH_OPTS)
        self.mock_image_list_detailed.assert_called_with(
            test.IsHttpRequest(),
            filters={'visibility': 'shared', 'status': 'active'})
        self.mock_volume_list.assert_called_once_with(test.IsHttpRequest(),
                                                      search_opts=SEARCH_OPTS)
        self.mock_tenant_quota_usages.assert_called_once()
        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_availability_zone_list.assert_called_once()
        self.mock_volume_create.assert_called_once_with(
            test.IsHttpRequest(), formData['size'], formData['name'],
            formData['description'], '', metadata={}, snapshot_id=None,
            group_id=None, image_id=None, availability_zone=None,
            source_volid=None)
        self.mock_group_list.assert_called_with(test.IsHttpRequest())

    @test.create_mocks({
        quotas: ['tenant_quota_usages'],
        cinder: ['volume_type_list',
                 'volume_type_default',
                 'volume_get',
                 'volume_snapshot_get',
                 'volume_create',
                 'group_list'],
    })
    def test_create_volume_from_snapshot(self):
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 50,
                    'type': '',
                    'snapshot_source': snapshot.id}

        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()
        self.mock_volume_snapshot_get.return_value = snapshot
        self.mock_volume_get.return_value = self.cinder_volumes.first()
        self.mock_volume_create.return_value = volume
        self.mock_group_list.return_value = []

        # get snapshot from url
        url = reverse('horizon:project:volumes:create')
        res = self.client.post("?".join([url,
                                         "snapshot_id=" + str(snapshot.id)]),
                               formData)

        redirect_url = INDEX_URL

        self.assertRedirectsNoFollow(res, redirect_url)
        self.mock_volume_type_default.assert_called_once()
        self.mock_volume_type_list.assert_called_once()
        self.mock_tenant_quota_usages.assert_called_once()
        self.mock_volume_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), str(snapshot.id))
        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     snapshot.volume_id)
        self.mock_volume_create.assert_called_once_with(
            test.IsHttpRequest(), formData['size'], formData['name'],
            formData['description'], '', metadata={}, snapshot_id=snapshot.id,
            group_id=None, image_id=None, availability_zone=None,
            source_volid=None)
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_list_detailed'],
        cinder: ['extension_supported',
                 'volume_snapshot_list',
                 'volume_snapshot_get',
                 'availability_zone_list',
                 'volume_type_list',
                 'volume_list',
                 'volume_type_default',
                 'volume_get',
                 'volume_create',
                 'group_list'],
    })
    def test_create_volume_from_volume(self):
        volume = self.cinder_volumes.first()

        formData = {'name': u'A copy of a volume',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 50,
                    'type': '',
                    'volume_source_type': 'volume_source',
                    'volume_source': volume.id}

        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_volume_snapshot_list.return_value = \
            self.cinder_volume_snapshots.list()
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()

        self.mock_volume_get.return_value = self.cinder_volumes.first()
        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_image_list_detailed.return_value = \
            [self.images.list(), False, False]
        self.mock_volume_create.return_value = volume
        self.mock_group_list.return_value = []

        url = reverse('horizon:project:volumes:create')
        redirect_url = INDEX_URL
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertMessageCount(info=1)
        self.assertRedirectsNoFollow(res, redirect_url)

        self.mock_volume_type_default.assert_called_once()
        self.mock_volume_list.assert_called_once_with(test.IsHttpRequest(),
                                                      search_opts=SEARCH_OPTS)
        self.mock_volume_type_list.assert_called_once()
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=SEARCH_OPTS)
        self.mock_tenant_quota_usages.assert_called_once()
        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_availability_zone_list.assert_called_once()
        self.mock_image_list_detailed.assert_called_with(
            test.IsHttpRequest(),
            filters={'visibility': 'shared', 'status': 'active'})
        self.mock_volume_create.assert_called_once_with(
            test.IsHttpRequest(), formData['size'], formData['name'],
            formData['description'], None, metadata={}, snapshot_id=None,
            group_id=None, image_id=None, availability_zone=None,
            source_volid=volume.id)
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_list_detailed'],
        cinder: ['extension_supported',
                 'availability_zone_list',
                 'volume_type_list',
                 'volume_list',
                 'volume_type_default',
                 'volume_get',
                 'volume_snapshot_get',
                 'volume_snapshot_list',
                 'volume_create',
                 'group_list'],
    })
    def test_create_volume_from_snapshot_dropdown(self):
        volume = self.cinder_volumes.first()
        snapshot = self.cinder_volume_snapshots.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 50,
                    'type': '',
                    'volume_source_type': 'snapshot_source',
                    'snapshot_source': snapshot.id}

        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_volume_snapshot_list.return_value = \
            self.cinder_volume_snapshots.list()
        self.mock_image_list_detailed.return_value = [self.images.list(),
                                                      False, False]
        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()
        self.mock_volume_snapshot_get.return_value = snapshot
        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_volume_create.return_value = volume
        self.mock_group_list.return_value = []

        # get snapshot from dropdown list
        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redirect_url)

        self.mock_volume_type_list.assert_called_once()
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=SEARCH_OPTS)
        self.mock_image_list_detailed.assert_called_with(
            test.IsHttpRequest(),
            filters={'visibility': 'shared', 'status': 'active'})
        self.mock_volume_type_default.assert_called_once()
        self.mock_volume_list.assert_called_once_with(test.IsHttpRequest(),
                                                      search_opts=SEARCH_OPTS)
        self.mock_tenant_quota_usages.assert_called_once()
        self.mock_volume_snapshot_get.assert_called_once_with(
            test.IsHttpRequest(), str(snapshot.id))
        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_availability_zone_list.assert_called_once()
        self.mock_volume_create.assert_called_once_with(
            test.IsHttpRequest(), formData['size'], formData['name'],
            formData['description'], '', metadata={}, snapshot_id=snapshot.id,
            group_id=None, image_id=None, availability_zone=None,
            source_volid=None)
        self.mock_group_list.assert_called_once_with(test.IsHttpRequest())

    @test.create_mocks({
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_list_detailed'],
        cinder: ['volume_snapshot_get',
                 'volume_type_list',
                 'volume_type_default',
                 'volume_get',
                 'group_list'],
    })
    def test_create_volume_from_snapshot_invalid_size(self):
        snapshot = self.cinder_volume_snapshots.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 20, 'snapshot_source': snapshot.id}

        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()
        self.mock_volume_snapshot_get.return_value = snapshot
        self.mock_volume_get.return_value = self.cinder_volumes.first()
        self.mock_group_list.return_value = []

        url = reverse('horizon:project:volumes:create')
        res = self.client.post("?".join([url,
                                         "snapshot_id=" + str(snapshot.id)]),
                               formData, follow=True)
        self.assertEqual(res.redirect_chain, [])
        self.assertFormError(res, 'form', None,
                             "The volume size cannot be less than the "
                             "snapshot size (40GiB)")
        self.assertEqual(3, self.mock_volume_type_list.call_count)
        self.assertEqual(2, self.mock_volume_type_default.call_count)

        self.mock_volume_snapshot_get.assert_called_with(test.IsHttpRequest(),
                                                         str(snapshot.id))
        self.mock_volume_get.assert_called_with(test.IsHttpRequest(),
                                                snapshot.volume_id)
        self.mock_group_list.assert_called_with(test.IsHttpRequest())

    @test.create_mocks({
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_get'],
        cinder: ['extension_supported',
                 'availability_zone_list',
                 'volume_type_default',
                 'volume_type_list',
                 'volume_create',
                 'group_list'],
    })
    def test_create_volume_from_image(self):
        volume = self.cinder_volumes.first()
        image = self.images.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 40,
                    'type': '',
                    'image_source': image.id}

        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_volume_type_list.ret = self.cinder_volume_types.list()
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()
        self.mock_image_get.return_value = image
        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_group_list.return_value = []

        self.mock_volume_create.return_value = volume

        # get image from url
        url = reverse('horizon:project:volumes:create')
        res = self.client.post("?".join([url,
                                         "image_id=" + str(image.id)]),
                               formData)

        redirect_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redirect_url)

        self.mock_volume_type_default.assert_called_once()
        self.mock_volume_type_list.assert_called_once()
        self.mock_tenant_quota_usages.assert_called_once()
        self.mock_image_get.assert_called_once_with(test.IsHttpRequest(),
                                                    str(image.id))
        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_availability_zone_list.assert_called_once()
        self.mock_volume_create.assert_called_once_with(
            test.IsHttpRequest(), formData['size'], formData['name'],
            formData['description'], '', metadata={}, snapshot_id=None,
            group_id=None, image_id=image.id, availability_zone=None,
            source_volid=None)
        self.mock_group_list.assert_called_with(test.IsHttpRequest())

    @test.create_mocks({
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_list_detailed',
                     'image_get'],
        cinder: ['extension_supported',
                 'availability_zone_list',
                 'volume_snapshot_list',
                 'volume_list',
                 'volume_type_list',
                 'volume_type_default',
                 'volume_create',
                 'group_list'],
    })
    def test_create_volume_from_image_dropdown(self):
        volume = self.cinder_volumes.first()
        image = self.images.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 30,
                    'type': '',
                    'volume_source_type': 'image_source',
                    'snapshot_source': self.cinder_volume_snapshots.first().id,
                    'image_source': image.id}

        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_volume_snapshot_list.return_value = \
            self.cinder_volume_snapshots.list()
        self.mock_image_list_detailed.return_value = [self.images.list(),
                                                      False, False]
        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()
        self.mock_image_get.return_value = image
        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_group_list.return_value = []

        self.mock_volume_create.return_value = volume

        # get image from dropdown list
        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redirect_url)

        self.mock_volume_type_list.assert_called_once()
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=SEARCH_OPTS)
        self.mock_image_list_detailed.assert_called_with(
            test.IsHttpRequest(),
            filters={'visibility': 'shared', 'status': 'active'})
        self.mock_volume_type_default.assert_called_once()
        self.mock_volume_list.assert_called_once_with(test.IsHttpRequest(),
                                                      search_opts=SEARCH_OPTS)
        self.mock_tenant_quota_usages.assert_called_once()
        self.mock_image_get.assert_called_with(test.IsHttpRequest(),
                                               str(image.id))
        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_availability_zone_list.assert_called_once()
        self.mock_volume_create.assert_called_once_with(
            test.IsHttpRequest(), formData['size'], formData['name'],
            formData['description'], '', metadata={}, snapshot_id=None,
            group_id=None, image_id=image.id, availability_zone=None,
            source_volid=None)
        self.mock_group_list.assert_called_with(test.IsHttpRequest())

    @test.create_mocks({
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_get'],
        cinder: ['extension_supported',
                 'availability_zone_list',
                 'volume_type_list',
                 'volume_type_default',
                 'group_list'],
    })
    def test_create_volume_from_image_under_image_size(self):
        image = self.images.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 1, 'image_source': image.id}

        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()
        self.mock_image_get.return_value = image
        self.mock_extension_supported.return_value = True
        self.mock_group_list.return_value = []

        url = reverse('horizon:project:volumes:create')
        res = self.client.post("?".join([url,
                                         "image_id=" + str(image.id)]),
                               formData, follow=True)
        self.assertEqual(res.redirect_chain, [])

        msg = (u"The volume size cannot be less than the "
               u"image size (20.0\xa0GB)")

        self.assertFormError(res, 'form', None, msg)

        self.assertEqual(3, self.mock_volume_type_list.call_count)
        self.assertEqual(2, self.mock_volume_type_default.call_count)

        self.assertEqual(2, self.mock_tenant_quota_usages.call_count)
        self.mock_image_get.assert_called_with(test.IsHttpRequest(),
                                               str(image.id))
        self.mock_extension_supported.assert_called_with(test.IsHttpRequest(),
                                                         'AvailabilityZones')
        self.mock_group_list.assert_called_with(test.IsHttpRequest())

    @test.create_mocks({
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_get'],
        cinder: ['extension_supported',
                 'availability_zone_list',
                 'volume_type_list',
                 'volume_type_default',
                 'group_list'],
    })
    def _test_create_volume_from_image_under_image_min_disk_size(self, image):
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 5, 'image_source': image.id}

        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()
        self.mock_image_get.return_value = image
        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_group_list.return_value = []

        url = reverse('horizon:project:volumes:create')
        res = self.client.post("?".join([url,
                                         "image_id=" + str(image.id)]),
                               formData, follow=True)
        self.assertEqual(res.redirect_chain, [])
        self.assertFormError(res, 'form', None,
                             "The volume size cannot be less than the "
                             "image minimum disk size (30GiB)")
        self.assertEqual(3, self.mock_volume_type_list.call_count)
        self.assertEqual(2, self.mock_volume_type_default.call_count)
        self.assertEqual(2, self.mock_availability_zone_list.call_count)

        self.mock_image_get.assert_called_with(test.IsHttpRequest(),
                                               str(image.id))
        self.mock_extension_supported.assert_called_with(test.IsHttpRequest(),
                                                         'AvailabilityZones')
        self.mock_group_list.assert_called_with(test.IsHttpRequest())

    def test_create_volume_from_image_under_image_min_disk_size(self):
        image = self.images.get(name="protected_images")
        image.min_disk = 30
        self._test_create_volume_from_image_under_image_min_disk_size(image)

    @override_settings(OPENSTACK_API_VERSIONS={'image': 1})
    def test_create_volume_from_image_under_image_prop_min_disk_size_v1(self):
        image = self.images.get(name="protected_images")
        image.min_disk = 0
        image.properties['min_disk'] = 30
        self._test_create_volume_from_image_under_image_min_disk_size(image)

    def test_create_volume_from_image_under_image_prop_min_disk_size_v2(self):
        image = self.imagesV2.get(name="protected_images")
        self._test_create_volume_from_image_under_image_min_disk_size(image)

    @test.create_mocks({
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_list_detailed'],
        cinder: ['extension_supported',
                 'availability_zone_list',
                 'volume_list',
                 'volume_type_list',
                 'volume_type_default',
                 'volume_snapshot_list',
                 'group_list'],
    })
    def test_create_volume_gb_used_over_alloted_quota(self):
        formData = {'name': u'This Volume Is Huge!',
                    'description': u'This is a volume that is just too big!',
                    'method': u'CreateForm',
                    'size': 5000}

        usage_limit = self.cinder_quota_usages.first()
        usage_limit.add_quota(api.base.Quota('volumes', 6))
        usage_limit.tally('volumes', len(self.cinder_volumes.list()))
        usage_limit.add_quota(api.base.Quota('gigabytes', 100))
        usage_limit.tally('gigabytes', 80)

        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_tenant_quota_usages.return_value = usage_limit
        self.mock_volume_snapshot_list.return_value = \
            self.cinder_volume_snapshots.list()
        self.mock_image_list_detailed.return_value = [self.images.list(),
                                                      False, False]
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_group_list.return_value = []

        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)

        expected_error = [u'A volume of 5000GiB cannot be created as you only'
                          ' have 20GiB of your quota available.']
        self.assertEqual(res.context['form'].errors['__all__'], expected_error)

        self.assertEqual(3, self.mock_volume_type_list.call_count)
        self.assertEqual(2, self.mock_volume_type_default.call_count)
        self.assertEqual(2, self.mock_volume_list.call_count)
        self.assertEqual(2, self.mock_availability_zone_list.call_count)

        self.assertEqual(2, self.mock_tenant_quota_usages.call_count)
        self.mock_volume_snapshot_list.assert_called_with(
            test.IsHttpRequest(), search_opts=SEARCH_OPTS)
        self.mock_image_list_detailed.assert_called_with(
            test.IsHttpRequest(),
            filters={'visibility': 'shared', 'status': 'active'})
        self.mock_extension_supported.assert_called_with(test.IsHttpRequest(),
                                                         'AvailabilityZones')
        self.mock_group_list.assert_called_with(test.IsHttpRequest())

    @test.create_mocks({
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_list_detailed'],
        cinder: ['extension_supported',
                 'availability_zone_list',
                 'volume_list',
                 'volume_type_list',
                 'volume_type_default',
                 'volume_snapshot_list',
                 'group_list'],
    })
    def test_create_volume_number_over_alloted_quota(self):
        formData = {'name': u'Too Many...',
                    'description': u'We have no volumes left!',
                    'method': u'CreateForm',
                    'size': 10}

        usage_limit = self.cinder_quota_usages.first()
        usage_limit.add_quota(api.base.Quota('volumes',
                                             len(self.cinder_volumes.list())))
        usage_limit.tally('volumes', len(self.cinder_volumes.list()))
        usage_limit.add_quota(api.base.Quota('gigabytes', 100))
        usage_limit.tally('gigabytes', 20)

        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_tenant_quota_usages.return_value = usage_limit
        self.mock_volume_snapshot_list.return_value = \
            self.cinder_volume_snapshots.list()
        self.mock_image_list_detailed.return_value = [self.images.list(),
                                                      False, False]
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_group_list.return_value = []

        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)

        expected_error = [u'You are already using all of your available'
                          ' volumes.']
        self.assertEqual(res.context['form'].errors['__all__'], expected_error)

        self.assertEqual(3, self.mock_volume_type_list.call_count)
        self.assertEqual(2, self.mock_volume_type_default.call_count)
        self.assertEqual(2, self.mock_availability_zone_list.call_count)

        self.mock_volume_snapshot_list.assert_called_with(
            test.IsHttpRequest(), search_opts=SEARCH_OPTS)
        self.mock_image_list_detailed.assert_called_with(
            test.IsHttpRequest(),
            filters={'visibility': 'shared', 'status': 'active'})
        self.mock_volume_list.assert_called_with(test.IsHttpRequest(),
                                                 search_opts=SEARCH_OPTS)
        self.mock_extension_supported.assert_called_with(test.IsHttpRequest(),
                                                         'AvailabilityZones')
        self.mock_group_list.assert_called_with(test.IsHttpRequest())

    @test.create_mocks({
        cinder: ['volume_create', 'volume_snapshot_list',
                 'volume_type_list', 'volume_type_default',
                 'volume_list', 'availability_zone_list',
                 'extension_supported', 'group_list'],
        quotas: ['tenant_quota_usages'],
        api.glance: ['image_list_detailed'],
    })
    def test_create_volume_with_group(self):
        volume = self.cinder_volumes.first()
        volume_type = self.cinder_volume_types.first()
        az = self.cinder_availability_zones.first().zoneName
        volume_group = self.cinder_groups.list()[0]
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'type': volume_type.name,
                    'size': 50,
                    'snapshot_source': '',
                    'availability_zone': az,
                    'group': volume_group.id}

        self.mock_volume_type_default.return_value = \
            self.cinder_volume_types.first()
        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_tenant_quota_usages.return_value = \
            self.cinder_quota_usages.first()
        self.mock_volume_snapshot_list.return_value = \
            self.cinder_volume_snapshots.list()
        self.mock_image_list_detailed.return_value = [[], False, False]
        self.mock_availability_zone_list.return_value = \
            self.cinder_availability_zones.list()
        self.mock_extension_supported.return_value = True
        self.mock_volume_list.return_value = self.cinder_volumes.list()
        self.mock_volume_create.return_value = volume
        self.mock_group_list.return_value = self.cinder_groups.list()

        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)

        redirect_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redirect_url)

        self.mock_volume_type_default.assert_called_once()
        self.mock_volume_type_list.assert_called_once()
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=SEARCH_OPTS)
        self.mock_availability_zone_list.assert_called_once()
        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_volume_list.assert_called_once_with(test.IsHttpRequest(),
                                                      search_opts=SEARCH_OPTS)
        self.mock_volume_create.assert_called_once_with(
            test.IsHttpRequest(), formData['size'], formData['name'],
            formData['description'], formData['type'], metadata={},
            snapshot_id=None, group_id=volume_group.id, image_id=None,
            availability_zone=formData['availability_zone'], source_volid=None)
        self.mock_image_list_detailed.assert_called_with(
            test.IsHttpRequest(),
            filters={'visibility': 'shared', 'status': 'active'})
        self.mock_tenant_quota_usages.assert_called_once_with(
            test.IsHttpRequest(),
            targets=('volumes', 'gigabytes'))
        self.mock_group_list.assert_called_with(test.IsHttpRequest())

    @test.create_mocks({
        api.nova: ['server_list'],
        cinder: ['volume_delete',
                 'volume_snapshot_list',
                 'volume_list_paged',
                 'tenant_absolute_limits'],
    })
    def test_delete_volume(self):
        volumes = self.cinder_volumes.list()
        volume = self.cinder_volumes.first()
        formData = {'action':
                    'volumes__delete__%s' % volume.id}

        self.mock_volume_list_paged.return_value = [volumes, False, False]
        self.mock_volume_snapshot_list.return_value = []
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_volume_list_paged.return_value = [volumes, False, False]
        self.mock_tenant_absolute_limits.return_value = \
            self.cinder_limits['absolute']

        url = INDEX_URL
        res = self.client.post(url, formData, follow=True)

        self.assertIn("Scheduled deletion of Volume: Volume name",
                      [m.message for m in res.context['messages']])

        self.mock_volume_list_paged.assert_called_with(
            test.IsHttpRequest(), marker=None,
            paginate=True, sort_dir='desc',
            search_opts=None)
        self.assertEqual(2, self.mock_volume_snapshot_list.call_count)
        self.mock_volume_delete.assert_called_once_with(test.IsHttpRequest(),
                                                        volume.id)
        self.mock_server_list.assert_called_with(test.IsHttpRequest(),
                                                 search_opts=None)
        self.assertEqual(8, self.mock_tenant_absolute_limits.call_count)

    @mock.patch.object(quotas, 'tenant_quota_usages')
    @mock.patch.object(cinder, 'tenant_absolute_limits')
    @mock.patch.object(cinder, 'volume_get')
    def test_delete_volume_with_snap_no_action_item(self, mock_get,
                                                    mock_limits,
                                                    mock_quotas):
        volume = self.cinder_volumes.get(name='Volume name')
        setattr(volume, 'has_snapshot', True)
        limits = self.cinder_limits['absolute']

        mock_get.return_value = volume
        mock_limits.return_value = limits
        mock_quotas.return_value = self.cinder_quota_usages.first()

        url = (INDEX_URL +
               "?action=row_update&table=volumes&obj_id=" + volume.id)

        res = self.client.get(url, {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(res.status_code, 200)
        mock_quotas.assert_called_once_with(test.IsHttpRequest(),
                                            targets=('volumes', 'gigabytes'))
        self.assert_mock_multiple_calls_with_same_arguments(
            mock_limits, 2,
            mock.call(test.IsHttpRequest()))

        self.assertNotContains(res, 'Delete Volume')
        self.assertNotContains(res, 'delete')

    @mock.patch.object(api.nova, 'server_list')
    @mock.patch.object(cinder, 'volume_get')
    @override_settings(OPENSTACK_HYPERVISOR_FEATURES={'can_set_mount_point':
                                                      True})
    def test_edit_attachments(self, mock_get, mock_server_list):
        volume = self.cinder_volumes.first()
        servers = [s for s in self.servers.list()
                   if s.tenant_id == self.request.user.tenant_id]
        volume.attachments = [{'id': volume.id,
                               'volume_id': volume.id,
                               'volume_name': volume.name,
                               "attachment_id": ATTACHMENT_ID,
                               'instance': servers[0],
                               'device': '/dev/vdb',
                               'server_id': servers[0].id}]

        mock_get.return_value = volume
        mock_server_list.return_value = [servers, False]

        url = reverse('horizon:project:volumes:attach',
                      args=[volume.id])
        res = self.client.get(url)
        msg = 'Volume %s on instance %s' % (volume.name, servers[0].name)
        self.assertContains(res, msg)
        # Asserting length of 2 accounts for the one instance option,
        # and the one 'Choose Instance' option.
        form = res.context['form']
        self.assertEqual(len(form.fields['instance']._choices),
                         1)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(form.fields['device'].widget,
                              widgets.TextInput)
        self.assertFalse(form.fields['device'].required)
        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_server_list.assert_called_once()

    @mock.patch.object(api.nova, 'server_list')
    @mock.patch.object(cinder, 'volume_get')
    @override_settings(OPENSTACK_HYPERVISOR_FEATURES={'can_set_mount_point':
                                                      True})
    def test_edit_attachments_auto_device_name(self, mock_get,
                                               mock_server_list):
        volume = self.cinder_volumes.first()
        servers = [s for s in self.servers.list()
                   if s.tenant_id == self.request.user.tenant_id]
        volume.attachments = [{'id': volume.id,
                               'volume_id': volume.id,
                               'volume_name': volume.name,
                               "attachment_id": ATTACHMENT_ID,
                               'instance': servers[0],
                               'device': '',
                               'server_id': servers[0].id}]

        mock_get.return_value = volume
        mock_server_list.return_value = [servers, False]

        url = reverse('horizon:project:volumes:attach',
                      args=[volume.id])
        res = self.client.get(url)
        form = res.context['form']
        self.assertIsInstance(form.fields['device'].widget,
                              widgets.TextInput)
        self.assertFalse(form.fields['device'].required)
        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_server_list.assert_called_once()

    @mock.patch.object(api.nova, 'server_list')
    @mock.patch.object(cinder, 'volume_get')
    def test_edit_attachments_cannot_set_mount_point(self, mock_get,
                                                     mock_server_list):
        volume = self.cinder_volumes.first()

        url = reverse('horizon:project:volumes:attach',
                      args=[volume.id])
        res = self.client.get(url)
        # Assert the device field is hidden.
        form = res.context['form']
        self.assertIsInstance(form.fields['device'].widget,
                              widgets.HiddenInput)
        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_server_list.assert_called_once()

    @mock.patch.object(api.nova, 'server_list')
    @mock.patch.object(cinder, 'volume_get')
    def test_edit_attachments_attached_volume(self, mock_get,
                                              mock_server_list):
        servers = [s for s in self.servers.list()
                   if s.tenant_id == self.request.user.tenant_id]
        server = servers[0]
        volume = self.cinder_volumes.list()[0]

        mock_get.return_value = volume
        mock_server_list.return_value = [servers, False]

        url = reverse('horizon:project:volumes:attach',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertEqual(res.context['form'].fields['instance']._choices[0][1],
                         "Select an instance")
        self.assertEqual(len(res.context['form'].fields['instance'].choices),
                         2)
        self.assertEqual(res.context['form'].fields['instance']._choices[1][0],
                         server.id)
        self.assertEqual(res.status_code, 200)
        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_server_list.assert_called_once()

    @mock.patch.object(quotas, 'tenant_quota_usages')
    @mock.patch.object(cinder, 'tenant_absolute_limits')
    @mock.patch.object(cinder, 'volume_get')
    def test_create_snapshot_button_attributes(self, mock_get,
                                               mock_limits,
                                               mock_quotas):
        limits = {'maxTotalSnapshots': 2}
        limits['totalSnapshotsUsed'] = 1
        volume = self.cinder_volumes.first()

        mock_get.return_value = volume
        mock_limits.return_value = limits
        mock_quotas.return_value = self.cinder_quota_usages.first()

        res_url = (INDEX_URL +
                   "?action=row_update&table=volumes&obj_id=" + volume.id)

        res = self.client.get(res_url, {},
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        action_name = ('%(table)s__row_%(id)s__action_%(action)s' %
                       {'table': 'volumes', 'id': volume.id,
                        'action': 'snapshots'})
        content = res.content.decode('utf-8')
        self.assertIn(action_name, content)
        self.assertIn('Create Snapshot', content)
        self.assertIn(reverse('horizon:project:volumes:create_snapshot',
                              args=[volume.id]),
                      content)
        self.assertNotIn('disabled', content)
        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_quotas.assert_called_once_with(test.IsHttpRequest(),
                                            targets=('volumes', 'gigabytes'))
        self.assert_mock_multiple_calls_with_same_arguments(
            mock_limits, 2,
            mock.call(test.IsHttpRequest()))

    @mock.patch.object(quotas, 'tenant_quota_usages')
    @mock.patch.object(cinder, 'tenant_absolute_limits')
    @mock.patch.object(cinder, 'volume_get')
    def test_create_snapshot_button_disabled_when_quota_exceeded(
            self, mock_get, mock_limits, mock_quotas):
        limits = {'maxTotalSnapshots': 1}
        limits['totalSnapshotsUsed'] = limits['maxTotalSnapshots']
        volume = self.cinder_volumes.first()

        mock_get.return_value = volume
        mock_limits.return_value = limits
        mock_quotas.return_value = self.cinder_quota_usages.first()

        res_url = (INDEX_URL +
                   "?action=row_update&table=volumes&obj_id=" + volume.id)

        res = self.client.get(res_url, {},
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        action_name = ('%(table)s__row_%(id)s__action_%(action)s' %
                       {'table': 'volumes', 'id': volume.id,
                        'action': 'snapshots'})
        content = res.content.decode('utf-8')
        self.assertIn(action_name, content)
        self.assertIn('Create Snapshot (Quota exceeded)', content)
        self.assertIn(reverse('horizon:project:volumes:create_snapshot',
                              args=[volume.id]),
                      content)
        self.assertIn('disabled', content,
                      'The create snapshot button should be disabled')
        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_quotas.assert_called_once_with(test.IsHttpRequest(),
                                            targets=('volumes', 'gigabytes'))
        self.assert_mock_multiple_calls_with_same_arguments(
            mock_limits, 2,
            mock.call(test.IsHttpRequest()))

    @test.create_mocks({
        api.nova: ['server_list'],
        cinder: ['volume_backup_supported',
                 'volume_snapshot_list',
                 'volume_list_paged',
                 'tenant_absolute_limits'],
    })
    def test_create_button_attributes(self):
        limits = self.cinder_limits['absolute']
        limits['maxTotalVolumes'] = 10
        limits['totalVolumesUsed'] = 1
        volumes = self.cinder_volumes.list()

        self.mock_volume_backup_supported.return_value = True
        self.mock_volume_list_paged.return_value = [volumes, False, False]
        self.mock_volume_snapshot_list.return_value = []
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_tenant_absolute_limits.return_value = limits

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')

        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, self.cinder_volumes.list())

        create_action = self.getAndAssertTableAction(res, 'volumes', 'create')

        self.assertEqual(set(['ajax-modal', 'ajax-update', 'btn-create']),
                         set(create_action.classes))
        self.assertEqual('Create Volume',
                         six.text_type(create_action.verbose_name))
        self.assertEqual('horizon:project:volumes:create',
                         create_action.url)
        self.assertEqual((('volume', 'volume:create'),),
                         create_action.policy_rules)
        self.assertEqual(5, self.mock_volume_backup_supported.call_count)
        self.mock_volume_list_paged.assert_called_once_with(
            test.IsHttpRequest(), sort_dir='desc', marker=None,
            paginate=True, search_opts=None)
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=None)
        self.mock_server_list.assert_called_once_with(test.IsHttpRequest(),
                                                      search_opts=None)
        self.assertEqual(9, self.mock_tenant_absolute_limits.call_count)

    @test.create_mocks({
        api.nova: ['server_list'],
        cinder: ['volume_backup_supported',
                 'volume_snapshot_list',
                 'volume_list_paged',
                 'tenant_absolute_limits'],
    })
    def test_create_button_disabled_when_quota_exceeded(self):
        limits = self.cinder_limits['absolute']
        limits['totalVolumesUsed'] = limits['maxTotalVolumes']
        volumes = self.cinder_volumes.list()

        self.mock_volume_backup_supported.return_value = True
        self.mock_volume_list_paged.return_value = [volumes, False, False]
        self.mock_volume_snapshot_list.return_value = []
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_tenant_absolute_limits.return_value = limits

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'horizon/common/_data_table_view.html')

        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, self.cinder_volumes.list())

        create_action = self.getAndAssertTableAction(res, 'volumes', 'create')
        self.assertIn('disabled', create_action.classes,
                      'The create button should be disabled')
        self.assertEqual(5, self.mock_volume_backup_supported.call_count)
        self.mock_volume_list_paged.assert_called_once_with(
            test.IsHttpRequest(), marker=None,
            paginate=True, sort_dir='desc',
            search_opts=None)
        self.mock_server_list.assert_called_once_with(test.IsHttpRequest(),
                                                      search_opts=None)
        self.assertEqual(9, self.mock_tenant_absolute_limits.call_count)

    @test.create_mocks({
        api.nova: ['server_get'],
        cinder: ['message_list',
                 'volume_snapshot_list',
                 'volume_get',
                 'tenant_absolute_limits'],
    })
    def test_detail_view(self):
        volume = self.cinder_volumes.first()
        server = self.servers.first()
        snapshots = self.cinder_volume_snapshots.list()

        volume.attachments = [{"server_id": server.id,
                               "attachment_id": ATTACHMENT_ID}]

        self.mock_volume_get.return_value = volume
        self.mock_volume_snapshot_list.return_value = snapshots
        self.mock_server_get.return_value = server
        self.mock_tenant_absolute_limits.return_value = \
            self.cinder_limits['absolute']
        self.mock_message_list.return_value = []

        url = reverse('horizon:project:volumes:detail',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['volume'].id, volume.id)
        self.assertNoMessages()
        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts={'volume_id': volume.id})
        self.mock_server_get.assert_called_once_with(test.IsHttpRequest(),
                                                     server.id)
        self.mock_tenant_absolute_limits.assert_called_once()
        self.mock_message_list.assert_called_once_with(
            test.IsHttpRequest(),
            {
                'resource_uuid': '11023e92-8008-4c8b-8059-7f2293ff3887',
                'resource_type': 'volume',
            })

    @mock.patch.object(cinder, 'volume_get_encryption_metadata')
    @mock.patch.object(cinder, 'volume_get')
    def test_encryption_detail_view_encrypted(self, mock_get, mock_encryption):
        enc_meta = self.cinder_volume_encryption.first()
        volume = self.cinder_volumes.get(name='my_volume2')

        mock_encryption.return_value = enc_meta
        mock_get.return_value = volume

        url = reverse('horizon:project:volumes:encryption_detail',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertContains(res,
                            "Volume Encryption Details: %s" % volume.name,
                            2, 200)
        self.assertContains(res, "<dd>%s</dd>" % volume.volume_type, 1, 200)
        self.assertContains(res, "<dd>%s</dd>" % enc_meta.provider, 1, 200)
        self.assertContains(res, "<dd>%s</dd>" % enc_meta.control_location, 1,
                            200)
        self.assertContains(res, "<dd>%s</dd>" % enc_meta.cipher, 1, 200)
        self.assertContains(res, "<dd>%s</dd>" % enc_meta.key_size, 1, 200)

        self.assertNoMessages()

        mock_encryption.assert_called_once_with(test.IsHttpRequest(),
                                                volume.id)
        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)

    @mock.patch.object(cinder, 'volume_get_encryption_metadata')
    @mock.patch.object(cinder, 'volume_get')
    def test_encryption_detail_view_unencrypted(self, mock_get,
                                                mock_encryption):
        enc_meta = self.cinder_volume_encryption.list()[1]
        volume = self.cinder_volumes.get(name='my_volume2')

        mock_encryption.return_value = enc_meta
        mock_get.return_value = volume

        url = reverse('horizon:project:volumes:encryption_detail',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertContains(res,
                            "Volume Encryption Details: %s" % volume.name,
                            2, 200)
        self.assertContains(res, "<h3>Volume is Unencrypted</h3>", 1, 200)

        self.assertNoMessages()

        mock_encryption.assert_called_once_with(test.IsHttpRequest(),
                                                volume.id)
        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)

    @mock.patch.object(quotas, 'tenant_quota_usages')
    @mock.patch.object(cinder, 'tenant_absolute_limits')
    @mock.patch.object(cinder, 'volume_get')
    def test_get_data(self, mock_get, mock_limits, mock_quotas):
        volume = self.cinder_volumes.get(name='v2_volume')
        volume._apiresource.name = ""

        mock_get.return_value = volume
        mock_limits.return_value = self.cinder_limits['absolute']
        mock_quotas.return_value = self.cinder_quota_usages.first()

        url = (INDEX_URL +
               "?action=row_update&table=volumes&obj_id=" + volume.id)

        res = self.client.get(url, {},
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(volume.name, volume.id)

        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_quotas.assert_called_once_with(test.IsHttpRequest(),
                                            targets=('volumes', 'gigabytes'))
        self.assert_mock_multiple_calls_with_same_arguments(
            mock_limits, 2,
            mock.call(test.IsHttpRequest()))

    @test.create_mocks({
        api.nova: ['server_get'],
        cinder: ['tenant_absolute_limits',
                 'volume_get',
                 'volume_snapshot_list',
                 'message_list'],
    })
    def test_detail_view_snapshot_tab(self):
        volume = self.cinder_volumes.first()
        server = self.servers.first()
        snapshots = self.cinder_volume_snapshots.list()
        this_volume_snapshots = [snapshot for snapshot in snapshots
                                 if snapshot.volume_id == volume.id]
        volume.attachments = [{"server_id": server.id,
                               "attachment_id": ATTACHMENT_ID}]

        self.mock_volume_get.return_value = volume
        self.mock_server_get.return_value = server
        self.mock_tenant_absolute_limits.return_value = \
            self.cinder_limits['absolute']
        self.mock_message_list.return_value = []
        self.mock_volume_snapshot_list.return_value = this_volume_snapshots

        url = '?'.join([reverse(DETAIL_URL, args=[volume.id]),
                        '='.join(['tab', 'volume_details__snapshots_tab'])])
        res = self.client.get(url)

        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertEqual(res.context['volume'].id, volume.id)
        self.assertEqual(len(res.context['table'].data),
                         len(this_volume_snapshots))
        self.assertNoMessages()

        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts={'volume_id': volume.id})
        self.mock_tenant_absolute_limits.assert_called_once()
        self.mock_message_list.assert_called_once_with(
            test.IsHttpRequest(),
            {
                'resource_uuid': volume.id,
                'resource_type': 'volume'
            })

    @mock.patch.object(cinder, 'volume_get')
    def test_detail_view_with_exception(self, mock_get):
        volume = self.cinder_volumes.first()
        server = self.servers.first()

        volume.attachments = [{"server_id": server.id,
                               "attachment_id": ATTACHMENT_ID}]

        mock_get.side_effect = self.exceptions.cinder

        url = reverse('horizon:project:volumes:detail',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, INDEX_URL)
        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)

    @test.create_mocks({cinder: ['volume_update',
                                 'volume_set_bootable',
                                 'volume_get']})
    def test_update_volume(self):
        volume = self.cinder_volumes.get(name="my_volume")

        self.mock_volume_get.return_value = volume

        formData = {'method': 'UpdateForm',
                    'name': volume.name,
                    'description': volume.description,
                    'bootable': False}

        url = reverse('horizon:project:volumes:update',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_get.assert_called_once_with(
            test.IsHttpRequest(), volume.id)
        self.mock_volume_update.assert_called_once_with(
            test.IsHttpRequest(), volume.id, volume.name, volume.description)
        self.mock_volume_set_bootable.assert_called_once_with(
            test.IsHttpRequest(), volume.id, False)

    @test.create_mocks({cinder: ['volume_update',
                                 'volume_set_bootable',
                                 'volume_get']})
    def test_update_volume_without_name(self):
        volume = self.cinder_volumes.get(name="my_volume")

        self.mock_volume_get.return_value = volume

        formData = {'method': 'UpdateForm',
                    'name': '',
                    'description': volume.description,
                    'bootable': False}

        url = reverse('horizon:project:volumes:update',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_volume_update.assert_called_once_with(
            test.IsHttpRequest(), volume.id, '', volume.description)
        self.mock_volume_set_bootable.assert_called_once_with(
            test.IsHttpRequest(), volume.id, False)

    @test.create_mocks({cinder: ['volume_update',
                                 'volume_set_bootable',
                                 'volume_get']})
    def test_update_volume_bootable_flag(self):
        volume = self.cinder_bootable_volumes.get(name="my_volume")

        self.mock_volume_get.return_value = volume

        formData = {'method': 'UpdateForm',
                    'name': volume.name,
                    'description': 'update bootable flag',
                    'bootable': True}

        url = reverse('horizon:project:volumes:update',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, INDEX_URL)

        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_volume_update.assert_called_once_with(
            test.IsHttpRequest(), volume.id, volume.name,
            'update bootable flag')
        self.mock_volume_set_bootable.assert_called_once_with(
            test.IsHttpRequest(), volume.id, True)

    @mock.patch.object(cinder, 'volume_upload_to_image')
    @mock.patch.object(cinder, 'volume_get')
    def test_upload_to_image(self, mock_get, mock_upload):
        volume = self.cinder_volumes.get(name='v2_volume')
        loaded_resp = {'container_format': 'bare',
                       'disk_format': 'raw',
                       'id': '741fe2ac-aa2f-4cec-82a9-4994896b43fb',
                       'image_id': '2faa080b-dd56-4bf0-8f0a-0d4627d8f306',
                       'image_name': 'test',
                       'size': '2',
                       'status': 'uploading'}

        form_data = {'id': volume.id,
                     'name': volume.name,
                     'image_name': 'testimage',
                     'force': True,
                     'container_format': 'bare',
                     'disk_format': 'raw'}

        mock_get.return_value = volume
        mock_upload.return_value = loaded_resp

        url = reverse('horizon:project:volumes:upload_to_image',
                      args=[volume.id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(info=1)

        redirect_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redirect_url)

        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_upload.assert_called_once_with(test.IsHttpRequest(),
                                            form_data['id'],
                                            form_data['force'],
                                            form_data['image_name'],
                                            form_data['container_format'],
                                            form_data['disk_format'])

    @mock.patch.object(quotas, 'tenant_quota_usages')
    @mock.patch.object(cinder, 'volume_extend')
    @mock.patch.object(cinder, 'volume_get')
    def test_extend_volume(self, mock_get, mock_extend, mock_quotas):
        volume = self.cinder_volumes.first()
        formData = {'name': u'A Volume I Am Making',
                    'orig_size': volume.size,
                    'new_size': 120}

        mock_get.return_value = volume
        mock_quotas.return_value = self.cinder_quota_usages.first()
        mock_extend.return_value = volume

        url = reverse('horizon:project:volumes:extend',
                      args=[volume.id])
        res = self.client.post(url, formData)

        redirect_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redirect_url)

        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_quotas.assert_called_once()
        mock_extend.assert_called_once_with(test.IsHttpRequest(), volume.id,
                                            formData['new_size'])

    @mock.patch.object(quotas, 'tenant_quota_usages')
    @mock.patch.object(cinder, 'volume_get')
    def test_extend_volume_with_wrong_size(self, mock_get, mock_quotas):
        volume = self.cinder_volumes.first()
        formData = {'name': u'A Volume I Am Making',
                    'orig_size': volume.size,
                    'new_size': 10}

        mock_get.return_value = volume
        mock_quotas.return_value = self.cinder_quota_usages.first()

        url = reverse('horizon:project:volumes:extend',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertFormErrors(res, 1,
                              "New size must be greater than "
                              "current size.")

        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_quotas.assert_called_once()

    @mock.patch.object(quotas, 'tenant_quota_usages')
    @mock.patch.object(cinder, 'tenant_absolute_limits')
    @mock.patch.object(cinder, 'volume_get')
    def test_retype_volume_supported_action_item(self, mock_get,
                                                 mock_limits, mock_quotas):
        volume = self.cinder_volumes.get(name='v2_volume')
        limits = self.cinder_limits['absolute']

        mock_get.return_value = volume
        mock_limits.return_value = limits
        mock_quotas.return_value = self.cinder_quota_usages.first()

        url = (INDEX_URL +
               "?action=row_update&table=volumes&obj_id=" + volume.id)

        res = self.client.get(url, {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(res.status_code, 200)

        self.assertContains(res, 'Change Volume Type')
        self.assertContains(res, 'retype')

        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        mock_quotas.assert_called_once_with(test.IsHttpRequest(),
                                            targets=('volumes', 'gigabytes'))
        self.assert_mock_multiple_calls_with_same_arguments(
            mock_limits, 2,
            mock.call(test.IsHttpRequest()))

    @test.create_mocks({
        cinder: ['volume_type_list',
                 'volume_retype',
                 'volume_get']
    })
    def test_retype_volume(self):
        volume = self.cinder_volumes.get(name='my_volume2')

        volume_type = self.cinder_volume_types.get(name='vol_type_1')

        form_data = {'id': volume.id,
                     'name': volume.name,
                     'volume_type': volume_type.name,
                     'migration_policy': 'on-demand'}

        self.mock_volume_get.return_value = volume
        self.mock_volume_type_list.return_value = \
            self.cinder_volume_types.list()
        self.mock_volume_retype.return_value = True

        url = reverse('horizon:project:volumes:retype',
                      args=[volume.id])
        res = self.client.post(url, form_data)

        self.assertNoFormErrors(res)

        redirect_url = INDEX_URL
        self.assertRedirectsNoFollow(res, redirect_url)

        self.mock_volume_get.assert_called_once_with(test.IsHttpRequest(),
                                                     volume.id)
        self.mock_volume_type_list.assert_called_once()
        self.mock_volume_retype.assert_called_once_with(
            test.IsHttpRequest(), volume.id,
            form_data['volume_type'], form_data['migration_policy'])

    def test_encryption_false(self):
        self._test_encryption(False)

    def test_encryption_true(self):
        self._test_encryption(True)

    @test.create_mocks({
        api.nova: ['server_list'],
        cinder: ['volume_backup_supported',
                 'volume_list_paged',
                 'volume_snapshot_list',
                 'tenant_absolute_limits'],
    })
    def _test_encryption(self, encryption):
        volumes = self.cinder_volumes.list()
        for volume in volumes:
            volume.encrypted = encryption
        limits = self.cinder_limits['absolute']

        self.mock_volume_backup_supported.return_value = False
        self.mock_volume_list_paged.return_value = [self.cinder_volumes.list(),
                                                    False, False]
        self.mock_volume_snapshot_list.return_value = \
            self.cinder_volume_snapshots.list()
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_tenant_absolute_limits.return_value = limits

        res = self.client.get(INDEX_URL)
        rows = res.context['volumes_table'].get_rows()

        column_value = 'Yes' if encryption else 'No'

        for row in rows:
            self.assertEqual(row.cells['encryption'].data, column_value)

        self.assertEqual(10, self.mock_volume_backup_supported.call_count)
        self.mock_volume_list_paged.assert_called_once_with(
            test.IsHttpRequest(), marker=None,
            sort_dir='desc', search_opts=None,
            paginate=True)
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=None)
        self.assertEqual(13, self.mock_tenant_absolute_limits.call_count)

    @mock.patch.object(quotas, 'tenant_quota_usages')
    @mock.patch.object(cinder, 'volume_get')
    def test_extend_volume_with_size_out_of_quota(self, mock_get, mock_quotas):
        volume = self.cinder_volumes.first()
        usage_limit = self.cinder_quota_usages.first()
        usage_limit.add_quota(api.base.Quota('gigabytes', 100))
        usage_limit.tally('gigabytes', 20)
        usage_limit.tally('volumes', len(self.cinder_volumes.list()))

        formData = {'name': u'A Volume I Am Making',
                    'orig_size': volume.size,
                    'new_size': 1000}

        mock_quotas.return_value = usage_limit
        mock_get.return_value = volume

        url = reverse('horizon:project:volumes:extend',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertFormError(res, "form", "new_size",
                             "Volume cannot be extended to 1000GiB as "
                             "the maximum size it can be extended to is "
                             "120GiB.")

        mock_get.assert_called_once_with(test.IsHttpRequest(), volume.id)
        self.assertEqual(2, mock_quotas.call_count)

    @test.create_mocks({
        api.nova: ['server_list'],
        cinder: ['volume_backup_supported',
                 'volume_list_paged',
                 'volume_snapshot_list',
                 'tenant_absolute_limits'],
    })
    def test_create_transfer_availability(self):
        limits = self.cinder_limits['absolute']

        self.mock_volume_backup_supported.return_value = False
        self.mock_volume_list_paged.return_value = [self.cinder_volumes.list(),
                                                    False, False]
        self.mock_volume_snapshot_list.return_value = []
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_tenant_absolute_limits.return_value = limits

        res = self.client.get(INDEX_URL)
        table = res.context['volumes_table']

        # Verify that the create transfer action is present if and only if
        # the volume is available
        for vol in table.data:
            actions = [a.name for a in table.get_row_actions(vol)]
            self.assertEqual('create_transfer' in actions,
                             vol.status == 'available')

        self.assertEqual(10, self.mock_volume_backup_supported.call_count)
        self.mock_volume_list_paged.assert_called_once_with(
            test.IsHttpRequest(), marker=None,
            sort_dir='desc', search_opts=None,
            paginate=True)
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=None)
        self.mock_server_list.assert_called_once_with(test.IsHttpRequest(),
                                                      search_opts=None)
        self.assertEqual(13, self.mock_tenant_absolute_limits.call_count)

    @mock.patch.object(cinder, 'transfer_get')
    @mock.patch.object(cinder, 'transfer_create')
    def test_create_transfer(self, mock_transfer_create, mock_transfer_get):
        volumes = self.cinder_volumes.list()
        volToTransfer = [v for v in volumes if v.status == 'available'][0]
        formData = {'volume_id': volToTransfer.id,
                    'name': u'any transfer name'}

        transfer = self.cinder_volume_transfers.first()
        mock_transfer_create.return_value = transfer
        mock_transfer_get.return_value = transfer

        # Create a transfer for the first available volume
        url = reverse('horizon:project:volumes:create_transfer',
                      args=[volToTransfer.id])
        res = self.client.post(url, formData)

        self.assertNoFormErrors(res)
        mock_transfer_create.assert_called_once_with(test.IsHttpRequest(),
                                                     formData['volume_id'],
                                                     formData['name'])
        mock_transfer_get.assert_called_once_with(test.IsHttpRequest(),
                                                  transfer.id)

    @test.create_mocks({
        api.nova: ['server_list'],
        cinder: ['volume_backup_supported',
                 'volume_list_paged',
                 'volume_snapshot_list',
                 'transfer_delete',
                 'tenant_absolute_limits'],
    })
    def test_delete_transfer(self):
        transfer = self.cinder_volume_transfers.first()
        volumes = []

        # Attach the volume transfer to the relevant volume
        for v in self.cinder_volumes.list():
            if v.id == transfer.volume_id:
                v.status = 'awaiting-transfer'
                v.transfer = transfer
            volumes.append(v)

        formData = {'action':
                    'volumes__delete_transfer__%s' % transfer.volume_id}

        self.mock_volume_backup_supported.return_value = False
        self.mock_volume_list_paged.return_value = [volumes, False, False]
        self.mock_volume_snapshot_list.return_value = []
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_tenant_absolute_limits.return_value = \
            self.cinder_limits['absolute']

        url = INDEX_URL
        res = self.client.post(url, formData, follow=True)
        self.assertNoFormErrors(res)
        self.assertIn('Successfully deleted volume transfer "test transfer"',
                      [m.message for m in res.context['messages']])

        self.assertEqual(5, self.mock_volume_backup_supported.call_count)
        self.mock_volume_list_paged.assert_called_once_with(
            test.IsHttpRequest(), marker=None,
            search_opts=None, sort_dir='desc',
            paginate=True)
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=None)
        self.mock_transfer_delete.assert_called_once_with(test.IsHttpRequest(),
                                                          transfer.id)
        self.mock_server_list.assert_called_once_with(test.IsHttpRequest(),
                                                      search_opts=None)
        self.assertEqual(8, self.mock_tenant_absolute_limits.call_count)

    @test.create_mocks({
        api.nova: ['server_list'],
        cinder: ['volume_list_paged',
                 'volume_snapshot_list',
                 'tenant_absolute_limits',
                 'transfer_accept']
    })
    def test_accept_transfer(self):
        transfer = self.cinder_volume_transfers.first()
        self.mock_tenant_absolute_limits.return_value = \
            self.cinder_limits['absolute']

        formData = {'transfer_id': transfer.id, 'auth_key': transfer.auth_key}
        url = reverse('horizon:project:volumes:accept_transfer')
        res = self.client.post(url, formData, follow=True)

        self.assertNoFormErrors(res)
        self.mock_transfer_accept.assert_called_once_with(test.IsHttpRequest(),
                                                          transfer.id,
                                                          transfer.auth_key)
        self.assertEqual(3, self.mock_tenant_absolute_limits.call_count)
        self.mock_server_list.assert_called_once()
        self.mock_volume_list_paged.assert_called_once()
        self.mock_volume_snapshot_list.assert_called_once()
        self.mock_transfer_accept.assert_called_once()

    @mock.patch.object(cinder, 'transfer_get')
    def test_download_transfer_credentials(self, mock_transfer):
        transfer = self.cinder_volume_transfers.first()

        filename = "{}.txt".format(slugify(transfer.id))

        url = reverse('horizon:project:volumes:'
                      'download_transfer_creds',
                      kwargs={'transfer_id': transfer.id,
                              'auth_key': transfer.auth_key})

        res = self.client.get(url)

        self.assertTrue(res.has_header('content-disposition'))
        self.assertTrue(res.has_header('content-type'))
        self.assertEqual(res.get('content-disposition'),
                         'attachment; filename={}'.format(filename))
        self.assertEqual(res.get('content-type'), 'application/text')
        self.assertIn(transfer.id, res.content.decode('utf-8'))
        self.assertIn(transfer.auth_key, res.content.decode('utf-8'))
        mock_transfer.assert_called_once_with(test.IsHttpRequest(),
                                              transfer.id)

    @test.create_mocks({
        api.nova: ['server_list'],
        cinder: ['volume_backup_supported',
                 'volume_list_paged',
                 'volume_snapshot_list',
                 'tenant_absolute_limits',
                 'volume_get'],
    })
    def test_create_backup_availability(self):
        limits = self.cinder_limits['absolute']

        self.mock_volume_backup_supported.return_value = True
        self.mock_volume_list_paged.return_value = [self.cinder_volumes.list(),
                                                    False, False]
        self.mock_volume_snapshot_list.return_value = []
        self.mock_server_list.return_value = [self.servers.list(), False]
        self.mock_tenant_absolute_limits.return_value = limits

        res = self.client.get(INDEX_URL)
        table = res.context['volumes_table']

        # Verify that the create backup action is present if and only if
        # the volume is available or in-use
        for vol in table.data:
            actions = [a.name for a in table.get_row_actions(vol)]
            self.assertEqual('backups' in actions,
                             vol.status in ('available', 'in-use'))

        self.assertEqual(10, self.mock_volume_backup_supported.call_count)
        self.mock_volume_list_paged.assert_called_once_with(
            test.IsHttpRequest(), marker=None,
            sort_dir='desc', search_opts=None,
            paginate=True)
        self.mock_volume_snapshot_list.assert_called_once_with(
            test.IsHttpRequest(), search_opts=None)
        self.mock_server_list.assert_called_once_with(test.IsHttpRequest(),
                                                      search_opts=None)
        self.assertEqual(13, self.mock_tenant_absolute_limits.call_count)
