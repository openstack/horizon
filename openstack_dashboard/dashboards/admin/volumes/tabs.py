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
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import tabs

from openstack_dashboard.api import keystone

from openstack_dashboard.dashboards.admin.volumes.volumes \
    import tables as volumes_tables
from openstack_dashboard.dashboards.project.volumes \
    import views as volumes_views


class VolumeTab(tables.PagedTableMixin, tabs.TableTab,
                volumes_views.VolumeTableMixIn, tables.DataTableView):
    table_classes = (volumes_tables.VolumesTable,)
    name = _("Volumes")
    slug = "volumes_tab"
    template_name = "admin/volumes/volumes/volumes_tables.html"
    preload = False
    FILTERS_MAPPING = {'bootable': {_('yes'): 'true', _('no'): 'false'},
                       'encrypted': {_('yes'): True, _('no'): False}}

    def get_volumes_data(self):
        default_filters = {'all_tenants': True}

        filters = self.get_filters(default_filters.copy())
        filter_first = getattr(settings, 'FILTER_DATA_FIRST', {})
        volumes = []

        self.table.needs_filter_first = False

        if filter_first.get('admin.volumes', False) and \
                len(filters) == len(default_filters):
            self.table.needs_filter_first = True
            return volumes

        if 'project' in filters:
            # Keystone returns a tuple ([],false) where the first element is
            # tenant list that's why the 0 is hardcoded below
            tenants = keystone.tenant_list(self.request)[0]
            tenant_ids = [t.id for t in tenants
                          if t.name == filters['project']]
            if not tenant_ids:
                return []
            del filters['project']
            for id in tenant_ids:
                filters['project_id'] = id
                volumes += self._get_volumes(search_opts=filters)
        else:
            volumes = self._get_volumes(search_opts=filters)

        attached_instance_ids = self._get_attached_instance_ids(volumes)
        instances = self._get_instances(search_opts={'all_tenants': True},
                                        instance_ids=attached_instance_ids)
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

    def get_filters(self, filters):
        self.table = self._tables['volumes']
        self.handle_server_filter(self.request, table=self.table)
        self.update_server_filter_action(self.request, table=self.table)
        filters = super(VolumeTab, self).get_filters(filters,
                                                     self.FILTERS_MAPPING)
        return filters


class VolumesGroupTabs(tabs.TabGroup):
    slug = "volumes_group_tabs"
    tabs = (VolumeTab, )
    sticky = True
