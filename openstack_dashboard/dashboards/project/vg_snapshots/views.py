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
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.project.vg_snapshots \
    import forms as vg_snapshot_forms
from openstack_dashboard.dashboards.project.vg_snapshots \
    import tables as vg_snapshot_tables
from openstack_dashboard.dashboards.project.vg_snapshots \
    import tabs as vg_snapshot_tabs

INDEX_URL = "horizon:project:vg_snapshots:index"


class IndexView(tables.DataTableView):
    table_class = vg_snapshot_tables.GroupSnapshotsTable
    page_title = _("Group Snapshots")

    def get_data(self):
        try:
            vg_snapshots = api.cinder.group_snapshot_list(self.request)
        except Exception:
            vg_snapshots = []
            exceptions.handle(self.request, _("Unable to retrieve "
                                              "volume group snapshots."))
        try:
            groups = dict((g.id, g) for g
                          in api.cinder.group_list(self.request))
        except Exception:
            groups = {}
            exceptions.handle(self.request,
                              _("Unable to retrieve volume groups."))
        for gs in vg_snapshots:
            gs.group = groups.get(gs.group_id)
        return vg_snapshots


class DetailView(tabs.TabView):
    tab_group_class = vg_snapshot_tabs.DetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ vg_snapshot.name|default:vg_snapshot.id }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        vg_snapshot = self.get_data()
        table = vg_snapshot_tables.GroupSnapshotsTable(self.request)
        context["vg_snapshot"] = vg_snapshot
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(vg_snapshot)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            vg_snapshot_id = self.kwargs['vg_snapshot_id']
            vg_snapshot = api.cinder.group_snapshot_get(self.request,
                                                        vg_snapshot_id)

            group_id = vg_snapshot.group_id
            group = api.cinder.group_get(self.request, group_id)
            vg_snapshot.vg_name = group.name
            vg_snapshot.volume_type_names = []
            for vol_type_id in group.volume_types:
                vol_type = api.cinder.volume_type_get(self.request,
                                                      vol_type_id)
                vg_snapshot.volume_type_names.append(vol_type.name)

            vg_snapshot.volume_names = []
            search_opts = {'group_id': group_id}
            volumes = api.cinder.volume_list(self.request,
                                             search_opts=search_opts)
            for volume in volumes:
                vg_snapshot.volume_names.append(volume.name)

        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve group snapshot details.'),
                              redirect=redirect)
        return vg_snapshot

    @staticmethod
    def get_redirect_url():
        return reverse(INDEX_URL)

    def get_tabs(self, request, *args, **kwargs):
        vg_snapshot = self.get_data()
        return self.tab_group_class(request, vg_snapshot=vg_snapshot, **kwargs)


class CreateGroupView(forms.ModalFormView):
    form_class = vg_snapshot_forms.CreateGroupForm
    template_name = 'project/vg_snapshots/create.html'
    submit_url = "horizon:project:vg_snapshots:create_group"
    success_url = reverse_lazy('horizon:project:volume_groups:index')
    page_title = _("Create Volume Group")

    def get_context_data(self, **kwargs):
        context = super(CreateGroupView, self).get_context_data(**kwargs)
        context['vg_snapshot_id'] = self.kwargs['vg_snapshot_id']
        args = (self.kwargs['vg_snapshot_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        try:
            # get number of volumes we will be creating
            vg_snapshot = cinder.group_snapshot_get(
                self.request, context['vg_snapshot_id'])

            group_id = vg_snapshot.group_id

            search_opts = {'group_id': group_id}
            volumes = api.cinder.volume_list(self.request,
                                             search_opts=search_opts)
            num_volumes = len(volumes)
            usages = quotas.tenant_quota_usages(
                self.request, targets=('volumes', 'gigabytes'))

            if (usages['volumes']['used'] + num_volumes >
                    usages['volumes']['quota']):
                raise ValueError(_('Unable to create group due to '
                                   'exceeding volume quota limit.'))
            else:
                context['numRequestedItems'] = num_volumes
                context['usages'] = usages

        except ValueError as e:
            exceptions.handle(self.request, e.message)
            return None
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve group information.'))
        return context

    def get_initial(self):
        return {'vg_snapshot_id': self.kwargs["vg_snapshot_id"]}
