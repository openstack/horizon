#    (c) Copyright 2014 Hewlett-Packard Development Company, L.P.
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

from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import forms
from horizon import tables

from openstack_dashboard.api import glance
from openstack_dashboard.dashboards.admin.metadata_defs \
    import constants


class ImportNamespace(tables.LinkAction):
    name = "import"
    verbose_name = _("Import Namespace")
    url = constants.METADATA_CREATE_URL
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("image", "add_metadef_namespace"),)


class EditNamespace(tables.LinkAction):
    name = 'update'
    verbose_name = _('Edit Namespace')
    url = constants.METADATA_UPDATE_URL
    classes = ('ajax-modal',)


class DeleteNamespace(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Namespace",
            u"Delete Namespaces",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Namespace",
            u"Deleted Namespaces",
            count
        )

    policy_rules = (("image", "modify_metadef_namespace"),)

    def allowed(self, request, namespace=None):
        # Protected namespaces can not be deleted.
        if namespace and namespace.protected:
            return False
        # Return True to allow table-level bulk delete action to appear.
        return True

    def delete(self, request, obj_id):
        glance.metadefs_namespace_delete(request, obj_id)


class ManageResourceTypeAssociations(tables.LinkAction):
    name = "manage_resource_types"
    verbose_name = _("Update Associations")
    url = constants.METADATA_MANAGE_RESOURCES_URL
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("image", "list_metadef_resource_types"),
                    ("image", "add_metadef_resource_type_association"))

    def allowed(self, request, namespace=None):
        # Protected namespace can not be updated
        if namespace and namespace.protected:
            return False
        # Return True to allow table-level bulk delete action to appear.
        return True


class AdminMetadataFilterAction(tables.FilterAction):
    filter_type = "server"
    filter_choices = (('resource_types', _("Resource Types ="), True),)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, namespace_name):
        return glance.metadefs_namespace_get(request,
                                             namespace_name,
                                             wrap=True)


class AdminNamespacesTable(tables.DataTable):
    display_name = tables.Column(
        "display_name",
        link=constants.METADATA_DETAIL_URL,
        verbose_name=_("Name"),
        form_field=forms.CharField(max_length=80))
    description = tables.Column(
        lambda obj: getattr(obj, 'description', None),
        verbose_name=_('Description'),
        form_field=forms.CharField(widget=forms.Textarea(), required=False),
        truncate=200)
    resource_type_names = tables.Column(
        lambda obj: getattr(obj, 'resource_type_names', []),
        verbose_name=_("Resource Types"),
        wrap_list=True,
        filters=(filters.unordered_list,))
    public = tables.Column(
        "public",
        verbose_name=_("Public"),
        empty_value=False,
        form_field=forms.BooleanField(required=False),
        filters=(filters.yesno, filters.capfirst))
    protected = tables.Column(
        "protected",
        verbose_name=_("Protected"),
        empty_value=False,
        form_field=forms.BooleanField(required=False),
        filters=(filters.yesno, filters.capfirst))

    def get_object_id(self, datum):
        return datum.namespace

    def get_object_display(self, datum):
        if hasattr(datum, 'display_name'):
            return datum.display_name
        return None

    class Meta(object):
        name = "namespaces"
        verbose_name = _("Namespaces")
        row_class = UpdateRow
        table_actions = (AdminMetadataFilterAction,
                         ImportNamespace,
                         DeleteNamespace,)
        row_actions = (EditNamespace,
                       ManageResourceTypeAssociations,
                       DeleteNamespace,)
        pagination_param = "namespace_marker"
