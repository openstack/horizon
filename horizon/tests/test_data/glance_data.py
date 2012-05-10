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
    snapshot = Image(ImageManager(None), snapshot_dict)
    TEST.snapshots.add(snapshot)

    # Images
    image_dict = {'id': '1',
                  'name': 'public_image',
                  'status': "active",
                  'owner': TEST.tenant.id,
                  'container_format': 'novaImage',
                  'properties': {'image_type': u'image'}}
    public_image = Image(ImageManager(None), image_dict)

    image_dict = {'id': '2',
                  'name': 'private_image',
                  'status': "active",
                  'owner': TEST.tenant.id,
                  'container_format': 'aki'}
    private_image = Image(ImageManager(None), image_dict)

    TEST.images.add(public_image, private_image)
