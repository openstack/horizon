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
from openstack_dashboard.dashboards.project.routers.ports \
    import tables as routers_tables


class PortsTable(routers_tables.PortsTable):
    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link="horizon:admin:networks:ports:detail")

    class Meta(object):
        name = "interfaces"
        verbose_name = _("Interfaces")
        table_actions = (routers_tables.AddInterface,
                         routers_tables.RemoveInterface)
        row_actions = (routers_tables.RemoveInterface,)
