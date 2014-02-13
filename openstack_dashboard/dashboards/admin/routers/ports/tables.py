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

from django.utils.translation import ugettext_lazy as _

from horizon import tables
from openstack_dashboard.dashboards.project.networks.ports \
    import tables as networks_tables
from openstack_dashboard.dashboards.project.routers.ports \
    import tables as routers_tables


class PortsTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:admin:networks:ports:detail")
    fixed_ips = tables.Column(networks_tables.get_fixed_ips,
                              verbose_name=_("Fixed IPs"))
    status = tables.Column("status", verbose_name=_("Status"))
    device_owner = tables.Column(routers_tables.get_device_owner,
                                 verbose_name=_("Type"))
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"))

    def get_object_display(self, port):
        return port.id

    class Meta:
        name = "interfaces"
        verbose_name = _("Interfaces")
