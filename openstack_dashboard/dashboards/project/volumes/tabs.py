# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Nebula, Inc.
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

from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.volumes.snapshots \
    import tables as vol_snapshot_tables
from openstack_dashboard.dashboards.project.volumes.volumes \
    import tables as volume_tables


class VolumeTableMixIn(object):
    def _get_volumes(self, search_opts=None):
        try:
            return api.cinder.volume_list(self.request,
                                          search_opts=search_opts)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume list.'))
            return []

    def _get_instances(self, search_opts=None):
        try:
            instances, has_more = api.nova.server_list(self.request,
                                                       search_opts=search_opts)
            return instances
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve volume/instance "
                                "attachment information"))
            return []

    def _set_attachments_string(self, volumes, instances):
        instances = SortedDict([(inst.id, inst) for inst in instances])
        for volume in volumes:
            for att in volume.attachments:
                server_id = att.get('server_id', None)
                att['instance'] = instances.get(server_id, None)


class VolumeTab(tabs.TableTab, VolumeTableMixIn):
    table_classes = (volume_tables.VolumesTable,)
    name = _("Volumes")
    slug = "volumes_tab"
    template_name = ("horizon/common/_detail_table.html")

    def get_volumes_data(self):
        volumes = self._get_volumes()
        instances = self._get_instances()
        self._set_attachments_string(volumes, instances)
        return volumes


class SnapshotTab(tabs.TableTab):
    table_classes = (vol_snapshot_tables.VolumeSnapshotsTable,)
    name = _("Volume Snapshots")
    slug = "snapshots_tab"
    template_name = ("horizon/common/_detail_table.html")

    def get_volume_snapshots_data(self):
        if api.base.is_service_enabled(self.request, 'volume'):
            try:
                snapshots = api.cinder.volume_snapshot_list(self.request)
                volumes = api.cinder.volume_list(self.request)
                volumes = dict((v.id, v) for v in volumes)
            except Exception:
                snapshots = []
                volumes = {}
                exceptions.handle(self.request, _("Unable to retrieve "
                                                  "volume snapshots."))

            for snapshot in snapshots:
                volume = volumes.get(snapshot.volume_id)
                setattr(snapshot, '_volume', volume)

        else:
            snapshots = []
        return snapshots


class VolumeAndSnapshotTabs(tabs.TabGroup):
    slug = "volumes_and_snapshots"
    tabs = (VolumeTab, SnapshotTab,)
    sticky = True
