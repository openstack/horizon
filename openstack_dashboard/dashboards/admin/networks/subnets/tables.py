# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class DeleteSubnet(tables.DeleteAction):
    data_type_singular = _("Subnet")
    data_type_plural = _("Subnets")

    def delete(self, request, obj_id):
        try:
            api.neutron.subnet_delete(request, obj_id)
        except Exception:
            msg = _('Failed to delete subnet %s') % obj_id
            LOG.info(msg)
            network_id = self.table.kwargs['network_id']
            redirect = reverse('horizon:admin:networks:detail',
                               args=[network_id])
            exceptions.handle(request, msg, redirect=redirect)


class CreateSubnet(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Subnet")
    url = "horizon:admin:networks:addsubnet"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum=None):
        network_id = self.table.kwargs['network_id']
        return reverse(self.url, args=(network_id,))


class UpdateSubnet(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Subnet")
    url = "horizon:admin:networks:editsubnet"
    classes = ("ajax-modal", "btn-edit")

    def get_link_url(self, subnet):
        network_id = self.table.kwargs['network_id']
        return reverse(self.url, args=(network_id, subnet.id))


class SubnetsTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Name"),
                         link='horizon:admin:networks:subnets:detail')
    cidr = tables.Column("cidr", verbose_name=_("CIDR"))
    ip_version = tables.Column("ipver_str", verbose_name=_("IP Version"))
    gateway_ip = tables.Column("gateway_ip", verbose_name=_("Gateway IP"))

    def get_object_display(self, subnet):
        return subnet.id

    class Meta:
        name = "subnets"
        verbose_name = _("Subnets")
        table_actions = (CreateSubnet, DeleteSubnet)
        row_actions = (UpdateSubnet, DeleteSubnet,)
