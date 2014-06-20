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

from horizon import forms

from openstack_dashboard.dashboards.admin.volumes.volumes \
    import forms as volumes_forms
from openstack_dashboard.dashboards.project.volumes.volumes \
    import views as volumes_views


class DetailView(volumes_views.DetailView):
    template_name = "admin/volumes/volumes/detail.html"


class CreateVolumeTypeView(forms.ModalFormView):
    form_class = volumes_forms.CreateVolumeType
    template_name = 'admin/volumes/volumes/create_volume_type.html'
    success_url = 'horizon:admin:volumes:volumes_tab'

    def get_success_url(self):
        return reverse(self.success_url)
