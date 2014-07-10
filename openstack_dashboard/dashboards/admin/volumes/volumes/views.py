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
from openstack_dashboard.dashboards.project.volumes.volumes \
    import views as volumes_views


class DetailView(volumes_views.DetailView):
    template_name = "admin/volumes/volumes/detail.html"

    def get_redirect_url(self):
        return reverse('horizon:admin:volumes:index')


class CreateVolumeTypeView(forms.ModalFormView):
    form_class = volumes_forms.CreateVolumeType
    template_name = 'admin/volumes/volumes/create_volume_type.html'
    success_url = 'horizon:admin:volumes:volumes_tab'

    def get_success_url(self):
        return reverse(self.success_url)


class UpdateStatusView(forms.ModalFormView):
    form_class = volumes_forms.UpdateStatus
    template_name = 'admin/volumes/volumes/update_status.html'
    success_url = reverse_lazy('horizon:admin:volumes:index')

    def get_context_data(self, **kwargs):
        context = super(UpdateStatusView, self).get_context_data(**kwargs)
        context["volume_id"] = self.kwargs['volume_id']
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
