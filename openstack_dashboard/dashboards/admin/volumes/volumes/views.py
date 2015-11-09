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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized

from openstack_dashboard.api import cinder
from openstack_dashboard.dashboards.admin.volumes.volumes \
    import forms as volumes_forms
from openstack_dashboard.dashboards.admin.volumes.volumes \
    import tables as volumes_tables
from openstack_dashboard.dashboards.project.volumes.volumes \
    import views as volumes_views


class DetailView(volumes_views.DetailView):
    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        table = volumes_tables.VolumesTable(self.request)
        context["actions"] = table.render_row_actions(context["volume"])
        return context

    def get_redirect_url(self):
        return reverse('horizon:admin:volumes:index')


class ManageVolumeView(forms.ModalFormView):
    form_class = volumes_forms.ManageVolume
    template_name = 'admin/volumes/volumes/manage_volume.html'
    modal_header = _("Manage Volume")
    form_id = "manage_volume_modal"
    submit_label = _("Manage")
    success_url = reverse_lazy('horizon:admin:volumes:volumes_tab')
    submit_url = reverse_lazy('horizon:admin:volumes:volumes:manage')
    cancel_url = reverse_lazy("horizon:admin:volumes:index")
    page_title = _("Manage a Volume")

    def get_context_data(self, **kwargs):
        context = super(ManageVolumeView, self).get_context_data(**kwargs)
        return context


class UnmanageVolumeView(forms.ModalFormView):
    form_class = volumes_forms.UnmanageVolume
    template_name = 'admin/volumes/volumes/unmanage_volume.html'
    modal_header = _("Confirm Unmanage Volume")
    form_id = "unmanage_volume_modal"
    submit_label = _("Unmanage")
    success_url = reverse_lazy('horizon:admin:volumes:volumes_tab')
    submit_url = 'horizon:admin:volumes:volumes:unmanage'
    cancel_url = reverse_lazy("horizon:admin:volumes:index")
    page_title = _("Unmanage a Volume")

    def get_context_data(self, **kwargs):
        context = super(UnmanageVolumeView, self).get_context_data(**kwargs)
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            volume_id = self.kwargs['volume_id']
            volume = cinder.volume_get(self.request, volume_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume details.'),
                              redirect=self.success_url)
        return volume

    def get_initial(self):
        volume = self.get_data()
        return {'volume_id': self.kwargs["volume_id"],
                'name': volume.name,
                'host': getattr(volume, "os-vol-host-attr:host")}


class MigrateVolumeView(forms.ModalFormView):
    form_class = volumes_forms.MigrateVolume
    template_name = 'admin/volumes/volumes/migrate_volume.html'
    modal_header = _("Migrate Volume")
    form_id = "migrate_volume_modal"
    submit_label = _("Migrate")
    success_url = reverse_lazy('horizon:admin:volumes:volumes_tab')
    submit_url = 'horizon:admin:volumes:volumes:migrate'
    cancel_url = reverse_lazy("horizon:admin:volumes:index")
    page_title = _("Migrate Volume")

    def get_context_data(self, **kwargs):
        context = super(MigrateVolumeView, self).get_context_data(**kwargs)
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            volume_id = self.kwargs['volume_id']
            volume = cinder.volume_get(self.request, volume_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume details.'),
                              redirect=self.success_url)
        return volume

    @memoized.memoized_method
    def get_hosts(self):
        try:
            return cinder.pool_list(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve pools information.'),
                              redirect=self.success_url)

    def get_initial(self):
        volume = self.get_data()
        return {'volume_id': self.kwargs["volume_id"],
                'name': volume.name,
                'current_host': getattr(volume, "os-vol-host-attr:host"),
                'hosts': self.get_hosts()}


class UpdateStatusView(forms.ModalFormView):
    form_class = volumes_forms.UpdateStatus
    modal_header = _("Update Volume Status")
    modal_id = "update_volume_status_modal"
    template_name = 'admin/volumes/volumes/update_status.html'
    submit_label = _("Update Status")
    submit_url = "horizon:admin:volumes:volumes:update_status"
    success_url = reverse_lazy('horizon:admin:volumes:index')
    page_title = _("Update Volume Status")

    def get_context_data(self, **kwargs):
        context = super(UpdateStatusView, self).get_context_data(**kwargs)
        context["volume_id"] = self.kwargs['volume_id']
        args = (self.kwargs['volume_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            volume_id = self.kwargs['volume_id']
            volume = cinder.volume_get(self.request, volume_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volume details.'),
                              redirect=self.success_url)
        return volume

    def get_initial(self):
        volume = self.get_data()
        return {'volume_id': self.kwargs["volume_id"],
                'status': volume.status}
