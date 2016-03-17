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

from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard import policy

from openstack_dashboard.dashboards.project.volumes.backups \
    import tables as backups_tables
from openstack_dashboard.dashboards.project.volumes.cgroups \
    import tables as vol_cgroup_tables
from openstack_dashboard.dashboards.project.volumes.snapshots \
    import tables as vol_snapshot_tables
from openstack_dashboard.dashboards.project.volumes.volumes \
    import tables as volume_tables


class VolumeTableMixIn(object):
    _has_more_data = False
    _has_prev_data = False

    def _get_volumes(self, search_opts=None):
        try:
            marker, sort_dir = self._get_marker()
            volumes, self._has_more_data, self._has_prev_data = \
                api.cinder.volume_list_paged(self.request, marker=marker,
                                             search_opts=search_opts,
                                             sort_dir=sort_dir, paginate=True)

            if sort_dir == "asc":
                volumes.reverse()

            return volumes
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume list.'))
            return []

    def _get_instances(self, search_opts=None, instance_ids=None):
        if not instance_ids:
            return []
        try:
            # TODO(tsufiev): we should pass attached_instance_ids to
            # nova.server_list as soon as Nova API allows for this
            instances, has_more = api.nova.server_list(self.request,
                                                       search_opts=search_opts)
            return instances
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve volume/instance "
                                "attachment information"))
            return []

    def _get_volumes_ids_with_snapshots(self, search_opts=None):
        try:
            volume_ids = []
            snapshots = api.cinder.volume_snapshot_list(
                self.request, search_opts=search_opts)
            if snapshots:
                # extract out the volume ids
                volume_ids = set([(s.volume_id) for s in snapshots])
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve snapshot list."))

        return volume_ids

    def _get_attached_instance_ids(self, volumes):
        attached_instance_ids = []
        for volume in volumes:
            for att in volume.attachments:
                server_id = att.get('server_id', None)
                if server_id is not None:
                    attached_instance_ids.append(server_id)
        return attached_instance_ids

    # set attachment string and if volume has snapshots
    def _set_volume_attributes(self,
                               volumes,
                               instances,
                               volume_ids_with_snapshots):
        instances = OrderedDict([(inst.id, inst) for inst in instances])
        for volume in volumes:
            if volume_ids_with_snapshots:
                if volume.id in volume_ids_with_snapshots:
                    setattr(volume, 'has_snapshot', True)
            if instances:
                for att in volume.attachments:
                    server_id = att.get('server_id', None)
                    att['instance'] = instances.get(server_id, None)


class PagedTableMixin(object):
    def __init__(self, *args, **kwargs):
        super(PagedTableMixin, self).__init__(*args, **kwargs)
        self._has_prev_data = False
        self._has_more_data = False

    def has_prev_data(self, table):
        return self._has_prev_data

    def has_more_data(self, table):
        return self._has_more_data

    def _get_marker(self):
        meta = self.table_classes[0]._meta
        prev_marker = self.request.GET.get(meta.prev_pagination_param, None)
        if prev_marker:
            return prev_marker, "asc"
        else:
            marker = self.request.GET.get(meta.pagination_param, None)
            if marker:
                return marker, "desc"
            return None, "desc"


class VolumeTab(PagedTableMixin, tabs.TableTab, VolumeTableMixIn):
    table_classes = (volume_tables.VolumesTable,)
    name = _("Volumes")
    slug = "volumes_tab"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_volumes_data(self):
        volumes = self._get_volumes()
        attached_instance_ids = self._get_attached_instance_ids(volumes)
        instances = self._get_instances(instance_ids=attached_instance_ids)
        volume_ids_with_snapshots = self._get_volumes_ids_with_snapshots()
        self._set_volume_attributes(
            volumes, instances, volume_ids_with_snapshots)
        return volumes


class SnapshotTab(PagedTableMixin, tabs.TableTab):
    table_classes = (vol_snapshot_tables.VolumeSnapshotsTable,)
    name = _("Volume Snapshots")
    slug = "snapshots_tab"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_volume_snapshots_data(self):
        snapshots = []
        volumes = {}
        if api.base.is_service_enabled(self.request, 'volumev2'):
            try:
                marker, sort_dir = self._get_marker()
                snapshots, self._has_more_data, self._has_prev_data = \
                    api.cinder.volume_snapshot_list_paged(
                        self.request, paginate=True, marker=marker,
                        sort_dir=sort_dir)
                volumes = api.cinder.volume_list(self.request)
                volumes = dict((v.id, v) for v in volumes)
            except Exception:
                exceptions.handle(self.request, _("Unable to retrieve "
                                                  "volume snapshots."))

        for snapshot in snapshots:
            volume = volumes.get(snapshot.volume_id)
            setattr(snapshot, '_volume', volume)

        return snapshots


class BackupsTab(PagedTableMixin, tabs.TableTab, VolumeTableMixIn):
    table_classes = (backups_tables.BackupsTable,)
    name = _("Volume Backups")
    slug = "backups_tab"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def allowed(self, request):
        return api.cinder.volume_backup_supported(self.request)

    def get_volume_backups_data(self):
        try:
            marker, sort_dir = self._get_marker()
            backups, self._has_more_data, self._has_prev_data = \
                api.cinder.volume_backup_list_paged(
                    self.request, marker=marker, sort_dir=sort_dir,
                    paginate=True)
            volumes = api.cinder.volume_list(self.request)
            volumes = dict((v.id, v) for v in volumes)
            for backup in backups:
                backup.volume = volumes.get(backup.volume_id)
        except Exception:
            backups = []
            exceptions.handle(self.request, _("Unable to retrieve "
                                              "volume backups."))
        return backups


class CGroupsTab(tabs.TableTab, VolumeTableMixIn):
    table_classes = (vol_cgroup_tables.VolumeCGroupsTable,)
    name = _("Volume Consistency Groups")
    slug = "cgroups_tab"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def allowed(self, request):
        return policy.check(
            (("volume", "consistencygroup:get_all"),),
            request
        )

    def get_volume_cgroups_data(self):
        try:
            cgroups = api.cinder.volume_cgroup_list_with_vol_type_names(
                self.request)
            for cgroup in cgroups:
                setattr(cgroup, '_volume_tab', self.tab_group.tabs[0])
        except Exception:
            cgroups = []
            exceptions.handle(self.request, _("Unable to retrieve "
                                              "volume consistency groups."))
        return cgroups


class VolumeAndSnapshotTabs(tabs.TabGroup):
    slug = "volumes_and_snapshots"
    tabs = (VolumeTab, SnapshotTab, BackupsTab, CGroupsTab)
    sticky = True
