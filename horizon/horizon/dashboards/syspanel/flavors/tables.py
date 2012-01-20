import logging

from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class DeleteFlavor(tables.DeleteAction):
    data_type_singular = "Flavor"
    data_type_plural = "Flavors"

    def delete(self, request, obj_id):
        api.flavor_delete(request, obj_id, False)


class CreateFlavor(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Flavor")
    url = "horizon:syspanel:flavors:create"
    attrs = {"class": "btn small ajax-modal"}


class FlavorsTable(tables.DataTable):
    flavor_id = tables.Column('id', verbose_name=('ID'))
    name = tables.Column('name', verbose_name=_('Flavor Name'))
    vcpus = tables.Column('vcpus', verbose_name=_('VCPUs'))
    ram = tables.Column('ram', verbose_name=_('Memory'))
    disk = tables.Column('disk', verbose_name=_('Disk'))

    class Meta:
        name = "flavors"
        verbose_name = _("Flavors")
        table_actions = (CreateFlavor, DeleteFlavor)
        row_actions = (DeleteFlavor, )
