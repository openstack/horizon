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

from django.utils.translation import ugettext_lazy as _

from horizon import tables
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.routers import tables as r_tables


class DeleteRouter(r_tables.DeleteRouter):
    redirect_url = "horizon:admin:routers:index"


class EditRouter(r_tables.EditRouter):
    url = "horizon:admin:routers:update"


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, router_id):
        router = api.neutron.router_get(request, router_id)
        return router


class RoutersTable(r_tables.RoutersTable):
    tenant = tables.Column("tenant_name", verbose_name=_("Project"))
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:admin:routers:detail")

    class Meta(object):
        name = "Routers"
        verbose_name = _("Routers")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (DeleteRouter, r_tables.RoutersFilterAction)
        row_actions = (EditRouter, DeleteRouter,)
        Columns = ('tenant', 'name', 'status', 'distributed', 'ext_net')
