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

from django.core.urlresolvers import reverse
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from ..images.tables import ImagesTable, EditImage, DeleteImage, UpdateRow


LOG = logging.getLogger(__name__)


class LaunchSnapshot(tables.LinkAction):
    name = "launch_snapshot"
    verbose_name = _("Launch")
    url = "horizon:project:instances:launch"
    classes = ("btn-launch", "ajax-modal")

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"source_type": "instance_snapshot_id",
                            "source_id": self.table.get_object_id(datum)})
        return "?".join([base_url, params])

    def allowed(self, request, snapshot):
        return snapshot.status in ("active",)


class DeleteSnapshot(DeleteImage):
    data_type_singular = _("Snapshot")
    data_type_plural = _("Snapshots")


class SnapshotsTable(ImagesTable):
    class Meta(ImagesTable.Meta):
        name = "snapshots"
        verbose_name = _("Instance Snapshots")
        table_actions = (DeleteSnapshot,)
        row_actions = (LaunchSnapshot, EditImage, DeleteSnapshot)
        pagination_param = "snapshot_marker"
        row_class = UpdateRow
        status_columns = ["status"]
