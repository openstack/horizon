# Copyright 2019 NEC Corporation
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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.vg_snapshots \
    import tables as admin_tables
from openstack_dashboard.dashboards.admin.vg_snapshots \
    import tabs as admin_tabs
from openstack_dashboard.dashboards.project.vg_snapshots \
    import views as project_views

INDEX_URL = "horizon:admin:vg_snapshots:index"


class IndexView(tables.DataTableView):
    table_class = admin_tables.GroupSnapshotsTable
    page_title = _("Group Snapshots")

    def get_data(self):
        try:
            vg_snapshots = api.cinder.group_snapshot_list(
                self.request, {'all_tenants': 1})
        except Exception:
            vg_snapshots = []
            exceptions.handle(self.request, _("Unable to retrieve "
                                              "volume group snapshots."))
        try:
            groups = dict((g.id, g) for g
                          in api.cinder.group_list(self.request,
                                                   {'all_tenants': 1}))
        except Exception:
            groups = {}
            exceptions.handle(self.request,
                              _("Unable to retrieve volume groups."))
        for vg_snapshot in vg_snapshots:
            vg_snapshot.group = groups.get(vg_snapshot.group_id)
        return vg_snapshots


class DetailView(project_views.DetailView):
    tab_group_class = admin_tabs.DetailTabs

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        table = admin_tables.GroupSnapshotsTable(self.request)
        context["actions"] = table.render_row_actions(context["vg_snapshot"])
        return context

    @staticmethod
    def get_redirect_url():
        return reverse(INDEX_URL)
