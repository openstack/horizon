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
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard.api import cinder


class CreateGroupType(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Group Type")
    url = "horizon:admin:group_types:create_type"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("volume", "group:group_types_manage"),)


class EditGroupType(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Group Type")
    url = "horizon:admin:group_types:update_type"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "group:group_types_manage"),)


class GroupTypeSpecs(tables.LinkAction):
    name = "specs"
    verbose_name = _("View Specs")
    url = "horizon:admin:group_types:specs:index"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "group:group_types_manage"),)


class GroupTypesFilterAction(tables.FilterAction):

    def filter(self, table, group_types, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [group_type for group_type in group_types
                if query in group_type.name.lower()]


class DeleteGroupType(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Group Type",
            u"Delete Group Types",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Group Type",
            u"Deleted Group Types",
            count
        )
    policy_rules = (("volume", "group:group_types_manage"),)

    def delete(self, request, obj_id):
        try:
            cinder.group_type_delete(request, obj_id)
        except exceptions.BadRequest as e:
            redirect_url = reverse("horizon:admin:group_types:index")
            exceptions.handle(request, e, redirect=redirect_url)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, group_type_id):
        try:
            group_type = \
                cinder.group_type_get(request, group_type_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve group type.'))
        return group_type


class GroupTypesTable(tables.DataTable):
    name = tables.WrappingColumn("name", verbose_name=_("Name"),
                                 form_field=forms.CharField(max_length=64))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'),
                                form_field=forms.CharField(
                                    widget=forms.Textarea(attrs={'rows': 4}),
                                    required=False))
    public = tables.Column("is_public",
                           verbose_name=_("Public"),
                           filters=(filters.yesno, filters.capfirst),
                           form_field=forms.BooleanField(
                               label=_('Public'), required=False))

    def get_object_display(self, group_type):
        return group_type.name

    def get_object_id(self, group_type):
        return str(group_type.id)

    class Meta(object):
        name = "group_types"
        verbose_name = _("Group Types")
        table_actions = (
            GroupTypesFilterAction,
            CreateGroupType,
            DeleteGroupType,
        )
        row_actions = (
            GroupTypeSpecs,
            EditGroupType,
            DeleteGroupType
        )
        row_class = UpdateRow
