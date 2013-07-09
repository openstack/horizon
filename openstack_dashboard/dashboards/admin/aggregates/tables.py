# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 B1 Systems GmbH
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

from django import template
from django.utils.translation import ugettext_lazy as _

from horizon import tables

LOG = logging.getLogger(__name__)


def get_hosts(aggregate):
    template_name = 'admin/aggregates/_aggregate_hosts.html'
    context = {"aggregate": aggregate}
    return template.loader.render_to_string(template_name, context)


def get_metadata(aggregate):
    template_name = 'admin/aggregates/_aggregate_metadata.html'
    context = {"aggregate": aggregate}
    return template.loader.render_to_string(template_name, context)


class AdminAggregatesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"))

    availability_zone = tables.Column("availability_zone",
                                      verbose_name=_("Availability Zone"))

    hosts = tables.Column(get_hosts,
                          verbose_name=_("Hosts"))

    metadata = tables.Column(get_metadata,
                             verbose_name=_("Metadata"))

    class Meta:
        name = "aggregates"
        verbose_name = _("Aggregates")
