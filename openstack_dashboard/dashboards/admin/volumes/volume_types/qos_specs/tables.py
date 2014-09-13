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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import tables


class SpecEdit(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:admin:volumes:volume_types:qos_specs:edit"
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, qos_spec):
        return reverse(self.url, args=[qos_spec.id, qos_spec.key])


class SpecsTable(tables.DataTable):
    key = tables.Column('key', verbose_name=_('Key'))
    value = tables.Column('value', verbose_name=_('Value'))

    class Meta:
        name = "specs"
        verbose_name = _("Key-Value Pairs")
        row_actions = (SpecEdit,)

    def get_object_id(self, datum):
        return datum.key

    def get_object_display(self, datum):
        return datum.key
