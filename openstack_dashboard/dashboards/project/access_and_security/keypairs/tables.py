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

from django.utils.translation import string_concat  # noqa
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.usage import quotas


class DeleteKeyPairs(tables.DeleteAction):
    policy_rules = (("compute", "compute_extension:keypairs:delete"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Key Pair",
            u"Delete Key Pairs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Key Pair",
            u"Deleted Key Pairs",
            count
        )

    def delete(self, request, obj_id):
        api.nova.keypair_delete(request, obj_id)


class ImportKeyPair(tables.LinkAction):
    name = "import"
    verbose_name = _("Import Key Pair")
    url = "horizon:project:access_and_security:keypairs:import"
    classes = ("ajax-modal",)
    icon = "upload"
    policy_rules = (("compute", "compute_extension:keypairs:create"),)


class CreateKeyPair(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Key Pair")
    url = "horizon:project:access_and_security:keypairs:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("compute", "compute_extension:keypairs:create"),)

    def allowed(self, request, keypair=None):
        usages = quotas.tenant_quota_usages(request)
        count = len(self.table.data)
        if (usages.get('key_pairs')
                and usages['key_pairs']['quota'] <= count):
            if "disabled" not in self.classes:
                self.classes = [c for c in self.classes] + ['disabled']
                self.verbose_name = string_concat(self.verbose_name, ' ',
                                                  _("(Quota exceeded)"))
        else:
            self.verbose_name = _("Create Key Pair")
            classes = [c for c in self.classes if c != "disabled"]
            self.classes = classes
        return True


class KeypairsFilterAction(tables.FilterAction):

    def filter(self, table, keypairs, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [keypair for keypair in keypairs
                if query in keypair.name.lower()]


class KeypairsTable(tables.DataTable):
    detail_link = "horizon:project:access_and_security:keypairs:detail"

    name = tables.Column("name", verbose_name=_("Key Pair Name"),
                         link=detail_link)
    fingerprint = tables.Column("fingerprint", verbose_name=_("Fingerprint"))

    def get_object_id(self, keypair):
        return keypair.name

    class Meta(object):
        name = "keypairs"
        verbose_name = _("Key Pairs")
        table_actions = (CreateKeyPair, ImportKeyPair, DeleteKeyPairs,
                         KeypairsFilterAction,)
        row_actions = (DeleteKeyPairs,)
