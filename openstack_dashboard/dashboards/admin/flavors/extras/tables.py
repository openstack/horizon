# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2012 Intel, Inc.
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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api


class ExtraSpecDelete(tables.DeleteAction):
    data_type_singular = _("ExtraSpec")
    data_type_plural = _("ExtraSpecs")

    def delete(self, request, obj_ids):
        flavor = api.nova.flavor_get(request, self.table.kwargs['id'])
        flavor.unset_keys([obj_ids])


class ExtraSpecCreate(tables.LinkAction):
    name = "create"
    verbose_name = _("Create")
    url = "horizon:admin:flavors:extras:create"
    classes = ("btn-create", "ajax-modal")

    def get_link_url(self, extra_spec=None):
        return reverse(self.url, args=[self.table.kwargs['id']])


class ExtraSpecEdit(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:admin:flavors:extras:edit"
    classes = ("btn-edit", "ajax-modal")

    def get_link_url(self, extra_spec):
        return reverse(self.url, args=[self.table.kwargs['id'],
                                       extra_spec.key])


class ExtraSpecsTable(tables.DataTable):
    key = tables.Column('key', verbose_name=_('Key'))
    value = tables.Column('value', verbose_name=_('Value'))

    class Meta:
        name = "extras"
        verbose_name = _("Extra Specs")
        table_actions = (ExtraSpecCreate, ExtraSpecDelete)
        row_actions = (ExtraSpecEdit, ExtraSpecDelete)

    def get_object_id(self, datum):
        return datum.key

    def get_object_display(self, datum):
        return datum.key
