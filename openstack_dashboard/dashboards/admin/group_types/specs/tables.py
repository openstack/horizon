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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from six.moves.urllib import parse

from horizon import tables

from openstack_dashboard import api


class GroupTypeSpecDelete(tables.DeleteAction):

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
            u"Delete Spec",
            u"Delete Specs",
            count
        )

    def delete(self, request, obj_id):
        key = parse.unquote(obj_id)
        api.cinder.group_type_spec_unset(request,
                                         self.table.kwargs['type_id'],
                                         [key])

    def get_success_url(self, request):
        return reverse('horizon:admin:group_types:index')


class GroupTypeSpecCreate(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Spec")
    url = "horizon:admin:group_types:specs:create"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, group_type_spec=None):
        return reverse(self.url, args=[self.table.kwargs['type_id']])


class GroupTypeSpecEdit(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Spec")
    url = "horizon:admin:group_types:specs:edit"
    classes = ("btn-edit", "ajax-modal")

    def get_link_url(self, group_type_spec):
        return reverse(self.url, args=[self.table.kwargs['type_id'],
                                       group_type_spec.key])


class GroupTypeSpecsTable(tables.DataTable):
    key = tables.Column('key', verbose_name=_('Key'))
    value = tables.Column('value', verbose_name=_('Value'))

    class Meta(object):
        name = "specs"
        verbose_name = _("Group Type Specs")
        table_actions = (GroupTypeSpecCreate, GroupTypeSpecDelete)
        row_actions = (GroupTypeSpecEdit, GroupTypeSpecDelete)

    def get_object_id(self, datum):
        return parse.quote(datum.key)

    def get_object_display(self, datum):
        return datum.key
