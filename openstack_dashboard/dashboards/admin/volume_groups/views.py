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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.volume_groups \
    import tables as volume_group_tables
from openstack_dashboard.dashboards.admin.volume_groups \
    import tabs as volume_group_tabs
from openstack_dashboard.dashboards.project.volume_groups \
    import views as volume_groups_views


class IndexView(tables.DataTableView):
    table_class = volume_group_tables.GroupsTable
    page_title = _("Groups")

    def get_data(self):
        try:
            groups = api.cinder.group_list_with_vol_type_names(
                self.request, {'all_tenants': 1})
        except Exception:
            groups = []
            exceptions.handle(self.request,
                              _("Unable to retrieve volume groups."))
        if not groups:
            return groups
        group_snapshots = api.cinder.group_snapshot_list(self.request)
        snapshot_groups = {gs.group_id for gs in group_snapshots}
        for g in groups:
            g.has_snapshots = g.id in snapshot_groups
        return groups


class DetailView(volume_groups_views.DetailView):
    tab_group_class = volume_group_tabs.GroupsDetailTabs

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        table = volume_group_tables.GroupsTable(self.request)
        context["actions"] = table.render_row_actions(context["group"])
        return context

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:admin:volume_groups:index')
