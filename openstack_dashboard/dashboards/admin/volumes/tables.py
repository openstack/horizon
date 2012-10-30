from django.utils.translation import ugettext_lazy as _

from horizon import tables
from openstack_dashboard.api import cinder
from openstack_dashboard.dashboards.project.volumes.tables import (UpdateRow,
        VolumesTable as _VolumesTable, DeleteVolume)


class CreateVolumeType(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Volume Type")
    url = "horizon:admin:volumes:create_type"
    classes = ("ajax-modal", "btn-create")


class DeleteVolumeType(tables.DeleteAction):
    data_type_singular = _("Volume Type")
    data_type_plural = _("Volume Types")

    def delete(self, request, obj_id):
        cinder.volume_type_delete(request, obj_id)


class VolumesTable(_VolumesTable):
    name = tables.Column("display_name",
                         verbose_name=_("Name"),
                         link="horizon:admin:volumes:detail")
    host = tables.Column("os-vol-host-attr:host", verbose_name=_("Host"))
    tenant = tables.Column("tenant_name", verbose_name=_("Project"))

    class Meta:
        name = "volumes"
        verbose_name = _("Volumes")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (DeleteVolume,)
        row_actions = (DeleteVolume,)
        columns = ('tenant', 'host', 'name', 'size', 'status', 'volume_type',
                   'attachments',)


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
        row_actions = (DeleteVolumeType,)
