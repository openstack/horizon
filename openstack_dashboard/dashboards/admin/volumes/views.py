# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
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

"""
Admin views for managing volumes.
"""

from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone

from openstack_dashboard.dashboards.admin.volumes \
    import forms as project_forms
from openstack_dashboard.dashboards.admin.volumes \
    import tables as project_tables

from openstack_dashboard.dashboards.project.volumes \
    import tabs as project_tabs
from openstack_dashboard.dashboards.project.volumes \
    .volumes import views as volume_views


class IndexView(tables.MultiTableView, project_tabs.VolumeTableMixIn):
    table_classes = (project_tables.VolumesTable,
                     project_tables.VolumeTypesTable)
    template_name = "admin/volumes/index.html"

    def get_volumes_data(self):
        volumes = self._get_volumes(search_opts={'all_tenants': True})
        instances = self._get_instances(search_opts={'all_tenants': True})
        self._set_attachments_string(volumes, instances)

        # Gather our tenants to correlate against IDs
        try:
            tenants, has_more = keystone.tenant_list(self.request)
        except Exception:
            tenants = []
            msg = _('Unable to retrieve volume project information.')
            exceptions.handle(self.request, msg)

        tenant_dict = SortedDict([(t.id, t) for t in tenants])
        for volume in volumes:
            tenant_id = getattr(volume, "os-vol-tenant-attr:tenant_id", None)
            tenant = tenant_dict.get(tenant_id, None)
            volume.tenant_name = getattr(tenant, "name", None)

        return volumes

    def get_volume_types_data(self):
        try:
            volume_types = cinder.volume_type_list(self.request)
        except Exception:
            volume_types = []
            exceptions.handle(self.request,
                              _("Unable to retrieve volume types"))
        return volume_types


class DetailView(volume_views.DetailView):
    template_name = "admin/volumes/detail.html"


class CreateVolumeTypeView(forms.ModalFormView):
    form_class = project_forms.CreateVolumeType
    template_name = 'admin/volumes/create_volume_type.html'
    success_url = 'horizon:admin:volumes:index'

    def get_success_url(self):
        return reverse(self.success_url)
