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

from urllib import parse

from django.template.loader import render_to_string
from django import urls
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.usage import quotas


class DeleteKeyPairs(tables.DeleteAction):
    policy_rules = (("compute", "os_compute_api:os-keypairs:delete"),)
    help_text = _("Removing a key pair can leave OpenStack resources orphaned."
                  " You should not remove a key pair unless you are certain it"
                  " is not being used anywhere.")

    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            "Delete Key Pair",
            "Delete Key Pairs",
            count
        )

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            "Deleted Key Pair",
            "Deleted Key Pairs",
            count
        )

    def delete(self, request, obj_id):
        api.nova.keypair_delete(request, parse.unquote(obj_id))


class QuotaKeypairMixin(object):
    def allowed(self, request, datum=None):
        usages = quotas.tenant_quota_usages(request, targets=('key_pairs', ))
        usages.tally('key_pairs', len(self.table.data))
        if usages['key_pairs']['available'] <= 0:
            if "disabled" not in self.classes:
                self.classes = list(self.classes) + ['disabled']
                self.verbose_name = format_lazy(
                    '{verbose_name} {quota_exceeded}',
                    verbose_name=self.verbose_name,
                    quota_exceeded=_("(Quota exceeded)"))
            return False
        classes = [c for c in self.classes if c != "disabled"]
        self.classes = classes
        return True


class ImportKeyPair(QuotaKeypairMixin, tables.LinkAction):
    name = "import"
    verbose_name = _("Import Public Key")
    url = "horizon:project:key_pairs:import"
    classes = ("ajax-modal",)
    icon = "upload"
    policy_rules = (("compute", "os_compute_api:os-keypairs:create"),)

    def allowed(self, request, keypair=None):
        if super().allowed(request, keypair):
            self.verbose_name = _("Import Public Key")
        return True


class CreateLinkNG(QuotaKeypairMixin, tables.LinkAction):
    name = "create-keypair-ng"
    verbose_name = _("Create Key Pair")
    url = "horizon:project:key_pairs:index"
    classes = ("btn-launch",)
    icon = "plus"
    policy_rules = (("compute", "os_compute_api:os-keypairs:create"),)

    def get_default_attrs(self):
        url = urls.reverse(self.url)
        ngclick = "modal.createKeyPair({ successUrl: '%s' })" % url
        self.attrs.update({
            'ng-controller': 'KeypairController as modal',
            'ng-click': ngclick
        })
        return super().get_default_attrs()

    def get_link_url(self, datum=None):
        return "javascript:void(0);"

    def allowed(self, request, keypair=None):
        if super().allowed(request, keypair):
            self.verbose_name = _("Create Key Pair")
        return True


class KeypairsFilterAction(tables.FilterAction):

    def filter(self, table, keypairs, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [keypair for keypair in keypairs
                if query in keypair.name.lower()]


def get_chevron_id(table, datum):
    """Generate a unique chevron ID for expandable key pair rows.

    This function ensures consistent ID generation between the chevron toggle
    column and the expandable detail row. The ID is based on the table name
    and the unique object identifier for the datum.

    Args:
        table: The DataTable instance (provides table.name and get_object_id())
        datum: The key pair object (passed to get_object_id())

    Returns:
        str: Unique chevron ID "{table_name}_chevron_{object_id}"

    Example:
        For a keypair named "test1" in the "keypairs" table:
        Returns "keypairs_chevron_test1"
    """
    object_id = table.get_object_id(datum)
    return "%s_chevron_%s" % (table.name, object_id)


class ExpandableKeyPairRow(tables.Row):
    """Custom row class for expandable key pair rows."""

    def render(self):
        chevron_id = get_chevron_id(self.table, self.datum)
        return render_to_string("key_pairs/expandable_row.html",
                                {"row": self, "chevron_id": chevron_id})


class ExpandableKeyPairColumn(tables.Column):
    """Column that renders a chevron toggle for expandable rows."""

    def get_data(self, datum):
        chevron_id = get_chevron_id(self.table, datum)
        return render_to_string(
            "key_pairs/_chevron_column.html",
            {"chevron_id": chevron_id}
        )


class KeyPairsTable(tables.DataTable):
    detail_link = "horizon:project:key_pairs:detail"
    chevron = ExpandableKeyPairColumn("chevron",
                                      verbose_name="",
                                      sortable=False,
                                      classes=['chevron_column'])
    name = tables.Column("name", verbose_name=_("Key Pair Name"),
                         link=detail_link)
    key_type = tables.Column("type", verbose_name=_("Key Pair Type"))
    fingerprint = tables.Column("fingerprint", verbose_name=_("Fingerprint"))

    def get_object_id(self, keypair):
        return parse.quote(keypair.name)

    class Meta(object):
        name = "keypairs"
        verbose_name = _("Key Pairs")
        row_class = ExpandableKeyPairRow
        template = 'key_pairs/_keypairs_table.html'
        table_actions = (CreateLinkNG, ImportKeyPair, DeleteKeyPairs,
                         KeypairsFilterAction,)
        row_actions = (DeleteKeyPairs,)
