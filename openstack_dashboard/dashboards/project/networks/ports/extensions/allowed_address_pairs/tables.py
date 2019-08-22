# Copyright 2015, Alcatel-Lucent USA Inc.
# All Rights Reserved.
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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy


LOG = logging.getLogger(__name__)


class AddAllowedAddressPair(policy.PolicyTargetMixin, tables.LinkAction):
    name = "AddAllowedAddressPair"
    verbose_name = _("Add Allowed Address Pair")
    url = "horizon:project:networks:ports:addallowedaddresspairs"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (
        ("network", "update_port"),
        ("network", "update_port:allowed_address_pairs"),
    )

    def get_policy_target(self, request, datum=None):
        policy_target = super(AddAllowedAddressPair, self).\
            get_policy_target(request, datum)
        policy_target["network:tenant_id"] = (
            self.table.kwargs['port'].tenant_id)

        return policy_target

    def get_link_url(self, port=None):
        if port:
            return reverse(self.url, args=(port.id,))
        else:
            return reverse(self.url, args=(self.table.kwargs.get('port_id'),))


class DeleteAllowedAddressPair(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete",
            u"Delete",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted address pair",
            u"Deleted address pairs",
            count
        )

    policy_rules = (
        ("network", "update_port"),
        ("network", "update_port:allowed_address_pairs"),
    )

    def get_policy_target(self, request, datum=None):
        policy_target = super(DeleteAllowedAddressPair, self).\
            get_policy_target(request, datum)
        policy_target["network:tenant_id"] = (
            self.table.kwargs['port'].tenant_id)

        return policy_target

    def delete(self, request, ip_address):
        try:
            port_id = self.table.kwargs['port_id']
            port = api.neutron.port_get(request, port_id)
            pairs = port.get('allowed_address_pairs', [])
            pairs = [pair for pair in pairs
                     if pair['ip_address'] != ip_address]
            pairs = [pair.to_dict() for pair in pairs]
            api.neutron.port_update(request, port_id,
                                    allowed_address_pairs=pairs)
        except Exception as e:
            LOG.error('Failed to update port %(port_id)s: %(reason)s',
                      {'port_id': port_id, 'reason': e})
            # NOTE: No exception handling is required here because
            # BatchAction.handle() does it. What we need to do is
            # just to re-raise the exception.
            raise


class AllowedAddressPairsTable(tables.DataTable):
    IP = tables.Column("ip_address",
                       verbose_name=_("IP Address or CIDR"))
    mac = tables.Column('mac_address', verbose_name=_("MAC Address"))

    def get_object_display(self, address_pair):
        return address_pair['ip_address']

    class Meta(object):
        name = "allowed_address_pairs"
        verbose_name = _("Allowed Address Pairs")
        row_actions = (DeleteAllowedAddressPair,)
        table_actions = (AddAllowedAddressPair, DeleteAllowedAddressPair)
