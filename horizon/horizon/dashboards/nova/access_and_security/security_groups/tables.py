# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Nebula, Inc.
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

from django import shortcuts
from django.contrib import messages
from django.core.urlresolvers import reverse
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class DeleteGroup(tables.Action):
    name = "delete"
    verbose_name = _("Delete")
    verbose_name_plural = _("Delete Security Groups")
    classes = ('danger',)

    def allowed(self, request, security_group=None):
        if not security_group:
            return True
        return security_group.name != 'default'

    def handle(self, table, request, object_ids):
        tenant_id = request.user.tenant_id
        deleted = []
        for obj_id in object_ids:
            obj = table.get_object_by_id(int(obj_id))
            if obj.name == "default":
                messages.info(request, _("The default group can't be deleted"))
                continue
            try:
                security_group = api.security_group_delete(request, obj_id)
                deleted.append(obj)
                LOG.info('Deleted security_group: "%s"' % obj.name)
            except novaclient_exceptions.ClientException, e:
                LOG.exception("Error deleting security group")
                messages.error(request, _('Unable to delete group: %s')
                                         % obj.name)
        if deleted:
            messages.success(request,
                             _('Successfully deleted security groups: %s')
                               % ", ".join([group.name for group in deleted]))
        return shortcuts.redirect('horizon:nova:access_and_security:index')


class CreateGroup(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Security Group")
    url = "horizon:nova:access_and_security:security_groups:create"
    attrs = {"class": "btn small ajax-modal"}


class EditRules(tables.LinkAction):
    name = "edit_rules"
    verbose_name = _("Edit Rules")
    url = "horizon:nova:access_and_security:security_groups:edit_rules"


class SecurityGroupsTable(tables.DataTable):
    name = tables.Column("name")
    description = tables.Column("description")

    class Meta:
        name = "security_groups"
        verbose_name = _("Security Groups")
        table_actions = (CreateGroup, DeleteGroup)
        row_actions = (EditRules, DeleteGroup)


class DeleteRule(tables.Action):
    name = "delete"
    verbose_name = _("Delete")
    classes = ('danger',)

    def single(self, table, request, obj_id):
        tenant_id = request.user.tenant_id
        obj = table.get_object_by_id(int(obj_id))
        try:
            LOG.info('Delete security_group_rule: "%s"' % obj_id)
            security_group = api.security_group_rule_delete(request, obj_id)
            messages.info(request, _('Successfully deleted rule: %s')
                                    % obj_id)
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in DeleteRule")
            messages.error(request, _('Error authorizing security group: %s')
                                     % e.message)
        return shortcuts.redirect('horizon:nova:access_and_security:'
                                  'security_groups:edit_rules',
                                  (obj.parent_group_id))


def get_cidr(rule):
    return rule.ip_range['cidr']


class RulesTable(tables.DataTable):
    protocol = tables.Column("ip_protocol", verbose_name=_("IP Protocol"))
    from_port = tables.Column("from_port", verbose_name=_("From Port"))
    to_port = tables.Column("to_port", verbose_name=_("To Port"))
    cidr = tables.Column(get_cidr, verbose_name=_("CIDR"))

    class Meta:
        name = "rules"
        verbose_name = _("Security Group Rules")
        row_actions = (DeleteRule,)
