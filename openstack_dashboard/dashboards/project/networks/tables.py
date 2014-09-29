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
from django import template
from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy

LOG = logging.getLogger(__name__)


class CheckNetworkEditable(object):
    """Mixin class to determine the specified network is editable."""

    def allowed(self, request, datum=None):
        # Only administrator is allowed to create and manage shared networks.
        if datum and datum.shared:
            return False
        return True


class DeleteNetwork(policy.PolicyTargetMixin, CheckNetworkEditable,
                    tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Network",
            u"Delete Networks",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Network",
            u"Deleted Networks",
            count
        )

    policy_rules = (("network", "delete_network"),)

    def delete(self, request, network_id):
        try:
            # Retrieve existing subnets belonging to the network.
            subnets = api.neutron.subnet_list(request, network_id=network_id)
            LOG.debug('Network %s has subnets: %s' %
                      (network_id, [s.id for s in subnets]))
            for s in subnets:
                api.neutron.subnet_delete(request, s.id)
                LOG.debug('Deleted subnet %s' % s.id)

            api.neutron.network_delete(request, network_id)
            LOG.debug('Deleted network %s successfully' % network_id)
        except Exception:
            msg = _('Failed to delete network %s') % network_id
            LOG.info(msg)
            redirect = reverse("horizon:project:networks:index")
            exceptions.handle(request, msg, redirect=redirect)


class CreateNetwork(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Network")
    url = "horizon:project:networks:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_network"),)


class EditNetwork(policy.PolicyTargetMixin, CheckNetworkEditable,
                  tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Network")
    url = "horizon:project:networks:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("network", "update_network"),)


class CreateSubnet(policy.PolicyTargetMixin, CheckNetworkEditable,
                   tables.LinkAction):
    name = "subnet"
    verbose_name = _("Add Subnet")
    url = "horizon:project:networks:addsubnet"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_subnet"),)
    policy_target_attrs = (("network:project_id", "tenant_id"),)


def get_subnets(network):
    template_name = 'project/networks/_network_ips.html'
    context = {"subnets": network.subnets}
    return template.loader.render_to_string(template_name, context)


class NetworksTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link='horizon:project:networks:detail')
    subnets = tables.Column(get_subnets,
                            verbose_name=_("Subnets Associated"),)
    shared = tables.Column("shared", verbose_name=_("Shared"),
                           filters=(filters.yesno, filters.capfirst))
    status = tables.Column("status", verbose_name=_("Status"))
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"))

    class Meta:
        name = "networks"
        verbose_name = _("Networks")
        table_actions = (CreateNetwork, DeleteNetwork)
        row_actions = (EditNetwork, CreateSubnet, DeleteNetwork)
