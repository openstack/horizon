# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Admin views for managing volumes.
"""
from collections import OrderedDict

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized
from horizon import views

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.volume_types \
    import forms as volume_types_forms
from openstack_dashboard.dashboards.admin.volume_types \
    import tables as volume_types_tables
from openstack_dashboard.dashboards.project.volumes \
    import views as volumes_views
from openstack_dashboard import policy


class VolumeTypesView(tables.MultiTableView, volumes_views.VolumeTableMixIn):
    table_classes = (volume_types_tables.VolumeTypesTable,
                     volume_types_tables.QosSpecsTable)
    page_title = _("Volume Types")
    template_name = "admin/volume_types/volume_types_tables.html"

    def get_volume_types_data(self):
        try:
            volume_types = \
                api.cinder.volume_type_list_with_qos_associations(self.request)
        except Exception:
            volume_types = []
            exceptions.handle(self.request,
                              _("Unable to retrieve volume types"))

        encryption_allowed = policy.check(
            (("volume", "volume_extension:volume_type_encryption"),),
            self.request)

        if encryption_allowed:
            # Gather volume type encryption information
            try:
                vol_type_enc_list = api.cinder.volume_encryption_type_list(
                    self.request)
            except Exception:
                vol_type_enc_list = []
                msg = _(
                    'Unable to retrieve volume type encryption information.')
                exceptions.handle(self.request, msg)

            vol_type_enc_dict = OrderedDict([(e.volume_type_id, e) for e in
                                            vol_type_enc_list])
            for volume_type in volume_types:
                vol_type_enc = vol_type_enc_dict.get(volume_type.id, None)
                if vol_type_enc is not None:
                    volume_type.encryption = vol_type_enc
                    volume_type.encryption.name = volume_type.name
                else:
                    volume_type.encryption = None

        return volume_types

    def get_qos_specs_data(self):
        try:
            qos_specs = api.cinder.qos_spec_list(self.request)
        except Exception:
            qos_specs = []
            exceptions.handle(self.request,
                              _("Unable to retrieve QoS specs"))
        return qos_specs


INDEX_URL = 'horizon:admin:volume_types:index'


class CreateVolumeTypeView(forms.ModalFormView):
    form_class = volume_types_forms.CreateVolumeType
    modal_id = "create_volume_type_modal"
    template_name = 'admin/volume_types/create_volume_type.html'
    submit_label = _("Create Volume Type")
    submit_url = reverse_lazy("horizon:admin:volume_types:create_type")
    success_url = reverse_lazy('horizon:admin:volume_types:index')
    page_title = _("Create Volume Type")


class VolumeTypeEncryptionDetailView(views.HorizonTemplateView):
    template_name = "admin/volume_types/volume_encryption_type_detail.html"
    page_title = _("Volume Type Encryption Details")

    def get_context_data(self, **kwargs):
        context = super(VolumeTypeEncryptionDetailView, self).\
            get_context_data(**kwargs)
        context["volume_type_encryption"] = self.get_data()
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            volume_type_id = self.kwargs['volume_type_id']
            self._volume_type_encryption = api.cinder.\
                volume_encryption_type_get(self.request, volume_type_id)
            volume_type_list = api.cinder.volume_type_list(self.request)
            for volume_type in volume_type_list:
                if volume_type.id == volume_type_id:
                    self.name = volume_type.name
            self._volume_type_encryption.name = self.name
        except Exception:
            redirect = reverse(INDEX_URL)
            exceptions.handle(self.request,
                              _('Unable to retrieve volume type encryption'
                                ' details.'),
                              redirect=redirect)
            return None

        return self._volume_type_encryption


class CreateVolumeTypeEncryptionView(forms.ModalFormView):
    form_class = volume_types_forms.CreateVolumeTypeEncryption
    form_id = "create_volume_form"
    modal_id = "create_volume_type_modal"
    template_name = "admin/volume_types/create_volume_type_encryption.html"
    submit_label = _("Create Volume Type Encryption")
    submit_url = "horizon:admin:volume_types:create_type_encryption"
    success_url = reverse_lazy(INDEX_URL)
    page_title = _("Create an Encrypted Volume Type")

    @memoized.memoized_method
    def get_name(self):
        if not hasattr(self, "name"):
            self.name = _get_volume_type_name(self.request, self.kwargs)
        return self.name

    def get_context_data(self, **kwargs):
        context = super(CreateVolumeTypeEncryptionView, self).\
            get_context_data(**kwargs)
        context['volume_type_id'] = self.kwargs['volume_type_id']
        args = (self.kwargs['volume_type_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        name = self.get_name()
        return {'name': name,
                'volume_type_id': self.kwargs['volume_type_id']}


class EditVolumeTypeView(forms.ModalFormView):
    form_class = volume_types_forms.EditVolumeType
    template_name = 'admin/volume_types/update_volume_type.html'
    success_url = reverse_lazy('horizon:admin:volume_types:index')
    cancel_url = reverse_lazy('horizon:admin:volume_types:index')
    submit_label = _('Edit')

    @memoized.memoized_method
    def get_data(self):
        try:
            volume_type_id = self.kwargs['type_id']
            volume_type = api.cinder.volume_type_get(self.request,
                                                     volume_type_id)
        except Exception:
            error_message = _(
                'Unable to retrieve volume type for: "%s"') \
                % volume_type_id
            exceptions.handle(self.request,
                              error_message,
                              redirect=self.success_url)

        return volume_type

    def get_context_data(self, **kwargs):
        context = super(EditVolumeTypeView, self).get_context_data(**kwargs)
        context['volume_type'] = self.get_data()

        return context

    def get_initial(self):
        volume_type = self.get_data()
        return {'id': self.kwargs['type_id'],
                'name': volume_type.name,
                'is_public': getattr(volume_type, 'is_public', True),
                'description': getattr(volume_type, 'description', "")}


def _get_volume_type_name(request, kwargs):
    try:
        volume_type_list = api.cinder.volume_type_list(request)
        for volume_type in volume_type_list:
            if volume_type.id == kwargs['volume_type_id']:
                return volume_type.name
    except Exception:
        msg = _('Unable to retrieve volume type name.')
        url = reverse(INDEX_URL)
        exceptions.handle(request, msg, redirect=url)


class UpdateVolumeTypeEncryptionView(forms.ModalFormView):
    form_class = volume_types_forms.UpdateVolumeTypeEncryption
    form_id = "update_volume_form"
    modal_id = "update_volume_type_modal"
    template_name = "admin/volume_types/update_volume_type_encryption.html"
    page_title = _("Update an Encrypted Volume Type")
    submit_label = _("Update Volume Type Encryption")
    submit_url = "horizon:admin:volume_types:update_type_encryption"
    success_url = reverse_lazy('horizon:admin:volume_types:index')

    def get_object(self):
        if not hasattr(self, "_object"):
            try:
                self._object = api.cinder.\
                    volume_encryption_type_get(self.request,
                                               self.kwargs['volume_type_id'])
            except Exception:
                msg = _('Unable to retrieve encryption type.')
                url = reverse('horizon:admin:volume_types:index')
                exceptions.handle(self.request, msg, redirect=url)
        return self._object

    @memoized.memoized_method
    def get_name(self):
        if not hasattr(self, "name"):
            self.name = _get_volume_type_name(self.request, self.kwargs)
        return self.name

    def get_context_data(self, **kwargs):
        context = super(UpdateVolumeTypeEncryptionView, self).\
            get_context_data(**kwargs)
        context['volume_type_id'] = self.kwargs['volume_type_id']
        args = (self.kwargs['volume_type_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        encryption_type = self.get_object()
        name = self.get_name()
        return {'volume_type_id': encryption_type.volume_type_id,
                'control_location': encryption_type.control_location,
                'key_size': encryption_type.key_size,
                'provider': encryption_type.provider,
                'cipher': encryption_type.cipher,
                'name': name}


class CreateQosSpecView(forms.ModalFormView):
    form_class = volume_types_forms.CreateQosSpec
    modal_id = "create_volume_type_modal"
    template_name = 'admin/volume_types/create_qos_spec.html'
    success_url = reverse_lazy('horizon:admin:volume_types:index')
    page_title = _("Create QoS Spec")
    submit_label = _("Create")
    submit_url = reverse_lazy("horizon:admin:volume_types:create_qos_spec")


class EditQosSpecConsumerView(forms.ModalFormView):
    form_class = volume_types_forms.EditQosSpecConsumer
    modal_id = "edit_qos_spec_modal"
    template_name = 'admin/volume_types/edit_qos_spec_consumer.html'
    submit_label = _("Modify Consumer")
    submit_url = "horizon:admin:volume_types:edit_qos_spec_consumer"
    success_url = reverse_lazy('horizon:admin:volume_types:index')
    page_title = _("Edit QoS Spec Consumer")

    def get_context_data(self, **kwargs):
        context = super(EditQosSpecConsumerView, self).\
            get_context_data(**kwargs)
        context['qos_spec_id'] = self.kwargs["qos_spec_id"]
        args = (self.kwargs['qos_spec_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        qos_spec_id = self.kwargs['qos_spec_id']
        try:
            self._object = api.cinder.qos_spec_get(self.request, qos_spec_id)
        except Exception:
            msg = _('Unable to retrieve QoS Spec details.')
            exceptions.handle(self.request, msg)
        return self._object

    def get_initial(self):
        qos_spec = self.get_object()
        qos_spec_id = self.kwargs['qos_spec_id']

        return {'qos_spec_id': qos_spec_id,
                'qos_spec': qos_spec}


class ManageQosSpecAssociationView(forms.ModalFormView):
    form_class = volume_types_forms.ManageQosSpecAssociation
    modal_id = "associate_qos_spec_modal"
    template_name = 'admin/volume_types/associate_qos_spec.html'
    submit_label = _("Associate")
    submit_url = "horizon:admin:volume_types:manage_qos_spec_association"
    success_url = reverse_lazy('horizon:admin:volume_types:index')
    page_title = _("Associate QoS Spec with Volume Type")

    def get_context_data(self, **kwargs):
        context = super(ManageQosSpecAssociationView, self).\
            get_context_data(**kwargs)
        context['type_id'] = self.kwargs["type_id"]
        args = (self.kwargs['type_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        type_id = self.kwargs['type_id']
        try:
            self._object = api.cinder.volume_type_get(self.request, type_id)
        except Exception:
            msg = _('Unable to retrieve volume type details.')
            exceptions.handle(self.request, msg)
        return self._object

    @memoized.memoized_method
    def get_qos_specs(self, *args, **kwargs):
        try:
            return api.cinder.qos_spec_list(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve QoS Specs.'))

    def find_current_qos_spec_association(self, vol_type_id):
        qos_specs = self.get_qos_specs()
        if qos_specs:
            try:
                # find out which QOS Spec is currently associated with this
                # volume type, if any
                # NOTE - volume type can only have ONE QOS Spec association
                for qos_spec in qos_specs:
                    type_ids = \
                        api.cinder.qos_spec_get_associations(self.request,
                                                             qos_spec.id)
                    for vtype in type_ids:
                        if vtype.id == vol_type_id:
                            return qos_spec

            except Exception:
                exceptions.handle(
                    self.request,
                    _('Unable to retrieve QoS Spec association.'))

        return None

    def get_initial(self):
        volume_type = self.get_object()
        vol_type_id = self.kwargs['type_id']

        cur_qos_spec_id = None
        cur_qos_spec_name = None

        qos_spec = self.find_current_qos_spec_association(vol_type_id)
        if qos_spec:
            cur_qos_spec_id = qos_spec.id
            cur_qos_spec_name = qos_spec.name

        return {'type_id': vol_type_id,
                'name': getattr(volume_type, 'name', None),
                'cur_qos_spec_id': cur_qos_spec_id,
                'cur_qos_spec_name': cur_qos_spec_name,
                'qos_specs': self.get_qos_specs()}


class EditAccessView(forms.ModalFormView):
    form_class = volume_types_forms.EditTypeAccessForm
    template_name = 'admin/volume_types/update_access.html'
    submit_label = _("Save")
    submit_url = "horizon:admin:volume_types:edit_access"
    success_url = reverse_lazy('horizon:admin:volume_types:index')
    cancel_url = reverse_lazy('horizon:admin:volume_types:index')
    page_title = _("Edit Volume Type Access")

    def get_context_data(self, **kwargs):
        context = super(EditAccessView, self).get_context_data(**kwargs)
        context['volume_type_id'] = self.kwargs["volume_type_id"]
        args = (self.kwargs['volume_type_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        return {'volume_type_id': self.kwargs['volume_type_id']}
