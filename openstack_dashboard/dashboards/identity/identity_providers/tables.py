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

from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api


class RegisterIdPLink(tables.LinkAction):
    name = "register"
    verbose_name = _("Register Identity Provider")
    url = "horizon:identity:identity_providers:register"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("identity", "identity:create_identity_provider"),)


class EditIdPLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:identity:identity_providers:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("identity", "identity:update_identity_provider"),)


class ManageProtocolsLink(tables.LinkAction):
    name = "manage_protocols"
    verbose_name = _("Manage Protocols")
    url = "horizon:identity:identity_providers:protocols_tab"
    icon = "pencil"
    policy_rules = (("identity", "identity:list_protocols"),)


class DeleteIdPsAction(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Unregister Identity Provider",
            u"Unregister Identity Providers",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Unregistered Identity Provider",
            u"Unregistered Identity Providers",
            count
        )
    policy_rules = (("identity", "identity:delete_identity_provider"),)

    def delete(self, request, obj_id):
        api.keystone.identity_provider_delete(request, obj_id)


class IdPFilterAction(tables.FilterAction):
    def filter(self, table, idps, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [idp for idp in idps
                if q in idp.ud.lower()]


class IdentityProvidersTable(tables.DataTable):
    id = tables.Column('id',
                       verbose_name=_('Identity Provider ID'),
                       link="horizon:identity:identity_providers:detail")
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'))
    enabled = tables.Column('enabled', verbose_name=_('Enabled'), status=True,
                            filters=(filters.yesno, filters.capfirst))
    remote_ids = tables.Column(
        lambda obj: getattr(obj, 'remote_ids', []),
        verbose_name=_("Remote IDs"),
        wrap_list=True,
        filters=(filters.unordered_list,))

    def get_object_display(self, datum):
        return datum.id

    class Meta(object):
        name = "identity_providers"
        verbose_name = _("Identity Providers")
        row_actions = (ManageProtocolsLink, EditIdPLink, DeleteIdPsAction)
        table_actions = (IdPFilterAction, RegisterIdPLink, DeleteIdPsAction)
