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


class CreateVolumeType(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Volume Type")
    url = "horizon:admin:volume_types:create_type"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("volume", "volume_extension:types_manage"),)


class EditVolumeType(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Volume Type")
    url = "horizon:admin:volume_types:update_type"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "volume_extension:types_manage"),)


class EditAccess(tables.LinkAction):
    name = "edit_access"
    verbose_name = _("Edit Access")
    url = "horizon:admin:volume_types:edit_access"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "volume_extension:types_manage"),)

    def allowed(self, request, volume_type=None):
        if volume_type is not None:
            return not getattr(volume_type, 'is_public', True)


class ViewVolumeTypeExtras(tables.LinkAction):
    name = "extras"
    verbose_name = _("View Extra Specs")
    url = "horizon:admin:volume_types:extras:index"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "volume_extension:types_manage"),)


class ManageQosSpecAssociation(tables.LinkAction):
    name = "associate"
    verbose_name = _("Manage QoS Spec Association")
    url = "horizon:admin:volume_types:manage_qos_spec_association"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "volume_extension:types_manage"),)


class DeleteVolumeType(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Volume Type",
            u"Delete Volume Types",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Volume Type",
            u"Deleted Volume Types",
            count
        )
    policy_rules = (("volume", "volume_extension:types_manage"),)

    def delete(self, request, obj_id):
        cinder.volume_type_delete(request, obj_id)


class CreateVolumeTypeEncryption(tables.LinkAction):
    name = "create_encryption"
    verbose_name = _("Create Encryption")
    url = "horizon:admin:volume_types:create_type_encryption"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("volume", "volume_extension:volume_type_encryption"),)

    def allowed(self, request, volume_type):
        return (_is_vol_type_enc_possible(request) and
                not _does_vol_type_enc_exist(volume_type))


class UpdateVolumeTypeEncryption(tables.LinkAction):
    name = "update_encryption"
    verbose_name = _("Update Encryption")
    url = "horizon:admin:volume_types:update_type_encryption"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "volume_extension:volume_type_encryption"),)

    def allowed(self, request, volume_type=None):
        return (_is_vol_type_enc_possible(request) and
                _does_vol_type_enc_exist(volume_type))


