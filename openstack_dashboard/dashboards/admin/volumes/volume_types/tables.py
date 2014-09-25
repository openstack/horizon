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
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard.api import cinder


class CreateVolumeType(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Volume Type")
    url = "horizon:admin:volumes:volume_types:create_type"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("volume", "volume_extension:types_manage"),)


class ViewVolumeTypeExtras(tables.LinkAction):
    name = "extras"
    verbose_name = _("View Extra Specs")
    url = "horizon:admin:volumes:volume_types:extras:index"
    classes = ("btn-edit",)
    policy_rules = (("volume", "volume_extension:types_manage"),)


class ManageQosSpecAssociation(tables.LinkAction):
    name = "associate"
    verbose_name = _("Manage QOS Spec Association")
    url = "horizon:admin:volumes:volume_types:manage_qos_spec_association"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "volume_extension:types_manage"),)


class DeleteVolumeType(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete VolumeType",
            u"Delete VolumeTypes",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted VolumeType",
            u"Deleted VolumeTypes",
            count
        )
    policy_rules = (("volume", "volume_extension:types_manage"),)

    def delete(self, request, obj_id):
        cinder.volume_type_delete(request, obj_id)


class VolumeTypesTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Name"))
    assoc_qos_spec = tables.Column("associated_qos_spec",
                                   verbose_name=_("Associated QOS Spec"))

    def get_object_display(self, vol_type):
        return vol_type.name

    def get_object_id(self, vol_type):
        return str(vol_type.id)

    class Meta:
        name = "volume_types"
        verbose_name = _("Volume Types")
        table_actions = (CreateVolumeType, DeleteVolumeType,)
        row_actions = (ViewVolumeTypeExtras,
                       ManageQosSpecAssociation,
                       DeleteVolumeType,)


# QOS Specs section of panel
class ManageQosSpec(tables.LinkAction):
    name = "qos_spec"
    verbose_name = _("Manage Specs")
    url = "horizon:admin:volumes:volume_types:qos_specs:index"
    icon = "pencil"
    policy_rules = (("volume", "volume_extension:types_manage"),)


def render_spec_keys(qos_spec):
    qos_spec_keys = ["%s=%s" % (key, value)
                     for key, value in qos_spec.specs.items()]
    return qos_spec_keys


class CreateQosSpec(tables.LinkAction):
    name = "create"
    verbose_name = _("Create QOS Spec")
    url = "horizon:admin:volumes:volume_types:create_qos_spec"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("volume", "volume_extension:types_manage"),)


class DeleteQosSpecs(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete QOS Spec",
            u"Delete QOS Specs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted QOS Spec",
            u"Deleted QOS Specs",
            count
        )
    policy_rules = (("volume", "volume_extension:types_manage"),)

    def delete(self, request, qos_spec_id):
        cinder.qos_spec_delete(request, qos_spec_id)


class EditConsumer(tables.LinkAction):
    name = "edit_consumer"
    verbose_name = _("Edit Consumer")
    url = "horizon:admin:volumes:volume_types:edit_qos_spec_consumer"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "volume_extension:types_manage"),)


class QosSpecsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    consumer = tables.Column('consumer', verbose_name=_('Consumer'))
    specs = tables.Column(render_spec_keys,
                          verbose_name=_('Specs'),
                          wrap_list=True,
                          filters=(filters.unordered_list,))

    def get_object_display(self, qos_specs):
        return qos_specs.name

    def get_object_id(self, qos_specs):
        return qos_specs.id

    class Meta:
        name = "qos_specs"
        verbose_name = _("QOS Specs")
        table_actions = (CreateQosSpec, DeleteQosSpecs,)
        row_actions = (ManageQosSpec, EditConsumer, DeleteQosSpecs)
