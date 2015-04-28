# Copyright 2015, Thales Services SAS
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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from openstack_dashboard.api import neutron as api
from openstack_dashboard import policy

from horizon import tables


class AddRouterRoute(policy.PolicyTargetMixin, tables.LinkAction):
    name = "create"
    verbose_name = _("Add Static Route")
    url = "horizon:project:routers:addrouterroute"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "update_router"),)

    def get_link_url(self, datum=None):
        router_id = self.table.kwargs['router_id']
        return reverse(self.url, args=(router_id,))


class RemoveRouterRoute(policy.PolicyTargetMixin, tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Static Route",
            u"Delete Static Routes",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Static Route",
            u"Deleted Static Routes",
            count
        )
    failure_url = 'horizon:project:routers:detail'
    policy_rules = (("network", "update_router"),)

    def delete(self, request, obj_id):
        router_id = self.table.kwargs['router_id']
        api.router_static_route_remove(request, router_id, [obj_id])


class ExtraRoutesTable(tables.DataTable):
    destination = tables.Column("destination",
                                verbose_name=_("Destination CIDR"))
    nexthop = tables.Column("nexthop", verbose_name=_("Next Hop"))

    def get_object_display(self, datum):
        """Display ExtraRoutes when deleted."""
        return (super(ExtraRoutesTable, self).get_object_display(datum)
                or datum.destination + " -> " + datum.nexthop)

    class Meta(object):
        name = "extra_routes"
        verbose_name = _("Static Routes")
        table_actions = (AddRouterRoute, RemoveRouterRoute)
        row_actions = (RemoveRouterRoute, )
