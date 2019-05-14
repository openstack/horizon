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
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.project.volume_groups \
    import forms as vol_group_forms
from openstack_dashboard.dashboards.project.volume_groups \
    import tables as vol_group_tables
from openstack_dashboard.dashboards.project.volume_groups \
    import tabs as vol_group_tabs
from openstack_dashboard.dashboards.project.volume_groups \
    import workflows as vol_group_workflows

INDEX_URL = "horizon:project:volume_groups:index"


class IndexView(tables.DataTableView):
    table_class = vol_group_tables.GroupsTable
    page_title = _("Groups")

    def get_data(self):
        try:
            groups = api.cinder.group_list_with_vol_type_names(self.request)
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


class CreateView(workflows.WorkflowView):
    workflow_class = vol_group_workflows.CreateGroupWorkflow
    template_name = 'project/volume_groups/create.html'
    page_title = _("Create Volume Group")


class UpdateView(forms.ModalFormView):
    template_name = 'project/volume_groups/update.html'
    page_title = _("Edit Group")
    form_class = vol_group_forms.UpdateForm
    success_url = reverse_lazy('horizon:project:volume_groups:index')
    submit_url = "horizon:project:volume_groups:update"

    def get_initial(self):
        group = self.get_object()
        return {'group_id': self.kwargs["group_id"],
                'name': group.name,
                'description': group.description}

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['group_id'] = self.kwargs['group_id']
        args = (self.kwargs['group_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_object(self):
        group_id = self.kwargs['group_id']
        try:
            self._object = cinder.group_get(self.request, group_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve group details.'),
                              redirect=reverse(INDEX_URL))
        return self._object


class RemoveVolumesView(forms.ModalFormView):
    template_name = 'project/volume_groups/remove_vols.html'
    page_title = _("Remove Volumes from Group")
    form_class = vol_group_forms.RemoveVolsForm
    success_url = reverse_lazy('horizon:project:volume_groups:index')
    submit_url = "horizon:project:volume_groups:remove_volumes"

    def get_initial(self):
        group = self.get_object()
        return {'group_id': self.kwargs["group_id"],
                'name': group.name}

    def get_context_data(self, **kwargs):
        context = super(RemoveVolumesView, self).get_context_data(**kwargs)
        context['group_id'] = self.kwargs['group_id']
        args = (self.kwargs['group_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_object(self):
        group_id = self.kwargs['group_id']
        try:
            self._object = cinder.group_get(self.request, group_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve group details.'),
                              redirect=reverse(INDEX_URL))
        return self._object


class DeleteView(forms.ModalFormView):
    template_name = 'project/volume_groups/delete.html'
    page_title = _("Delete Group")
    form_class = vol_group_forms.DeleteForm
    success_url = reverse_lazy('horizon:project:volume_groups:index')
    submit_url = "horizon:project:volume_groups:delete"
    submit_label = page_title

    def get_initial(self):
        group = self.get_object()
        return {'group_id': self.kwargs["group_id"],
                'name': group.name}

    def get_context_data(self, **kwargs):
        context = super(DeleteView, self).get_context_data(**kwargs)
        context['group_id'] = self.kwargs['group_id']
        args = (self.kwargs['group_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_object(self):
        group_id = self.kwargs['group_id']
        try:
            self._object = cinder.group_get(self.request, group_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve group details.'),
                              redirect=reverse(INDEX_URL))
        return self._object


class ManageView(workflows.WorkflowView):
    workflow_class = vol_group_workflows.UpdateGroupWorkflow

    def get_context_data(self, **kwargs):
        context = super(ManageView, self).get_context_data(**kwargs)
        context['group_id'] = self.kwargs["group_id"]
        return context

    def _get_object(self, *args, **kwargs):
        group_id = self.kwargs['group_id']
        try:
            group = cinder.group_get(self.request, group_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve group details.'),
                              redirect=reverse(INDEX_URL))
        return group

    def get_initial(self):
        group = self._get_object()
        return {'group_id': group.id,
                'name': group.name,
                'description': group.description,
                'vtypes': getattr(group, "volume_types")}


class CreateSnapshotView(forms.ModalFormView):
    form_class = vol_group_forms.CreateSnapshotForm
    page_title = _("Create Group Snapshot")
    template_name = 'project/volume_groups/create_snapshot.html'
    submit_label = _("Create Snapshot")
    submit_url = "horizon:project:volume_groups:create_snapshot"
    success_url = reverse_lazy('horizon:project:vg_snapshots:index')

    def get_context_data(self, **kwargs):
        context = super(CreateSnapshotView, self).get_context_data(**kwargs)
        context['group_id'] = self.kwargs['group_id']
        args = (self.kwargs['group_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        try:
            # get number of snapshots we will be creating
            search_opts = {'group_id': context['group_id']}
            volumes = api.cinder.volume_list(self.request,
                                             search_opts=search_opts)
            num_volumes = len(volumes)
            usages = quotas.tenant_quota_usages(
                self.request, targets=('snapshots', 'gigabytes'))

            if (usages['snapshots']['used'] + num_volumes >
                    usages['snapshots']['quota']):
                raise ValueError(_('Unable to create snapshots due to '
                                   'exceeding snapshot quota limit.'))
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
        return {'group_id': self.kwargs["group_id"]}


class CloneGroupView(forms.ModalFormView):
    form_class = vol_group_forms.CloneGroupForm
    page_title = _("Clone Group")
    template_name = 'project/volume_groups/clone_group.html'
    submit_label = _("Clone Group")
    submit_url = "horizon:project:volume_groups:clone_group"
    success_url = reverse_lazy('horizon:project:volume_groups:index')

    def get_context_data(self, **kwargs):
        context = super(CloneGroupView, self).get_context_data(**kwargs)
        context['group_id'] = self.kwargs['group_id']
        args = (self.kwargs['group_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        try:
            # get number of volumes we will be creating
            group_id = context['group_id']

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
        return {'group_id': self.kwargs["group_id"]}


class DetailView(tabs.TabView):
    tab_group_class = vol_group_tabs.GroupsDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ group.name|default:group.id }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        group = self.get_data()
        table = vol_group_tables.GroupsTable(self.request)
        context["group"] = group
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(group)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            group_id = self.kwargs['group_id']
            group = api.cinder.group_get_with_vol_type_names(self.request,
                                                             group_id)
            search_opts = {'group_id': group_id}
            volumes = api.cinder.volume_list(self.request,
                                             search_opts=search_opts)
            group.volume_names = [{'id': vol.id, 'name': vol.name}
                                  for vol in volumes]
            group_snapshots = api.cinder.group_snapshot_list(
                self.request, search_opts=search_opts)
            group.has_snapshots = bool(group_snapshots)
        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve group details.'),
                              redirect=redirect)
        return group

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:volume_groups:index')

    def get_tabs(self, request, *args, **kwargs):
        group = self.get_data()
        return self.tab_group_class(request, group=group, **kwargs)
