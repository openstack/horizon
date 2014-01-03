# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
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

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.ports \
    import tables as project_tables

LOG = logging.getLogger(__name__)


def get_device_owner(port):
    if port['device_owner'] == 'network:router_gateway':
        return _('External Gateway')
    elif port['device_owner'] == 'network:router_interface':
        return _('Internal Interface')
    else:
        return ' '


class AddInterface(tables.LinkAction):
    name = "create"
    verbose_name = _("Add Interface")
    url = "horizon:project:routers:addinterface"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum=None):
        router_id = self.table.kwargs['router_id']
        return reverse(self.url, args=(router_id,))


class RemoveInterface(tables.DeleteAction):
    data_type_singular = _("Interface")
    data_type_plural = _("Interfaces")
    failure_url = 'horizon:project:routers:detail'

    def delete(self, request, obj_id):
        try:
            router_id = self.table.kwargs['router_id']
            port = api.neutron.port_get(request, obj_id)
            if port['device_owner'] == 'network:router_gateway':
                api.neutron.router_remove_gateway(request, router_id)
            else:
                api.neutron.router_remove_interface(request,
                                                    router_id,
                                                    port_id=obj_id)
        except Exception:
            msg = _('Failed to delete interface %s') % obj_id
            LOG.info(msg)
            router_id = self.table.kwargs['router_id']
            redirect = reverse(self.failure_url,
                               args=[router_id])
            exceptions.handle(request, msg, redirect=redirect)

    def allowed(self, request, datum=None):
        if datum and datum['device_owner'] == 'network:router_gateway':
            return False
        return True


class PortsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:networks:ports:detail")
    fixed_ips = tables.Column(project_tables.get_fixed_ips,
                              verbose_name=_("Fixed IPs"))
    status = tables.Column("status", verbose_name=_("Status"))
    device_owner = tables.Column(get_device_owner,
                                 verbose_name=_("Type"))
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"))

    def get_object_display(self, port):
        return port.id

    class Meta:
        name = "interfaces"
        verbose_name = _("Interfaces")
        table_actions = (AddInterface, RemoveInterface)
        row_actions = (RemoveInterface, )
