# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
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

from horizon import tables

from openstack_dashboard import api
from ..floating_ips.utils import get_int_or_uuid


LOG = logging.getLogger(__name__)


class DeleteGroup(tables.DeleteAction):
    data_type_singular = _("Security Group")
    data_type_plural = _("Security Groups")

    def allowed(self, request, security_group=None):
        if not security_group:
            return True
        return security_group.name != 'default'

    def delete(self, request, obj_id):
        api.nova.security_group_delete(request, obj_id)


class CreateGroup(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Security Group")
    url = "horizon:project:access_and_security:security_groups:create"
    classes = ("ajax-modal", "btn-create")


class EditRules(tables.LinkAction):
    name = "edit_rules"
    verbose_name = _("Edit Rules")
    url = "horizon:project:access_and_security:security_groups:detail"
    classes = ("btn-edit")


class SecurityGroupsTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Name"))
    description = tables.Column("description", verbose_name=_("Description"))

    def sanitize_id(self, obj_id):
        return get_int_or_uuid(obj_id)

    class Meta:
        name = "security_groups"
        verbose_name = _("Security Groups")
        table_actions = (CreateGroup, DeleteGroup)
        row_actions = (EditRules, DeleteGroup)


class CreateRule(tables.LinkAction):
    name = "add_rule"
    verbose_name = _("Add Rule")
    url = "horizon:project:access_and_security:security_groups:add_rule"
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self):
        return reverse(self.url, args=[self.table.kwargs['security_group_id']])


class DeleteRule(tables.DeleteAction):
    data_type_singular = _("Rule")
    data_type_plural = _("Rules")

    def delete(self, request, obj_id):
        api.nova.security_group_rule_delete(request, obj_id)

    def get_success_url(self, request):
        sg_id = self.table.kwargs['security_group_id']
        return reverse("horizon:project:access_and_security:"
                       "security_groups:detail", args=[sg_id])


def get_source(rule):
    if 'cidr' in rule.ip_range:
        return rule.ip_range['cidr'] + ' (CIDR)'
    elif 'name' in rule.group:
        return rule.group['name']
    else:
        return None


def filter_protocol(protocol):
    if protocol is None:
        return _('Any')
    return unicode.upper(protocol)


class RulesTable(tables.DataTable):
    protocol = tables.Column("ip_protocol",
                             verbose_name=_("IP Protocol"),
                             filters=(filter_protocol,))
    from_port = tables.Column("from_port", verbose_name=_("From Port"))
    to_port = tables.Column("to_port", verbose_name=_("To Port"))
    source = tables.Column(get_source, verbose_name=_("Source"))

    def sanitize_id(self, obj_id):
        return get_int_or_uuid(obj_id)

    def get_object_display(self, rule):
        return unicode(rule)

    class Meta:
        name = "rules"
        verbose_name = _("Security Group Rules")
        table_actions = (CreateRule, DeleteRule)
        row_actions = (DeleteRule,)
