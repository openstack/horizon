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
from django.template.defaultfilters import title
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tables
from openstack_dashboard import api
from quantumclient.common import exceptions as q_ext

LOG = logging.getLogger(__name__)


class DeleteRouter(tables.DeleteAction):
    data_type_singular = _("Router")
    data_type_plural = _("Routers")
    redirect_url = "horizon:project:routers:index"

    def delete(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        name = self.table.get_object_display(obj)
        try:
            api.router_delete(request, obj_id)
        except q_ext.QuantumClientException as e:
            msg = _('Unable to delete router "%s"') % e.message
            LOG.info(msg)
            messages.error(request, msg)
            redirect = reverse(self.redirect_url)
            raise exceptions.Http302(redirect, message=msg)
        except Exception as e:
            msg = _('Unable to delete router "%s"') % name
            LOG.info(msg)
            exceptions.handle(request, msg)

    def allowed(self, request, router=None):
        return True


class CreateRouter(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Router")
    url = "horizon:project:routers:create"
    classes = ("ajax-modal", "btn-create")


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, router_id):
        router = api.router_get(request, router_id)
        return router


class RoutersTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:routers:detail")
    status = tables.Column("status",
                           filters=(title,),
                           verbose_name=_("Status"),
                           status=True)

    def get_object_display(self, obj):
        return obj.name

    class Meta:
        name = "Routers"
        verbose_name = _("Routers")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (CreateRouter, DeleteRouter)
        row_actions = (DeleteRouter, )
