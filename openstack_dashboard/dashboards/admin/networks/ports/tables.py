# Copyright 2012 NEC Corporation
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

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.ports import \
    tables as project_tables
from openstack_dashboard.dashboards.project.networks.ports.tabs \
    import PortsTab as project_port_tab


class DeletePort(project_tables.DeletePort):
    failure_url = "horizon:admin:networks:detail"


class CreatePort(project_tables.CreatePort):
    url = "horizon:admin:networks:addport"

    def allowed(self, request, datum=None):
        return True


class UpdatePort(project_tables.UpdatePort):
    url = "horizon:admin:networks:editport"


class PortsTable(project_tables.PortsTable):
    name = tables.WrappingColumn("name_or_id",
                                 verbose_name=_("Name"),
                                 link="horizon:admin:networks:ports:detail")
    failure_url = reverse_lazy('horizon:admin:networks:index')

    @memoized.memoized_method
    def _get_network(self):
        try:
            network_id = self.kwargs['network_id']
            network = api.neutron.network_get(self.request, network_id)
            network.set_id_as_name_if_empty(length=0)
        except Exception:
            msg = _('Unable to retrieve details for network "%s".') \
                % (network_id)
            exceptions.handle(self.request, msg, redirect=self.failure_url)
        return network

    class Meta(object):
        name = "ports"
        verbose_name = _("Ports")
        table_actions = (CreatePort, DeletePort, tables.FilterAction)
        row_actions = (UpdatePort, DeletePort,)
        hidden_title = False


class PortsTab(project_port_tab):
    table_classes = (PortsTable,)
