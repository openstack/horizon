import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class RenameNetworkLink(tables.LinkAction):
    name = "rename_network"
    verbose_name = _("Rename Network")
    url = "horizon:nova:networks:rename"
    attrs = {"class": "ajax-modal"}


class CreateNetworkLink(tables.LinkAction):
    name = "create_network"
    verbose_name = _("Create New Network")
    url = "horizon:nova:networks:create"
    classes = ("ajax-modal",)


class DeleteNetworkAction(tables.DeleteAction):
    data_type_singular = _("Network")
    data_type_plural = _("Networks")

    def delete(self, request, obj_id):
        api.quantum_delete_network(request, obj_id)


class NetworksTable(tables.DataTable):
    id = tables.Column('id', verbose_name=_('Network Id'),
                       link="horizon:nova:networks:detail")
    name = tables.Column('name', verbose_name=_('Name'))
    used = tables.Column('used', verbose_name=_('Used'))
    available = tables.Column('available', verbose_name=_('Available'))
    total = tables.Column('total', verbose_name=_('Total'))
    #tenant = tables.Column('tenant', verbose_name=_('Project'))

    def get_object_id(self, datum):
        return datum['id']

    def get_object_display(self, obj):
        return obj['name']

    class Meta:
        name = "networks"
        verbose_name = _("Networks")
        row_actions = (DeleteNetworkAction, RenameNetworkLink,)
        table_actions = (CreateNetworkLink, DeleteNetworkAction,)


class CreatePortLink(tables.LinkAction):
    name = "create_port"
    verbose_name = _("Create Ports")
    url = "horizon:nova:networks:port_create"
    classes = ("ajax-modal",)

    def get_link_url(self, datum=None):
        network_id = self.table.kwargs['network_id']
        return reverse(self.url, args=(network_id,))


class DeletePortAction(tables.DeleteAction):
    data_type_singular = _("Port")
    data_type_plural = _("Ports")

    def delete(self, request, obj_id):
        api.quantum_delete_port(request,
                                self.table.kwargs['network_id'],
                                obj_id)


class DetachPortAction(tables.BatchAction):
    name = "detach_port"
    action_present = _("Detach")
    action_past = _("Detached")
    data_type_singular = _("Port")
    data_type_plural = _("Ports")

    def action(self, request, datum_id):
        body = {'port': {'state': 'DOWN'}}
        api.quantum_set_port_state(request,
                                   self.table.kwargs['network_id'],
                                   datum_id, body)


class AttachPortAction(tables.LinkAction):
    name = "attach_port"
    verbose_name = _("Attach Port")
    url = "horizon:nova:networks:port_attach"
    attrs = {"class": "ajax-modal"}

    def get_link_url(self, datum=None):
        network_id = self.table.kwargs['network_id']
        return reverse(self.url, args=(network_id, datum['id']))


class NetworkDetailsTable(tables.DataTable):
    id = tables.Column('id', verbose_name=_('Port Id'))
    state = tables.Column('state', verbose_name=_('State'))
    attachment = tables.Column('attachment', verbose_name=_('Attachment'))

    def get_object_id(self, datum):
        return datum['id']

    def get_object_display(self, obj):
        return obj['id']

    class Meta:
        name = "network_details"
        verbose_name = _("Network Port Details")
        row_actions = (DeletePortAction, AttachPortAction, DetachPortAction)
        table_actions = (CreatePortLink, DeletePortAction,)
