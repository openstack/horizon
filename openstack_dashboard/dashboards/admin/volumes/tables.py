from django.utils.translation import ugettext_lazy as _

from horizon import tables
from openstack_dashboard.dashboards.project.volumes.tables import (UpdateRow,
        VolumesTable as _VolumesTable, DeleteVolume)


class VolumesTable(_VolumesTable):
    name = tables.Column("display_name",
                         verbose_name=_("Name"),
                         link="horizon:admin:volumes:detail")

    class Meta:
        name = "volumes"
        verbose_name = _("Volumes")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (DeleteVolume,)
        row_actions = (DeleteVolume,)