class DeleteVolumeTypeEncryption(tables.DeleteAction):
    name = "delete_encryption"
    policy_rules = (("volume", "volume_extension:volume_type_encryption"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Encryption",
            u"Delete Encryptions",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Encryption",
            u"Deleted Encryptions",
            count
        )

    def delete(self, request, volume_type_id):
        cinder.volume_encryption_type_delete(request,
                                             volume_type_id)

    def allowed(self, request, volume_type=None):
        return (_is_vol_type_enc_possible(request) and
                _does_vol_type_enc_exist(volume_type))


def _does_vol_type_enc_exist(volume_type):
    # Check to see if there is an existing encryption information
    # for the volume type or not
    return (hasattr(volume_type, 'encryption') and
            hasattr(volume_type.encryption, 'provider'))


def _is_vol_type_enc_possible(request):
    try:
        supported = cinder.extension_supported(request,
                                               'VolumeTypeEncryption')
    except Exception:
        exceptions.handle(request, _('Unable to determine if volume type '
                                     'encryption is supported.'))
        return False
    return supported


def get_volume_type_encryption(volume_type):
    try:
        provider = volume_type.encryption.provider
    except Exception:
        provider = None
    return provider


def get_volume_type_encryption_link(volume_type):
    if _does_vol_type_enc_exist(volume_type):
        return reverse("horizon:admin:volume_types:type_encryption_detail",
                       kwargs={'volume_type_id': volume_type.id})


class VolumeTypesFilterAction(tables.FilterAction):

    def filter(self, table, volume_types, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [volume_type for volume_type in volume_types
                if query in volume_type.name.lower()]


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, volume_type_id):
        try:
            volume_type = \
                cinder.volume_type_get_with_qos_association(request,
                                                            volume_type_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve volume type qos.'))
        return volume_type


class UpdateMetadata(tables.LinkAction):
    name = "update_metadata"
    verbose_name = _("Update Metadata")
    ajax = False
    attrs = {"ng-controller": "MetadataModalHelperController as modal"}

    def __init__(self, **kwargs):
        kwargs['preempt'] = True
        super(UpdateMetadata, self).__init__(**kwargs)

    def get_link_url(self, datum):
        obj_id = self.table.get_object_id(datum)
        self.attrs['ng-click'] = (
            "modal.openMetadataModal('volume_type', '%s', true)" % obj_id)
        return "javascript:void(0);"


class VolumeTypesTable(tables.DataTable):
    name = tables.WrappingColumn("name", verbose_name=_("Name"),
                                 form_field=forms.CharField(max_length=64))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'),
                                form_field=forms.CharField(
                                    widget=forms.Textarea(attrs={'rows': 4}),
                                    required=False))

    assoc_qos_spec = tables.Column("associated_qos_spec",
                                   verbose_name=_("Associated QoS Spec"))
    encryption = tables.Column(get_volume_type_encryption,
                               verbose_name=_("Encryption"),
                               link=get_volume_type_encryption_link)
    public = tables.Column("is_public",
                           verbose_name=_("Public"),
                           filters=(filters.yesno, filters.capfirst),
                           form_field=forms.BooleanField(
                               label=_('Public'), required=False))

    def get_object_display(self, vol_type):
        return vol_type.name

    def get_object_id(self, vol_type):
        return str(vol_type.id)

    class Meta(object):
        name = "volume_types"
        hidden_title = False
        verbose_name = _("Volume Types")
        table_actions = (VolumeTypesFilterAction, CreateVolumeType,
                         DeleteVolumeType,)
        row_actions = (CreateVolumeTypeEncryption,
                       ViewVolumeTypeExtras,
                       ManageQosSpecAssociation,
                       EditVolumeType,
                       UpdateVolumeTypeEncryption,
                       EditAccess,
                       DeleteVolumeTypeEncryption,
                       DeleteVolumeType,
                       UpdateMetadata)
        row_class = UpdateRow


# QOS Specs section of panel
class ManageQosSpec(tables.LinkAction):
    name = "qos_spec"
    verbose_name = _("Manage Specs")
    url = "horizon:admin:volume_types:qos_specs:index"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "volume_extension:types_manage"),)


def render_spec_keys(qos_spec):
    qos_spec_keys = ["%s=%s" % (key, value)
                     for key, value in qos_spec.specs.items()]
    return qos_spec_keys


class CreateQosSpec(tables.LinkAction):
    name = "create"
    verbose_name = _("Create QoS Spec")
    url = "horizon:admin:volume_types:create_qos_spec"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("volume", "volume_extension:types_manage"),)


class DeleteQosSpecs(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete QoS Spec",
            u"Delete QoS Specs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted QoS Spec",
            u"Deleted QoS Specs",
            count
        )
    policy_rules = (("volume", "volume_extension:types_manage"),)

    def delete(self, request, qos_spec_id):
        cinder.qos_spec_delete(request, qos_spec_id)


class EditConsumer(tables.LinkAction):
    name = "edit_consumer"
    verbose_name = _("Edit Consumer")
    url = "horizon:admin:volume_types:edit_qos_spec_consumer"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("volume", "volume_extension:types_manage"),)


class QosSpecsTable(tables.DataTable):
    name = tables.WrappingColumn('name', verbose_name=_('Name'))
    consumer = tables.Column('consumer', verbose_name=_('Consumer'))
    specs = tables.Column(render_spec_keys,
                          verbose_name=_('Specs'),
                          wrap_list=True,
                          filters=(filters.unordered_list,))

    def get_object_display(self, qos_specs):
        return qos_specs.name

    def get_object_id(self, qos_specs):
        return qos_specs.id

    class Meta(object):
        name = "qos_specs"
        hidden_title = False
        verbose_name = _("QoS Specs")
        table_actions = (CreateQosSpec, DeleteQosSpecs,)
        row_actions = (ManageQosSpec, EditConsumer, DeleteQosSpecs)
