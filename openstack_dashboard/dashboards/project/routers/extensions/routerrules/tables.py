# Copyright 2013,  Big Switch Networks, Inc
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
from django.utils.translation import ungettext_lazy

from openstack_dashboard.dashboards.project.routers.extensions.routerrules\
    import rulemanager
from openstack_dashboard import policy

from horizon import tables

LOG = logging.getLogger(__name__)


class AddRouterRule(policy.PolicyTargetMixin, tables.LinkAction):
    name = "create"
    verbose_name = _("Add Router Rule")
    url = "horizon:project:routers:addrouterrule"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "update_router"),)

    def get_link_url(self, datum=None):
        router_id = self.table.kwargs['router_id']
        return reverse(self.url, args=(router_id,))


class RemoveRouterRule(policy.PolicyTargetMixin, tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Router Rule",
            u"Delete Router Rules",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Router Rule",
            u"Deleted Router Rules",
            count
        )

    failure_url = 'horizon:project:routers:detail'
    policy_rules = (("network", "update_router"),)

    def delete(self, request, obj_id):
        router_id = self.table.kwargs['router_id']
        rulemanager.remove_rules(request, [obj_id],
                                 router_id=router_id)


class RouterRulesTable(tables.DataTable):
    source = tables.Column("source", verbose_name=_("Source CIDR"))
    destination = tables.Column("destination",
                                verbose_name=_("Destination CIDR"))
    action = tables.Column("action", verbose_name=_("Action"))
    nexthops = tables.Column("nexthops", verbose_name=_("Next Hops"))

    def get_object_display(self, rule):
        return "(%(action)s) %(source)s -> %(destination)s" % rule

    class Meta(object):
        name = "routerrules"
        verbose_name = _("Router Rules")
        table_actions = (AddRouterRule, RemoveRouterRule)
        row_actions = (RemoveRouterRule, )
