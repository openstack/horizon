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

from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from openstack_dashboard.dashboards.project.volumes.views import \
        VolumeTableMixIn, DetailView as _DetailView
from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone

from .tables import VolumesTable, VolumeTypesTable
from .forms import CreateVolumeType
from horizon import exceptions
from horizon import forms
from horizon import tables


class IndexView(tables.MultiTableView, VolumeTableMixIn):
    table_classes = (VolumesTable, VolumeTypesTable)
    template_name = "admin/volumes/index.html"

    def get_volumes_data(self):
        volumes = self._get_volumes(search_opts={'all_tenants': 1})
        instances = self._get_instances()
        self._set_id_if_nameless(volumes, instances)
        self._set_attachments_string(volumes, instances)

        # Gather our tenants to correlate against IDs
        try:
            tenants = keystone.tenant_list(self.request, admin=True)
        except:
            tenants = []
            msg = _('Unable to retrieve volume tenant information.')
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
        except:
            volume_types = []
            exceptions.handle(self.request,
                              _("Unable to retrieve volume types"))
        return volume_types


class DetailView(_DetailView):
    template_name = "admin/volumes/detail.html"


class CreateVolumeTypeView(forms.ModalFormView):
    form_class = CreateVolumeType
    template_name = 'admin/volumes/create_volume_type.html'
    success_url = 'horizon:admin:volumes:index'

    def get_success_url(self):
        return reverse(self.success_url)
