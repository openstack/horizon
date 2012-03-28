# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import tables
from ...instances_and_volumes.volumes import tables as volume_tables


LOG = logging.getLogger(__name__)


class DeleteVolumeSnapshot(tables.DeleteAction):
    data_type_singular = _("Volume Snapshot")
    data_type_plural = _("Volume Snapshots")

    def delete(self, request, obj_id):
        api.volume_snapshot_delete(request, obj_id)


class VolumeSnapshotsTable(volume_tables.VolumesTableBase):
    volume_id = tables.Column("volume_id", verbose_name=_("Volume ID"))

    class Meta:
        name = "volume_snapshots"
        verbose_name = _("Volume Snapshots")
        table_actions = (DeleteVolumeSnapshot,)
        row_actions = (DeleteVolumeSnapshot,)
