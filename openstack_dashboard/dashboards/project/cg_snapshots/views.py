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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.project.cg_snapshots \
    import forms as cg_snapshot_forms
from openstack_dashboard.dashboards.project.cg_snapshots \
    import tables as cg_snapshot_tables
from openstack_dashboard.dashboards.project.cg_snapshots \
    import tabs as cg_snapshot_tabs

CGROUP_INFO_FIELDS = ("name",
                      "description")

INDEX_URL = "horizon:project:cg_snapshots:index"


class CGSnapshotsView(tables.DataTableView):
    table_class = cg_snapshot_tables.CGSnapshotsTable
    page_title = _("Consistency Group Snapshots")

    def get_data(self):
        try:
            cg_snapshots = api.cinder.volume_cg_snapshot_list(self.request)
        except Exception:
            cg_snapshots = []
            exceptions.handle(self.request, _("Unable to retrieve "
                                              "volume consistency group "
                                              "snapshots."))
        return cg_snapshots


class DetailView(tabs.TabView):
    tab_group_class = cg_snapshot_tabs.CGSnapshotsDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ cg_snapshot.name|default:cg_snapshot.id }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        cg_snapshot = self.get_data()
        table = cg_snapshot_tables.CGSnapshotsTable(self.request)
        context["cg_snapshot"] = cg_snapshot
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(cg_snapshot)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            cg_snapshot_id = self.kwargs['cg_snapshot_id']
            cg_snapshot = api.cinder.volume_cg_snapshot_get(self.request,
                                                            cg_snapshot_id)

            cgroup_id = cg_snapshot.consistencygroup_id
            cgroup = api.cinder.volume_cgroup_get(self.request,
                                                  cgroup_id)
            cg_snapshot.cg_name = cgroup.name
            cg_snapshot.volume_type_names = []
            for vol_type_id in cgroup.volume_types:
                vol_type = api.cinder.volume_type_get(self.request,
                                                      vol_type_id)
                cg_snapshot.volume_type_names.append(vol_type.name)

            cg_snapshot.volume_names = []
            search_opts = {'consistencygroup_id': cgroup_id}
            volumes = api.cinder.volume_list(self.request,
                                             search_opts=search_opts)
            for volume in volumes:
                cg_snapshot.volume_names.append(volume.name)

        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve consistency group '
                                'snapshot details.'),
                              redirect=redirect)
        return cg_snapshot

    @staticmethod
    def get_redirect_url():
        return reverse(INDEX_URL)

    def get_tabs(self, request, *args, **kwargs):
        cg_snapshot = self.get_data()
        return self.tab_group_class(request, cg_snapshot=cg_snapshot, **kwargs)


class CreateCGroupView(forms.ModalFormView):
    form_class = cg_snapshot_forms.CreateCGroupForm
    template_name = 'project/cg_snapshots/create.html'
    submit_url = "horizon:project:cg_snapshots:create_cgroup"
    success_url = reverse_lazy('horizon:project:cgroups:index')
    page_title = _("Create Volume Consistency Group")

    def get_context_data(self, **kwargs):
        context = super(CreateCGroupView, self).get_context_data(**kwargs)
        context['cg_snapshot_id'] = self.kwargs['cg_snapshot_id']
        args = (self.kwargs['cg_snapshot_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        try:
            # get number of volumes we will be creating
            cg_snapshot = cinder.volume_cg_snapshot_get(
                self.request, context['cg_snapshot_id'])

            cgroup_id = cg_snapshot.consistencygroup_id

            search_opts = {'consistencygroup_id': cgroup_id}
            volumes = api.cinder.volume_list(self.request,
                                             search_opts=search_opts)
            num_volumes = len(volumes)
            usages = quotas.tenant_limit_usages(self.request)

            if usages['totalVolumesUsed'] + num_volumes > \
                    usages['maxTotalVolumes']:
                raise ValueError(_('Unable to create consistency group due to '
                                   'exceeding volume quota limit.'))
            else:
                usages['numRequestedItems'] = num_volumes
                context['usages'] = usages

        except ValueError as e:
            exceptions.handle(self.request, e.message)
            return None
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve consistency '
                                'group information.'))
        return context

    def get_initial(self):
        return {'cg_snapshot_id': self.kwargs["cg_snapshot_id"]}
