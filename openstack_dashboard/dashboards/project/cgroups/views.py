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
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.project.cgroups \
    import forms as vol_cgroup_forms
from openstack_dashboard.dashboards.project.cgroups \
    import tables as vol_cgroup_tables
from openstack_dashboard.dashboards.project.cgroups \
    import tabs as vol_cgroup_tabs
from openstack_dashboard.dashboards.project.cgroups \
    import workflows as vol_cgroup_workflows

CGROUP_INFO_FIELDS = ("name",
                      "description")

INDEX_URL = "horizon:project:cgroups:index"


class CGroupsView(tables.DataTableView):
    table_class = vol_cgroup_tables.VolumeCGroupsTable
    page_title = _("Consistency Groups")

    def get_data(self):
        try:
            cgroups = api.cinder.volume_cgroup_list_with_vol_type_names(
                self.request)

        except Exception:
            cgroups = []
            exceptions.handle(self.request, _("Unable to retrieve "
                                              "volume consistency groups."))
        return cgroups


class CreateView(workflows.WorkflowView):
    workflow_class = vol_cgroup_workflows.CreateCGroupWorkflow
    template_name = 'project/cgroups/create.html'
    page_title = _("Create Volume Consistency Group")


class UpdateView(forms.ModalFormView):
    template_name = 'project/cgroups/update.html'
    page_title = _("Edit Consistency Group")
    form_class = vol_cgroup_forms.UpdateForm
    success_url = reverse_lazy('horizon:project:cgroups:index')
    submit_url = "horizon:project:cgroups:update"

    def get_initial(self):
        cgroup = self.get_object()
        return {'cgroup_id': self.kwargs["cgroup_id"],
                'name': cgroup.name,
                'description': cgroup.description}

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['cgroup_id'] = self.kwargs['cgroup_id']
        args = (self.kwargs['cgroup_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_object(self):
        cgroup_id = self.kwargs['cgroup_id']
        try:
            self._object = cinder.volume_cgroup_get(self.request, cgroup_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve consistency group '
                                'details.'),
                              redirect=reverse(INDEX_URL))
        return self._object


class RemoveVolumesView(forms.ModalFormView):
    template_name = 'project/cgroups/remove_vols.html'
    page_title = _("Remove Volumes from Consistency Group")
    form_class = vol_cgroup_forms.RemoveVolsForm
    success_url = reverse_lazy('horizon:project:cgroups:index')
    submit_url = "horizon:project:cgroups:remove_volumes"

    def get_initial(self):
        cgroup = self.get_object()
        return {'cgroup_id': self.kwargs["cgroup_id"],
                'name': cgroup.name}

    def get_context_data(self, **kwargs):
        context = super(RemoveVolumesView, self).get_context_data(**kwargs)
        context['cgroup_id'] = self.kwargs['cgroup_id']
        args = (self.kwargs['cgroup_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_object(self):
        cgroup_id = self.kwargs['cgroup_id']
        try:
            self._object = cinder.volume_cgroup_get(self.request, cgroup_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve consistency group '
                                'details.'),
                              redirect=reverse(INDEX_URL))
        return self._object


class DeleteView(forms.ModalFormView):
    template_name = 'project/cgroups/delete.html'
    page_title = _("Delete Consistency Group")
    form_class = vol_cgroup_forms.DeleteForm
    success_url = reverse_lazy('horizon:project:cgroups:index')
    submit_url = "horizon:project:cgroups:delete"
    submit_label = page_title

    def get_initial(self):
        cgroup = self.get_object()
        return {'cgroup_id': self.kwargs["cgroup_id"],
                'name': cgroup.name}

    def get_context_data(self, **kwargs):
        context = super(DeleteView, self).get_context_data(**kwargs)
        context['cgroup_id'] = self.kwargs['cgroup_id']
        args = (self.kwargs['cgroup_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_object(self):
        cgroup_id = self.kwargs['cgroup_id']
        try:
            self._object = cinder.volume_cgroup_get(self.request, cgroup_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve consistency group '
                                'details.'),
                              redirect=reverse(INDEX_URL))
        return self._object


class ManageView(workflows.WorkflowView):
    workflow_class = vol_cgroup_workflows.UpdateCGroupWorkflow

    def get_context_data(self, **kwargs):
        context = super(ManageView, self).get_context_data(**kwargs)
        context['cgroup_id'] = self.kwargs["cgroup_id"]
        return context

    def _get_object(self, *args, **kwargs):
        cgroup_id = self.kwargs['cgroup_id']
        try:
            cgroup = cinder.volume_cgroup_get(self.request, cgroup_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve consistency group '
                                'details.'),
                              redirect=reverse(INDEX_URL))
        return cgroup

    def get_initial(self):
        cgroup = self._get_object()
        return {'cgroup_id': cgroup.id,
                'name': cgroup.name,
                'description': cgroup.description,
                'vtypes': getattr(cgroup, "volume_types")}


class CreateSnapshotView(forms.ModalFormView):
    form_class = vol_cgroup_forms.CreateSnapshotForm
    page_title = _("Create Consistency Group Snapshot")
    template_name = 'project/cgroups/create_snapshot.html'
    submit_label = _("Create Snapshot")
    submit_url = "horizon:project:cgroups:create_snapshot"
    success_url = reverse_lazy('horizon:project:cg_snapshots:index')

    def get_context_data(self, **kwargs):
        context = super(CreateSnapshotView, self).get_context_data(**kwargs)
        context['cgroup_id'] = self.kwargs['cgroup_id']
        args = (self.kwargs['cgroup_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        try:
            # get number of snapshots we will be creating
            search_opts = {'consistencygroup_id': context['cgroup_id']}
            volumes = api.cinder.volume_list(self.request,
                                             search_opts=search_opts)
            num_volumes = len(volumes)
            usages = quotas.tenant_limit_usages(self.request)

            if usages['totalSnapshotsUsed'] + num_volumes > \
                    usages['maxTotalSnapshots']:
                raise ValueError(_('Unable to create snapshots due to '
                                   'exceeding snapshot quota limit.'))
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
        return {'cgroup_id': self.kwargs["cgroup_id"]}


class CloneCGroupView(forms.ModalFormView):
    form_class = vol_cgroup_forms.CloneCGroupForm
    page_title = _("Clone Consistency Group")
    template_name = 'project/cgroups/clone_cgroup.html'
    submit_label = _("Clone Consistency Group")
    submit_url = "horizon:project:cgroups:clone_cgroup"
    success_url = reverse_lazy('horizon:project:cgroups:index')

    def get_context_data(self, **kwargs):
        context = super(CloneCGroupView, self).get_context_data(**kwargs)
        context['cgroup_id'] = self.kwargs['cgroup_id']
        args = (self.kwargs['cgroup_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        try:
            # get number of volumes we will be creating
            cgroup_id = context['cgroup_id']

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
        return {'cgroup_id': self.kwargs["cgroup_id"]}


class DetailView(tabs.TabView):
    tab_group_class = vol_cgroup_tabs.CGroupsDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ cgroup.name|default:cgroup.id }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        cgroup = self.get_data()
        table = vol_cgroup_tables.VolumeCGroupsTable(self.request)
        context["cgroup"] = cgroup
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(cgroup)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            cgroup_id = self.kwargs['cgroup_id']
            cgroup = api.cinder.volume_cgroup_get(self.request,
                                                  cgroup_id)
            cgroup.volume_type_names = []
            for vol_type_id in cgroup.volume_types:
                vol_type = api.cinder.volume_type_get(self.request,
                                                      vol_type_id)
                cgroup.volume_type_names.append(vol_type.name)

            cgroup.volume_names = []
            search_opts = {'consistencygroup_id': cgroup_id}
            volumes = api.cinder.volume_list(self.request,
                                             search_opts=search_opts)
            for volume in volumes:
                cgroup.volume_names.append(volume.name)

        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve consistency group '
                                'details.'),
                              redirect=redirect)
        return cgroup

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:cgroups:index')

    def get_tabs(self, request, *args, **kwargs):
        cgroup = self.get_data()
        return self.tab_group_class(request, cgroup=cgroup, **kwargs)
