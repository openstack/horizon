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

from django.utils.translation import ugettext_lazy as _

from horizon import tables
from openstack_dashboard.api import cinder


class CreateVolumeType(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Volume Type")
    url = "horizon:admin:volumes:volume_types:create_type"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("volume", "volume_extension:types_manage"),)


class ViewVolumeTypeExtras(tables.LinkAction):
    name = "extras"
    verbose_name = _("View Extra Specs")
    url = "horizon:admin:volumes:volume_types:extras:index"
    classes = ("btn-edit",)
    policy_rules = (("volume", "volume_extension:types_manage"),)


class DeleteVolumeType(tables.DeleteAction):
    data_type_singular = _("Volume Type")
    data_type_plural = _("Volume Types")
    policy_rules = (("volume", "volume_extension:types_manage"),)

    def delete(self, request, obj_id):
        cinder.volume_type_delete(request, obj_id)


class VolumeTypesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"))

    def get_object_display(self, vol_type):
        return vol_type.name

    def get_object_id(self, vol_type):
        return str(vol_type.id)

    class Meta:
        name = "volume_types"
        verbose_name = _("Volume Types")
        table_actions = (CreateVolumeType, DeleteVolumeType,)
        row_actions = (ViewVolumeTypeExtras, DeleteVolumeType,)
