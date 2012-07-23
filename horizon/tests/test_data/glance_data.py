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

from glanceclient.v1.images import Image, ImageManager

from .utils import TestDataContainer


def data(TEST):
    TEST.images = TestDataContainer()
    TEST.snapshots = TestDataContainer()

    # Snapshots
    snapshot_dict = {'name': u'snapshot',
                     'container_format': u'ami',
                     'id': 3,
                     'status': "active",
                     'owner': TEST.tenant.id,
                     'properties': {'image_type': u'snapshot'}}
    snapshot_dict_no_owner = {'name': u'snapshot 2',
                              'container_format': u'ami',
                              'id': 4,
                              'status': "active",
                              'owner': None,
                              'properties': {'image_type': u'snapshot'}}
    snapshot_dict_queued = {'name': u'snapshot 2',
                            'container_format': u'ami',
                            'id': 5,
                            'status': "queued",
                            'owner': TEST.tenant.id,
                            'properties': {'image_type': u'snapshot'}}
    snapshot = Image(ImageManager(None), snapshot_dict)
    TEST.snapshots.add(snapshot)
    snapshot = Image(ImageManager(None), snapshot_dict_no_owner)
    TEST.snapshots.add(snapshot)
    snapshot = Image(ImageManager(None), snapshot_dict_queued)
    TEST.snapshots.add(snapshot)

    # Images
    image_dict = {'id': '007e7d55-fe1e-4c5c-bf08-44b4a4964822',
                  'name': 'public_image',
                  'status': "active",
                  'owner': TEST.tenant.id,
                  'container_format': 'novaImage',
                  'properties': {'image_type': u'image'}}
    public_image = Image(ImageManager(None), image_dict)

    image_dict = {'id': 'a001c047-22f8-47d0-80a1-8ec94a9524fe',
                  'name': 'private_image',
                  'status': "active",
                  'owner': TEST.tenant.id,
                  'container_format': 'aki'}
    private_image = Image(ImageManager(None), image_dict)

    image_dict = {'id': '278905a6-4b52-4d1e-98f9-8c57bb25ba32',
                  'name': 'public_image 2',
                  'status': "active",
                  'owner': TEST.tenant.id,
                  'container_format': 'novaImage',
                  'properties': {'image_type': u'image'}}
    public_image2 = Image(ImageManager(None), image_dict)

    image_dict = {'id': '710a1acf-a3e3-41dd-a32d-5d6b6c86ea10',
                  'name': 'private_image 2',
                  'status': "active",
                  'owner': TEST.tenant.id,
                  'container_format': 'aki'}
    private_image2 = Image(ImageManager(None), image_dict)

    image_dict = {'id': '7cd892fd-5652-40f3-a450-547615680132',
                  'name': 'private_image 3',
                  'status': "active",
                  'owner': TEST.tenant.id,
                  'container_format': 'aki'}
    private_image3 = Image(ImageManager(None), image_dict)

    TEST.images.add(public_image, private_image,
                    public_image2, private_image2, private_image3)
