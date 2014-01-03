# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013,  Big Switch Networks,  Inc.
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


class RouterRulesTable(tables.DataTable):
    source = tables.Column("source", verbose_name=_("Source CIDR"))
    destination = tables.Column("destination",
                                verbose_name=_("Destination CIDR"))
    action = tables.Column("action", verbose_name=_("Action"))
    nexthops = tables.Column("nexthops", verbose_name=_("Next Hops"))

    class Meta:
        name = "routerrules"
        verbose_name = _("Router Rules")
