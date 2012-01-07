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

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class DeleteKeyPairs(tables.Action):
    name = "delete"
    verbose_name = _("Delete")
    verbose_name_plural = _("Delete Keypairs")
    classes = ("danger",)

    def handle(self, data_table, request, object_ids):
        failures = 0
        deleted = []
        for obj_id in object_ids:
            try:
                api.nova.keypair_delete(request, obj_id)
                deleted.append(obj_id)
            except Exception, e:
                failures += 1
                messages.error(request, _("Error deleting keypair: %s") % e)
                LOG.exception("Error deleting keypair.")
        if failures:
            messages.info(request, _("Deleted the following keypairs: %s")
                                     % ", ".join(deleted))
        else:
            messages.success(request, _("Successfully deleted keypairs: %s")
                                        % ", ".join(deleted))
        return shortcuts.redirect('horizon:nova:access_and_security:index')


class ImportKeyPair(tables.LinkAction):
    name = "import"
    verbose_name = _("Import Keypair")
    url = "horizon:nova:access_and_security:keypairs:import"
    attrs = {"class": "ajax-modal btn"}


class CreateKeyPair(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Keypair")
    url = "horizon:nova:access_and_security:keypairs:create"
    attrs = {"class": "ajax-modal btn"}


class KeypairsTable(tables.DataTable):
    name = tables.Column("name")
    fingerprint = tables.Column("fingerprint")

    def get_object_id(self, keypair):
        return keypair.name

    class Meta:
        name = "keypairs"
        verbose_name = _("Keypairs")
        table_actions = (CreateKeyPair, ImportKeyPair, DeleteKeyPairs,)
        row_actions = (DeleteKeyPairs,)
