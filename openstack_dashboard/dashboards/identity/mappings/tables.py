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

import json

from django.utils import safestring
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api


class CreateMappingLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Mapping")
    url = "horizon:identity:mappings:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("identity", "identity:create_mapping"),)


class EditMappingLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:identity:mappings:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("identity", "identity:update_mapping"),)


class DeleteMappingsAction(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Mapping",
            u"Delete Mappings",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Mapping",
            u"Deleted Mappings",
            count
        )
    policy_rules = (("identity", "identity:delete_mapping"),)

    def delete(self, request, obj_id):
        api.keystone.mapping_delete(request, obj_id)


class MappingFilterAction(tables.FilterAction):
    def filter(self, table, mappings, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [mapping for mapping in mappings
                if q in mapping.ud.lower()]


def get_rules_as_json(mapping):
    rules = getattr(mapping, 'rules', None)
    if rules:
        rules = json.dumps(rules, indent=4)
    return safestring.mark_safe(rules)


class MappingsTable(tables.DataTable):
    id = tables.Column('id', verbose_name=_('Mapping ID'))
    description = tables.Column(get_rules_as_json,
                                verbose_name=_('Rules'))

    class Meta(object):
        name = "idp_mappings"
        verbose_name = _("Attribute Mappings")
        row_actions = (EditMappingLink, DeleteMappingsAction)
        table_actions = (MappingFilterAction, CreateMappingLink,
                         DeleteMappingsAction)
