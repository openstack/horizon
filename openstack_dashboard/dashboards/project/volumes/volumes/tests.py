# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import django
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import widgets
from django import http

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.dashboards.project.volumes \
    .volumes import tables
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


VOLUME_INDEX_URL = reverse('horizon:project:volumes:index')
VOLUME_VOLUMES_TAB_URL = reverse('horizon:project:volumes:volumes_tab')


class VolumeViewTests(test.TestCase):
    @test.create_stubs({cinder: ('volume_create',
                                 'volume_snapshot_list',
                                 'volume_type_list',
                                 'volume_list',
                                 'availability_zone_list',
                                 'extension_supported'),
                        api.glance: ('image_list_detailed',),
                        quotas: ('tenant_limit_usages',)})
    def test_create_volume(self):
        volume = self.cinder_volumes.first()
        volume_type = self.volume_types.first()
        az = self.cinder_availability_zones.first().zoneName
        usage_limit = {'maxTotalVolumeGigabytes': 250,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': 6}
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'type': volume_type.name,
                    'size': 50,
                    'snapshot_source': '',
                    'availability_zone': az}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
            AndReturn(self.cinder_volume_snapshots.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        cinder.availability_zone_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_availability_zones.list())

        cinder.extension_supported(IsA(http.HttpRequest), 'AvailabilityZones')\
            .AndReturn(True)
        cinder.volume_list(IsA(
            http.HttpRequest)).AndReturn(self.cinder_volumes.list())

        cinder.volume_create(IsA(http.HttpRequest),
                             formData['size'],
                             formData['name'],
                             formData['description'],
                             formData['type'],
                             metadata={},
                             snapshot_id=None,
                             image_id=None,
                             availability_zone=formData['availability_zone'],
                             source_volid=None)\
            .AndReturn(volume)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = VOLUME_VOLUMES_TAB_URL
        self.assertRedirectsNoFollow(res, redirect_url)

    @test.create_stubs({cinder: ('volume_create',
                                 'volume_snapshot_list',
                                 'volume_type_list',
                                 'volume_list',
                                 'availability_zone_list',
                                 'extension_supported'),
                        api.glance: ('image_list_detailed',),
                        quotas: ('tenant_limit_usages',)})
    def test_create_volume_dropdown(self):
        volume = self.cinder_volumes.first()
        usage_limit = {'maxTotalVolumeGigabytes': 250,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': 6}
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 50,
                    'type': '',
                    'volume_source_type': 'no_source_type',
                    'snapshot_source': self.cinder_volume_snapshots.first().id,
                    'image_source': self.images.first().id}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
                                 AndReturn(self.cinder_volume_snapshots.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        cinder.volume_list(IsA(
            http.HttpRequest)).AndReturn(self.cinder_volumes.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)

        cinder.extension_supported(IsA(http.HttpRequest), 'AvailabilityZones')\
            .AndReturn(True)
        cinder.availability_zone_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_availability_zones.list())

        cinder.volume_create(IsA(http.HttpRequest),
                             formData['size'],
                             formData['name'],
                             formData['description'],
                             '',
                             metadata={},
                             snapshot_id=None,
                             image_id=None,
                             availability_zone=None,
                             source_volid=None).AndReturn(volume)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = VOLUME_VOLUMES_TAB_URL
        self.assertRedirectsNoFollow(res, redirect_url)

    @test.create_stubs({cinder: ('volume_create',
                                 'volume_snapshot_get',
                                 'volume_get',
                                 'volume_type_list'),
                        quotas: ('tenant_limit_usages',)})
    def test_create_volume_from_snapshot(self):
        volume = self.cinder_volumes.first()
        usage_limit = {'maxTotalVolumeGigabytes': 250,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': 6}
        snapshot = self.cinder_volume_snapshots.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 50,
                    'type': '',
                    'snapshot_source': snapshot.id}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)
        cinder.volume_snapshot_get(IsA(http.HttpRequest),
                                   str(snapshot.id)).AndReturn(snapshot)
        cinder.volume_get(IsA(http.HttpRequest), snapshot.volume_id).\
                          AndReturn(self.cinder_volumes.first())

        cinder.volume_create(IsA(http.HttpRequest),
                             formData['size'],
                             formData['name'],
                             formData['description'],
                             '',
                             metadata={},
                             snapshot_id=snapshot.id,
                             image_id=None,
                             availability_zone=None,
                             source_volid=None).AndReturn(volume)
        self.mox.ReplayAll()

        # get snapshot from url
        url = reverse('horizon:project:volumes:volumes:create')
        res = self.client.post("?".join([url,
                                         "snapshot_id=" + str(snapshot.id)]),
                               formData)

        redirect_url = VOLUME_VOLUMES_TAB_URL
        self.assertRedirectsNoFollow(res, redirect_url)

    @test.create_stubs({cinder: ('volume_create',
                                 'volume_get',
                                 'volume_list',
                                 'volume_type_list',
                                 'availability_zone_list',
                                 'volume_snapshot_get',
                                 'volume_snapshot_list',
                                 'extension_supported'),
                        api.glance: ('image_list_detailed',),
                        quotas: ('tenant_limit_usages',)})
    def test_create_volume_from_volume(self):
        volume = self.cinder_volumes.first()
        usage_limit = {'maxTotalVolumeGigabytes': 250,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': 6}

        formData = {'name': u'A copy of a volume',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 50,
                    'type': '',
                    'volume_source_type': 'volume_source',
                    'volume_source': volume.id}

        cinder.volume_list(IsA(http.HttpRequest)).\
                AndReturn(self.cinder_volumes.list())
        cinder.volume_type_list(IsA(http.HttpRequest)).\
                AndReturn(self.volume_types.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
                AndReturn(self.cinder_volume_snapshots.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                AndReturn(usage_limit)

        cinder.volume_get(IsA(http.HttpRequest),
                          volume.id).AndReturn(self.cinder_volumes.first())
        cinder.extension_supported(IsA(http.HttpRequest),
                                   'AvailabilityZones').AndReturn(True)
        cinder.availability_zone_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_availability_zones.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])

        cinder.volume_create(IsA(http.HttpRequest),
                             formData['size'],
                             formData['name'],
                             formData['description'],
                             '',
                             metadata={},
                             snapshot_id=None,
                             image_id=None,
                             availability_zone=None,
                             source_volid=volume.id).AndReturn(volume)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:create')
        redirect_url = VOLUME_VOLUMES_TAB_URL
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)
        self.assertMessageCount(info=1)
        self.assertRedirectsNoFollow(res, redirect_url)

    @test.create_stubs({cinder: ('volume_create',
                                 'volume_snapshot_list',
                                 'volume_snapshot_get',
                                 'volume_get',
                                 'volume_list',
                                 'volume_type_list',
                                 'availability_zone_list',
                                 'extension_supported'),
                        api.glance: ('image_list_detailed',),
                        quotas: ('tenant_limit_usages',)})
    def test_create_volume_from_snapshot_dropdown(self):
        volume = self.cinder_volumes.first()
        usage_limit = {'maxTotalVolumeGigabytes': 250,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': 6}
        snapshot = self.cinder_volume_snapshots.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 50,
                    'type': '',
                    'volume_source_type': 'snapshot_source',
                    'snapshot_source': snapshot.id}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
                                 AndReturn(self.cinder_volume_snapshots.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        cinder.volume_list(IsA(
            http.HttpRequest)).AndReturn(self.cinder_volumes.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)
        cinder.volume_snapshot_get(IsA(http.HttpRequest),
                                   str(snapshot.id)).AndReturn(snapshot)

        cinder.extension_supported(IsA(http.HttpRequest), 'AvailabilityZones')\
            .AndReturn(True)
        cinder.availability_zone_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_availability_zones.list())

        cinder.volume_create(IsA(http.HttpRequest),
                             formData['size'],
                             formData['name'],
                             formData['description'],
                             '',
                             metadata={},
                             snapshot_id=snapshot.id,
                             image_id=None,
                             availability_zone=None,
                             source_volid=None).AndReturn(volume)

        self.mox.ReplayAll()

        # get snapshot from dropdown list
        url = reverse('horizon:project:volumes:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = VOLUME_VOLUMES_TAB_URL
        self.assertRedirectsNoFollow(res, redirect_url)

    @test.create_stubs({cinder: ('volume_snapshot_get',
                                 'volume_type_list',
                                 'volume_get'),
                        api.glance: ('image_list_detailed',),
                        quotas: ('tenant_limit_usages',)})
    def test_create_volume_from_snapshot_invalid_size(self):
        usage_limit = {'maxTotalVolumeGigabytes': 100,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': 6}
        snapshot = self.cinder_volume_snapshots.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 20, 'snapshot_source': snapshot.id}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)
        cinder.volume_snapshot_get(IsA(http.HttpRequest),
                                   str(snapshot.id)).AndReturn(snapshot)
        cinder.volume_get(IsA(http.HttpRequest), snapshot.volume_id).\
                          AndReturn(self.cinder_volumes.first())

        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:create')
        res = self.client.post("?".join([url,
                                         "snapshot_id=" + str(snapshot.id)]),
                               formData, follow=True)
        self.assertEqual(res.redirect_chain, [])
        self.assertFormError(res, 'form', None,
                             "The volume size cannot be less than the "
                             "snapshot size (40GB)")

    @test.create_stubs({cinder: ('volume_create',
                                 'volume_type_list',
                                 'availability_zone_list',
                                 'extension_supported'),
                        api.glance: ('image_get',),
                        quotas: ('tenant_limit_usages',)})
    def test_create_volume_from_image(self):
        volume = self.cinder_volumes.first()
        usage_limit = {'maxTotalVolumeGigabytes': 200,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': 6}
        image = self.images.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 40,
                    'type': '',
                    'image_source': image.id}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)
        api.glance.image_get(IsA(http.HttpRequest),
                             str(image.id)).AndReturn(image)

        cinder.extension_supported(IsA(http.HttpRequest), 'AvailabilityZones')\
            .AndReturn(True)
        cinder.availability_zone_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_availability_zones.list())

        cinder.volume_create(IsA(http.HttpRequest),
                             formData['size'],
                             formData['name'],
                             formData['description'],
                             '',
                             metadata={},
                             snapshot_id=None,
                             image_id=image.id,
                             availability_zone=None,
                             source_volid=None).AndReturn(volume)

        self.mox.ReplayAll()

        # get image from url
        url = reverse('horizon:project:volumes:volumes:create')
        res = self.client.post("?".join([url,
                                         "image_id=" + str(image.id)]),
                               formData)

        redirect_url = VOLUME_VOLUMES_TAB_URL
        self.assertRedirectsNoFollow(res, redirect_url)

    @test.create_stubs({cinder: ('volume_create',
                                 'volume_type_list',
                                 'volume_list',
                                 'volume_snapshot_list',
                                 'availability_zone_list',
                                 'extension_supported'),
                        api.glance: ('image_get',
                                     'image_list_detailed'),
                        quotas: ('tenant_limit_usages',)})
    def test_create_volume_from_image_dropdown(self):
        volume = self.cinder_volumes.first()
        usage_limit = {'maxTotalVolumeGigabytes': 200,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': 6}
        image = self.images.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 30,
                    'type': '',
                    'volume_source_type': 'image_source',
                    'snapshot_source': self.cinder_volume_snapshots.first().id,
                    'image_source': image.id}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
                                 AndReturn(self.cinder_volume_snapshots.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        cinder.volume_list(IsA(
            http.HttpRequest)).AndReturn(self.cinder_volumes.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)) \
                  .AndReturn(usage_limit)
        api.glance.image_get(IsA(http.HttpRequest),
                             str(image.id)).AndReturn(image)

        cinder.extension_supported(IsA(http.HttpRequest), 'AvailabilityZones')\
            .AndReturn(True)
        cinder.availability_zone_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_availability_zones.list())

        cinder.volume_create(IsA(http.HttpRequest),
                             formData['size'],
                             formData['name'],
                             formData['description'],
                             '',
                             metadata={},
                             snapshot_id=None,
                             image_id=image.id,
                             availability_zone=None,
                             source_volid=None).AndReturn(volume)

        self.mox.ReplayAll()

        # get image from dropdown list
        url = reverse('horizon:project:volumes:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = VOLUME_VOLUMES_TAB_URL
        self.assertRedirectsNoFollow(res, redirect_url)

    @test.create_stubs({cinder: ('volume_type_list',
                                 'availability_zone_list',
                                 'extension_supported'),
                        api.glance: ('image_get',
                                     'image_list_detailed'),
                        quotas: ('tenant_limit_usages',)})
    def test_create_volume_from_image_under_image_size(self):
        usage_limit = {'maxTotalVolumeGigabytes': 100,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': 6}
        image = self.images.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 1, 'image_source': image.id}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)
        api.glance.image_get(IsA(http.HttpRequest),
                             str(image.id)).AndReturn(image)
        cinder.extension_supported(IsA(http.HttpRequest), 'AvailabilityZones')\
            .AndReturn(True)
        cinder.availability_zone_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_availability_zones.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:create')
        res = self.client.post("?".join([url,
                                         "image_id=" + str(image.id)]),
                               formData, follow=True)
        self.assertEqual(res.redirect_chain, [])

        # in django 1.6 filesizeformat replaces all spaces with
        # non-breaking space characters
        if django.VERSION >= (1, 6):
            msg = (u"The volume size cannot be less than the "
                   u"image size (20.0\xa0GB)")
        else:
            msg = (u"The volume size cannot be less than the "
                   u"image size (20.0 GB)")

        self.assertFormError(res, 'form', None, msg)

    @test.create_stubs({cinder: ('volume_type_list',
                                 'availability_zone_list',
                                 'extension_supported'),
                        api.glance: ('image_get',
                                     'image_list_detailed'),
                        quotas: ('tenant_limit_usages',)})
    def test_create_volume_from_image_under_image_min_disk_size(self):
        usage_limit = {'maxTotalVolumeGigabytes': 100,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': 6}
        image = self.images.get(name="protected_images")
        image.min_disk = 30
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 5, 'image_source': image.id}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)
        api.glance.image_get(IsA(http.HttpRequest),
                             str(image.id)).AndReturn(image)
        cinder.extension_supported(IsA(http.HttpRequest), 'AvailabilityZones')\
            .AndReturn(True)
        cinder.availability_zone_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_availability_zones.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:create')
        res = self.client.post("?".join([url,
                                         "image_id=" + str(image.id)]),
                               formData, follow=True)
        self.assertEqual(res.redirect_chain, [])
        self.assertFormError(res, 'form', None,
                             "The volume size cannot be less than the "
                             "image minimum disk size (30GB)")

    @test.create_stubs({cinder: ('volume_snapshot_list',
                                 'volume_type_list',
                                 'volume_list',
                                 'availability_zone_list',
                                 'extension_supported'),
                        api.glance: ('image_list_detailed',),
                        quotas: ('tenant_limit_usages',)})
    def test_create_volume_gb_used_over_alloted_quota(self):
        usage_limit = {'maxTotalVolumeGigabytes': 100,
                       'gigabytesUsed': 80,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': 6}
        formData = {'name': u'This Volume Is Huge!',
                    'description': u'This is a volume that is just too big!',
                    'method': u'CreateForm',
                    'size': 5000}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
            AndReturn(self.cinder_volume_snapshots.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        cinder.volume_list(IsA(
            http.HttpRequest)).AndReturn(self.cinder_volumes.list())
        cinder.extension_supported(IsA(http.HttpRequest), 'AvailabilityZones')\
            .AndReturn(True)
        cinder.availability_zone_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_availability_zones.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:create')
        res = self.client.post(url, formData)

        expected_error = [u'A volume of 5000GB cannot be created as you only'
                          ' have 20GB of your quota available.']
        self.assertEqual(res.context['form'].errors['__all__'], expected_error)

    @test.create_stubs({cinder: ('volume_snapshot_list',
                                 'volume_type_list',
                                 'volume_list',
                                 'availability_zone_list',
                                 'extension_supported'),
                        api.glance: ('image_list_detailed',),
                        quotas: ('tenant_limit_usages',)})
    def test_create_volume_number_over_alloted_quota(self):
        usage_limit = {'maxTotalVolumeGigabytes': 100,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': len(self.cinder_volumes.list())}
        formData = {'name': u'Too Many...',
                    'description': u'We have no volumes left!',
                    'method': u'CreateForm',
                    'size': 10}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
            AndReturn(self.cinder_volume_snapshots.list())
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       filters={'is_public': True,
                                                'status': 'active'}) \
                  .AndReturn([self.images.list(), False])
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                            filters={'property-owner_id': self.tenant.id,
                                     'status': 'active'}) \
                  .AndReturn([[], False])
        cinder.volume_list(IsA(
            http.HttpRequest)).AndReturn(self.cinder_volumes.list())
        cinder.extension_supported(IsA(http.HttpRequest), 'AvailabilityZones')\
            .AndReturn(True)
        cinder.availability_zone_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_availability_zones.list())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
                                AndReturn(usage_limit)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:create')
        res = self.client.post(url, formData)

        expected_error = [u'You are already using all of your available'
                          ' volumes.']
        self.assertEqual(res.context['form'].errors['__all__'], expected_error)

    @test.create_stubs({cinder: ('volume_list',
                                 'volume_snapshot_list',
                                 'volume_delete',),
                        api.nova: ('server_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_delete_volume(self):
        volumes = self.cinder_volumes.list()
        volume = self.cinder_volumes.first()
        formData = {'action':
                    'volumes__delete__%s' % volume.id}

        cinder.volume_list(IsA(http.HttpRequest), search_opts=None).\
            AndReturn(volumes)
        cinder.volume_delete(IsA(http.HttpRequest), volume.id)
        api.nova.server_list(IsA(http.HttpRequest), search_opts=None).\
            AndReturn([self.servers.list(), False])
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
            AndReturn(self.cinder_volume_snapshots.list())
        cinder.volume_list(IsA(http.HttpRequest), search_opts=None).\
            AndReturn(volumes)
        api.nova.server_list(IsA(http.HttpRequest), search_opts=None).\
            AndReturn([self.servers.list(), False])
        cinder.volume_list(IsA(http.HttpRequest)).AndReturn(volumes)
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).MultipleTimes().\
            AndReturn(self.quota_usages.first())

        self.mox.ReplayAll()

        url = VOLUME_INDEX_URL
        res = self.client.post(url, formData, follow=True)
        self.assertIn("Scheduled deletion of Volume: Volume name",
                      [m.message for m in res.context['messages']])

    @test.create_stubs({cinder: ('volume_list',
                                 'volume_snapshot_list',
                                 'volume_delete',),
                        api.nova: ('server_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_delete_volume_error_existing_snapshot(self):
        volume = self.cinder_volumes.first()
        volumes = self.cinder_volumes.list()
        formData = {'action':
                    'volumes__delete__%s' % volume.id}
        exc = self.exceptions.cinder.__class__(400,
                                               "error: dependent snapshots")

        cinder.volume_list(IsA(http.HttpRequest), search_opts=None).\
                           AndReturn(volumes)
        cinder.volume_delete(IsA(http.HttpRequest), volume.id).\
                             AndRaise(exc)
        api.nova.server_list(IsA(http.HttpRequest), search_opts=None).\
                             AndReturn([self.servers.list(), False])
        cinder.volume_list(IsA(http.HttpRequest), search_opts=None).\
                           AndReturn(volumes)
        api.nova.server_list(IsA(http.HttpRequest), search_opts=None).\
                             AndReturn([self.servers.list(), False])
        cinder.volume_snapshot_list(IsA(http.HttpRequest))\
              .AndReturn(self.cinder_volume_snapshots.list())
        cinder.volume_list(IsA(http.HttpRequest)).AndReturn(volumes)
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).MultipleTimes().\
                                   AndReturn(self.quota_usages.first())

        self.mox.ReplayAll()

        url = VOLUME_INDEX_URL
        res = self.client.post(url, formData, follow=True)
        self.assertEqual(list(res.context['messages'])[0].message,
                         u'Unable to delete volume "%s". '
                         u'One or more snapshots depend on it.' %
                         volume.name)

    @test.create_stubs({cinder: ('volume_get',), api.nova: ('server_list',)})
    def test_edit_attachments(self):
        PREV = settings.OPENSTACK_HYPERVISOR_FEATURES['can_set_mount_point']
        settings.OPENSTACK_HYPERVISOR_FEATURES['can_set_mount_point'] = True

        volume = self.cinder_volumes.first()
        servers = [s for s in self.servers.list()
                   if s.tenant_id == self.request.user.tenant_id]

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        api.nova.server_list(IsA(http.HttpRequest)).AndReturn([servers, False])
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:attach',
                      args=[volume.id])
        res = self.client.get(url)
        # Asserting length of 2 accounts for the one instance option,
        # and the one 'Choose Instance' option.
        form = res.context['form']
        self.assertEqual(len(form.fields['instance']._choices),
                         2)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(form.fields['device'].widget,
                                   widgets.TextInput))
        settings.OPENSTACK_HYPERVISOR_FEATURES['can_set_mount_point'] = PREV

    @test.create_stubs({cinder: ('volume_get',), api.nova: ('server_list',)})
    def test_edit_attachments_cannot_set_mount_point(self):

        volume = self.cinder_volumes.first()
        servers = [s for s in self.servers.list()
                   if s.tenant_id == self.request.user.tenant_id]

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        api.nova.server_list(IsA(http.HttpRequest)).AndReturn([servers, False])
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:attach',
                      args=[volume.id])
        res = self.client.get(url)
        # Assert the device field is hidden.
        form = res.context['form']
        self.assertTrue(isinstance(form.fields['device'].widget,
                                   widgets.HiddenInput))

    @test.create_stubs({cinder: ('volume_get',),
                        api.nova: ('server_get', 'server_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_edit_attachments_attached_volume(self):
        servers = [s for s in self.servers.list()
                   if s.tenant_id == self.request.user.tenant_id]
        server = servers[0]
        volume = self.cinder_volumes.list()[0]

        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
                          .AndReturn(volume)
        api.nova.server_list(IsA(http.HttpRequest)) \
                             .AndReturn([servers, False])

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:attach',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertEqual(res.context['form'].fields['instance']._choices[0][1],
                         "Select an instance")
        self.assertEqual(len(res.context['form'].fields['instance'].choices),
                         2)
        self.assertEqual(res.context['form'].fields['instance']._choices[1][0],
                         server.id)
        self.assertEqual(res.status_code, 200)

    @test.create_stubs({cinder: ('volume_list',
                                 'volume_snapshot_list'),
                        api.nova: ('server_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_create_button_disabled_when_quota_exceeded(self):
        quota_usages = self.quota_usages.first()
        quota_usages['volumes']['available'] = 0
        volumes = self.cinder_volumes.list()

        cinder.volume_list(IsA(http.HttpRequest), search_opts=None)\
              .AndReturn(volumes)
        api.nova.server_list(IsA(http.HttpRequest), search_opts=None)\
              .AndReturn([self.servers.list(), False])
        cinder.volume_snapshot_list(IsA(http.HttpRequest))\
              .AndReturn(self.cinder_volume_snapshots.list())
        cinder.volume_list(IsA(http.HttpRequest)).AndReturn(volumes)
        quotas.tenant_quota_usages(IsA(http.HttpRequest))\
              .MultipleTimes().AndReturn(quota_usages)

        self.mox.ReplayAll()

        res = self.client.get(VOLUME_INDEX_URL)
        self.assertTemplateUsed(res, 'project/volumes/index.html')

        volumes = res.context['volumes_table'].data
        self.assertItemsEqual(volumes, self.cinder_volumes.list())

        create_link = tables.CreateVolume()
        url = create_link.get_link_url()
        classes = list(create_link.get_default_classes())\
                    + list(create_link.classes)
        link_name = "%s (%s)" % (unicode(create_link.verbose_name),
                                 "Quota exceeded")
        expected_string = "<a href='%s' title='%s'  class='%s disabled' "\
                          "id='volumes__action_create'>%s</a>" \
                            % (url, link_name, " ".join(classes), link_name)
        self.assertContains(res, expected_string, html=True,
                            msg_prefix="The create button is not disabled")

    @test.create_stubs({cinder: ('volume_get',),
                        api.nova: ('server_get',)})
    def test_detail_view(self):
        volume = self.cinder_volumes.first()
        server = self.servers.first()

        volume.attachments = [{"server_id": server.id}]

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:detail',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertContains(res, "<h2>Volume Details: Volume name</h2>",
                            1, 200)
        self.assertContains(res, "<dd>Volume name</dd>", 1, 200)
        self.assertContains(res, "<dd>%s</dd>" % volume.id, 1, 200)
        self.assertContains(res, "<dd>Available</dd>", 1, 200)
        self.assertContains(res, "<dd>40 GB</dd>", 1, 200)
        self.assertContains(res,
                            ("<a href=\"/project/instances/1/\">%s</a>"
                             % server.name),
                            1,
                            200)

        self.assertNoMessages()

    @test.create_stubs({cinder: ('volume_get',)})
    def test_get_data(self):
        volume = self.cinder_volumes.get(name='v2_volume')
        volume._apiresource.name = ""

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)

        self.mox.ReplayAll()

        url = VOLUME_INDEX_URL + \
                "?action=row_update&table=volumes&obj_id=" + volume.id

        res = self.client.get(url, {},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(volume.name, volume.id)

    @test.create_stubs({cinder: ('volume_get',)})
    def test_detail_view_with_exception(self):
        volume = self.cinder_volumes.first()
        server = self.servers.first()

        volume.attachments = [{"server_id": server.id}]

        cinder.volume_get(IsA(http.HttpRequest), volume.id).\
            AndRaise(self.exceptions.cinder)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:detail',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, VOLUME_INDEX_URL)

    @test.create_stubs({cinder: ('volume_update',
                                 'volume_get',)})
    def test_update_volume(self):
        volume = self.cinder_volumes.get(name="my_volume")

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        cinder.volume_update(IsA(http.HttpRequest),
                             volume.id,
                             volume.name,
                             volume.description)

        self.mox.ReplayAll()

        formData = {'method': 'UpdateForm',
                    'name': volume.name,
                    'description': volume.description}

        url = reverse('horizon:project:volumes:volumes:update',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertRedirectsNoFollow(res, VOLUME_INDEX_URL)

    @test.create_stubs({cinder: ('volume_get',
                                 'volume_extend')})
    def test_extend_volume(self):
        volume = self.cinder_volumes.first()
        formData = {'name': u'A Volume I Am Making',
                    'orig_size': volume.size,
                    'new_size': 100}

        cinder.volume_get(IsA(http.HttpRequest), volume.id).\
                          AndReturn(self.cinder_volumes.first())

        cinder.volume_extend(IsA(http.HttpRequest),
                             volume.id,
                             formData['new_size']).AndReturn(volume)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:extend',
                      args=[volume.id])
        res = self.client.post(url, formData)

        redirect_url = VOLUME_INDEX_URL
        self.assertRedirectsNoFollow(res, redirect_url)

    @test.create_stubs({cinder: ('volume_get',),
                        quotas: ('tenant_limit_usages',)})
    def test_extend_volume_with_wrong_size(self):
        volume = self.cinder_volumes.first()
        usage_limit = {'maxTotalVolumeGigabytes': 100,
                       'gigabytesUsed': 20,
                       'volumesUsed': len(self.cinder_volumes.list()),
                       'maxTotalVolumes': 6}
        formData = {'name': u'A Volume I Am Making',
                    'orig_size': volume.size,
                    'new_size': 10}

        cinder.volume_get(IsA(http.HttpRequest), volume.id).\
            AndReturn(self.cinder_volumes.first())
        quotas.tenant_limit_usages(IsA(http.HttpRequest)).\
            AndReturn(usage_limit)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:volumes:extend',
                      args=[volume.id])
        res = self.client.post(url, formData)
        self.assertFormError(res, 'form', None,
                             "New size for extend must be greater than "
                             "current size.")
