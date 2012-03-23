# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright 2012 OpenStack LLC
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

"""
Views for managing Images and Snapshots.
"""

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import tables
from .images.tables import ImagesTable
from .snapshots.tables import SnapshotsTable
from .volume_snapshots.tables import VolumeSnapshotsTable


LOG = logging.getLogger(__name__)


class IndexView(tables.MultiTableView):
    table_classes = (ImagesTable, SnapshotsTable, VolumeSnapshotsTable)
    template_name = 'nova/images_and_snapshots/index.html'

    def get_images_data(self):
        try:
            all_images = api.image_list_detailed(self.request)
            images = [im for im in all_images
                      if im['container_format'] not in ['aki', 'ari'] and
                      getattr(im.properties, "image_type", '') != "snapshot"]
        except:
            images = []
            exceptions.handle(self.request, _("Unable to retrieve images."))
        return images

    def get_snapshots_data(self):
        try:
            snapshots = api.snapshot_list_detailed(self.request)
        except:
            snapshots = []
            exceptions.handle(self.request, _("Unable to retrieve snapshots."))
        return snapshots

    def get_volume_snapshots_data(self):
        try:
            snapshots = api.volume_snapshot_list(self.request)
        except:
            snapshots = []
            exceptions.handle(self.request, _("Unable to retrieve "
                    "volume snapshots."))
        return snapshots
