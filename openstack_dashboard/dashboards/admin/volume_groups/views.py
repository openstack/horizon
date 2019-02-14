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
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.volume_groups \
    import forms as admin_forms
from openstack_dashboard.dashboards.admin.volume_groups \
    import tables as admin_tables
from openstack_dashboard.dashboards.admin.volume_groups \
    import tabs as admin_tabs
from openstack_dashboard.dashboards.admin.volume_groups \
    import workflows as admin_workflows
from openstack_dashboard.dashboards.project.volume_groups \
    import views as project_views


class IndexView(tables.DataTableView):
    table_class = admin_tables.GroupsTable
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

        # Gather our tenants to correlate against Group IDs
        try:
            tenants, has_more = api.keystone.tenant_list(self.request)
        except Exception:
            tenants = []
            msg = _('Unable to retrieve volume group project information.')
            exceptions.handle(self.request, msg)

        tenant_dict = dict((t.id, t) for t in tenants)
        for g in groups:
            g.has_snapshots = g.id in snapshot_groups
            tenant_id = getattr(g, "project_id", None)
            tenant = tenant_dict.get(tenant_id)

            # NOTE: If horizon is using cinder API microversion below '3.58',
            # it doesn't include any 'project id' information in group's
            # object.
            g.tenant_name = getattr(tenant, "name", None)
        return groups


class RemoveVolumesView(project_views.RemoveVolumesView):
    template_name = 'admin/volume_groups/remove_vols.html'
    form_class = admin_forms.RemoveVolsForm
    success_url = reverse_lazy('horizon:admin:volume_groups:index')
    submit_url = "horizon:admin:volume_groups:remove_volumes"


class DeleteView(project_views.DeleteView):
    template_name = 'admin/volume_groups/delete.html'
    form_class = admin_forms.DeleteForm
    success_url = reverse_lazy('horizon:admin:volume_groups:index')
    submit_url = "horizon:admin:volume_groups:delete"


class ManageView(project_views.ManageView):
    workflow_class = admin_workflows.UpdateGroupWorkflow


class DetailView(project_views.DetailView):
    tab_group_class = admin_tabs.GroupsDetailTabs

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        table = admin_tables.GroupsTable(self.request)
        context["actions"] = table.render_row_actions(context["group"])
        return context

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:admin:volume_groups:index')
