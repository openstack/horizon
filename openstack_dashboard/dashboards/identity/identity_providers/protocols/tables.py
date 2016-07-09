# Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from openstack_dashboard import api
from openstack_dashboard import policy


class AddProtocol(policy.PolicyTargetMixin, tables.LinkAction):
    name = "create"
    verbose_name = _("Add Protocol")
    url = "horizon:identity:identity_providers:protocols:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("identity", "identity:create_protocol"),)

    def get_link_url(self, datum=None):
        idp_id = self.table.kwargs['identity_provider_id']
        return reverse(self.url, args=(idp_id,))


class RemoveProtocol(policy.PolicyTargetMixin, tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Protocol",
            u"Delete Protocols",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Protocol",
            u"Deleted Protocols",
            count
        )

    policy_rules = (("identity", "identity:delete_protocol"),)

    def delete(self, request, obj_id):
        identity_provider = self.table.kwargs['identity_provider_id']
        protocol = obj_id
        api.keystone.protocol_delete(request, identity_provider, protocol)


class ProtocolsTable(tables.DataTable):
    protocol = tables.Column("id",
                             verbose_name=_("Protocol ID"))
    mapping = tables.Column("mapping_id",
                            verbose_name=_("Mapping ID"))

    def get_object_display(self, datum):
        return datum.id

    class Meta(object):
        name = "idp_protocols"
        verbose_name = _("Protocols")
        table_actions = (AddProtocol, RemoveProtocol)
        row_actions = (RemoveProtocol, )
