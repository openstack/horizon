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

from django.utils.translation import ugettext as _

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class DeleteKeyPairs(tables.DeleteAction):
    data_type_singular = _("Keypair")
    data_type_plural = _("Keypairs")

    def delete(self, request, obj_id):
        api.nova.keypair_delete(request, obj_id)


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
