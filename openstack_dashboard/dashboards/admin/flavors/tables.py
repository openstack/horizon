import logging

from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class DeleteFlavor(tables.DeleteAction):
    data_type_singular = _("Flavor")
    data_type_plural = _("Flavors")

    def delete(self, request, obj_id):
        api.nova.flavor_delete(request, obj_id)


class CreateFlavor(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Flavor")
    url = "horizon:admin:flavors:create"
    classes = ("ajax-modal", "btn-create")


class EditFlavor(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Flavor")
    url = "horizon:admin:flavors:edit"
    classes = ("ajax-modal", "btn-edit")


class ViewFlavorExtras(tables.LinkAction):
    name = "extras"
    verbose_name = _("View Extra Specs")
    url = "horizon:admin:flavors:extras:index"
    classes = ("btn-edit",)


def get_size(flavor):
    return _("%sMB") % flavor.ram


def get_swap_size(flavor):
    return _("%sMB") % (flavor.swap or 0)


class FlavorsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Flavor Name'))
    vcpus = tables.Column('vcpus', verbose_name=_('VCPUs'))
    ram = tables.Column(get_size,
                        verbose_name=_('RAM'),
                        attrs={'data-type': 'size'})
    disk = tables.Column('disk', verbose_name=_('Root Disk'))
    ephemeral = tables.Column('OS-FLV-EXT-DATA:ephemeral',
                              verbose_name=_('Ephemeral Disk'))
    swap = tables.Column(get_swap_size,
                         verbose_name=_('Swap Disk'),
                         attrs={'data-type': 'size'})
    flavor_id = tables.Column('id', verbose_name=('ID'))

    class Meta:
        name = "flavors"
        verbose_name = _("Flavors")
        table_actions = (CreateFlavor, DeleteFlavor)
        row_actions = (EditFlavor, ViewFlavorExtras, DeleteFlavor)
