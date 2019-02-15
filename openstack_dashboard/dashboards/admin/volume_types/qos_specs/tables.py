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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from six.moves.urllib import parse

from horizon import tables

from openstack_dashboard import api


class SpecCreateKeyValuePair(tables.LinkAction):
    # this is to create a spec key-value pair for an existing QOS Spec
    name = "create"
    verbose_name = _("Create")
    url = "horizon:admin:volume_types:qos_specs:create"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, qos_spec=None):
        qos_spec_id = self.table.kwargs['qos_spec_id']
        return reverse(self.url, args=[qos_spec_id])


class SpecDeleteKeyValuePair(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Spec",
            u"Delete Specs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Spec",
            u"Deleted Specs",
            count
        )

    def delete(self, request, obj_id):
        qos_spec_id = self.table.kwargs['qos_spec_id']
        # use "unset" api to remove this key-value pair from QOS Spec
        key = parse.unquote(obj_id)
        api.cinder.qos_spec_unset_keys(request,
                                       qos_spec_id,
                                       [key])

    # redirect to non-modal page
    def get_success_url(self, request=None):
        return reverse('horizon:admin:volume_types:index')


class SpecEditKeyValuePair(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:admin:volume_types:qos_specs:edit"
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, qos_spec):
        return reverse(self.url, args=[qos_spec.id, qos_spec.key])


class SpecsTable(tables.DataTable):
    key = tables.Column('key', verbose_name=_('Key'))
    value = tables.Column('value', verbose_name=_('Value'))

    class Meta(object):
        name = "specs"
        verbose_name = _("Key-Value Pairs")
        table_actions = (SpecCreateKeyValuePair, SpecDeleteKeyValuePair)
        row_actions = (SpecEditKeyValuePair, SpecDeleteKeyValuePair)

    def get_object_id(self, datum):
        return parse.quote(datum.key)

    def get_object_display(self, datum):
        return datum.key
