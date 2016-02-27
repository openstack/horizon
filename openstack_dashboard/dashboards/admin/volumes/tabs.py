# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from collections import OrderedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone

from openstack_dashboard.dashboards.admin.volumes.snapshots \
    import tables as snapshots_tables
from openstack_dashboard.dashboards.admin.volumes.volume_types \
    import tables as volume_types_tables
from openstack_dashboard.dashboards.admin.volumes.volumes \
    import tables as volumes_tables
from openstack_dashboard.dashboards.project.volumes \
    import tabs as volumes_tabs


class VolumeTab(volumes_tabs.PagedTableMixin, tabs.TableTab,
                volumes_tabs.VolumeTableMixIn):
    table_classes = (volumes_tables.VolumesTable,)
    name = _("Volumes")
    slug = "volumes_tab"
    template_name = "admin/volumes/volumes/volumes_tables.html"
    preload = False

    def get_volumes_data(self):
        volumes = self._get_volumes(search_opts={'all_tenants': True})
        instances = self._get_instances(search_opts={'all_tenants': True})
        volume_ids_with_snapshots = self._get_volumes_ids_with_snapshots(
            search_opts={'all_tenants': True})
        self._set_volume_attributes(
            volumes, instances, volume_ids_with_snapshots)

        # Gather our tenants to correlate against IDs
        try:
            tenants, has_more = keystone.tenant_list(self.request)
        except Exception:
            tenants = []
            msg = _('Unable to retrieve volume project information.')
            exceptions.handle(self.request, msg)

        tenant_dict = OrderedDict([(t.id, t) for t in tenants])
        for volume in volumes:
            tenant_id = getattr(volume, "os-vol-tenant-attr:tenant_id", None)
            tenant = tenant_dict.get(tenant_id, None)
            volume.tenant_name = getattr(tenant, "name", None)

        return volumes


class VolumeTypesTab(tabs.TableTab, volumes_tabs.VolumeTableMixIn):
    table_classes = (volume_types_tables.VolumeTypesTable,
                     volume_types_tables.QosSpecsTable)
    name = _("Volume Types")
    slug = "volume_types_tab"
    template_name = "admin/volumes/volume_types/volume_types_tables.html"
    preload = False

    def get_volume_types_data(self):
        try:
            volume_types = \
                cinder.volume_type_list_with_qos_associations(self.request)
        except Exception:
            volume_types = []
            exceptions.handle(self.request,
                              _("Unable to retrieve volume types"))

        # Gather volume type encryption information
        try:
            vol_type_enc_list = cinder.volume_encryption_type_list(
                self.request)
        except Exception:
            vol_type_enc_list = []
            msg = _('Unable to retrieve volume type encryption information.')
            exceptions.handle(self.request, msg)

        vol_type_enc_dict = OrderedDict([(e.volume_type_id, e) for e in
                                        vol_type_enc_list])
        for volume_type in volume_types:
            vol_type_enc = vol_type_enc_dict.get(volume_type.id, None)
            if vol_type_enc is not None:
                volume_type.encryption = vol_type_enc
                volume_type.encryption.name = volume_type.name
            else:
                volume_type.encryption = None

        return volume_types

    def get_qos_specs_data(self):
        try:
            qos_specs = cinder.qos_spec_list(self.request)
        except Exception:
            qos_specs = []
            exceptions.handle(self.request,
                              _("Unable to retrieve QoS specs"))
        return qos_specs


class SnapshotTab(volumes_tabs.PagedTableMixin, tabs.TableTab):
    table_classes = (snapshots_tables.VolumeSnapshotsTable,)
    name = _("Volume Snapshots")
    slug = "snapshots_tab"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_volume_snapshots_data(self):
        if cinder.is_volume_service_enabled(self.request):
            try:
                marker, sort_dir = self._get_marker()
                snapshots, self._has_more_data, self._has_prev_data = \
                    cinder.volume_snapshot_list_paged(
                        self.request, paginate=True, marker=marker,
                        sort_dir=sort_dir, search_opts={'all_tenants': True})
                volumes = cinder.volume_list(
                    self.request,
                    search_opts={'all_tenants': True})
                volumes = dict((v.id, v) for v in volumes)
            except Exception:
                snapshots = []
                volumes = {}
                exceptions.handle(self.request, _("Unable to retrieve "
                                                  "volume snapshots."))

            # Gather our tenants to correlate against volume IDs
            try:
                tenants, has_more = keystone.tenant_list(self.request)
            except Exception:
                tenants = []
                msg = _('Unable to retrieve volume project information.')
                exceptions.handle(self.request, msg)

            tenant_dict = dict([(t.id, t) for t in tenants])
            for snapshot in snapshots:
                volume = volumes.get(snapshot.volume_id)
                tenant_id = getattr(volume,
                                    'os-vol-tenant-attr:tenant_id', None)
                tenant = tenant_dict.get(tenant_id, None)
                snapshot._volume = volume
                snapshot.tenant_name = getattr(tenant, "name", None)
                snapshot.host_name = getattr(
                    volume, 'os-vol-host-attr:host', None)

        else:
            snapshots = []
        return sorted(snapshots,
                      key=lambda snapshot: snapshot.tenant_name or '')


class VolumesGroupTabs(tabs.TabGroup):
    slug = "volumes_group_tabs"
    tabs = (VolumeTab, VolumeTypesTab, SnapshotTab)
    sticky = True
