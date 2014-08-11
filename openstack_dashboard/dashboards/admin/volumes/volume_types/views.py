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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.volumes.volume_types \
    import forms as volume_type_forms
from openstack_dashboard.dashboards.admin.volumes.volumes \
    import forms as volumes_forms


class CreateVolumeTypeView(forms.ModalFormView):
    form_class = volumes_forms.CreateVolumeType
    template_name = 'admin/volumes/volume_types/create_volume_type.html'
    success_url = 'horizon:admin:volumes:volume_types_tab'

    def get_success_url(self):
        return reverse(self.success_url)


class CreateQosSpecView(forms.ModalFormView):
    form_class = volumes_forms.CreateQosSpec
    template_name = 'admin/volumes/volume_types/create_qos_spec.html'
    success_url = 'horizon:admin:volumes:volume_types_tab'

    def get_success_url(self):
        return reverse(self.success_url)


class EditQosSpecConsumerView(forms.ModalFormView):
    form_class = volume_type_forms.EditQosSpecConsumer
    template_name = 'admin/volumes/volume_types/edit_qos_spec_consumer.html'
    success_url = 'horizon:admin:volumes:volume_types_tab'

    def get_success_url(self):
        return reverse(self.success_url)

    def get_context_data(self, **kwargs):
        context = super(EditQosSpecConsumerView, self).\
            get_context_data(**kwargs)
        context['qos_spec_id'] = self.kwargs["qos_spec_id"]
        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        qos_spec_id = self.kwargs['qos_spec_id']
        try:
            self._object = api.cinder.qos_spec_get(self.request, qos_spec_id)
        except Exception:
            msg = _('Unable to retrieve QOS Spec details.')
            exceptions.handle(self.request, msg)
        return self._object

    def get_initial(self):
        qos_spec = self.get_object()
        qos_spec_id = self.kwargs['qos_spec_id']

        return {'qos_spec_id': qos_spec_id,
                'qos_spec': qos_spec}


class ManageQosSpecAssociationView(forms.ModalFormView):
    form_class = volume_type_forms.ManageQosSpecAssociation
    template_name = 'admin/volumes/volume_types/associate_qos_spec.html'
    success_url = 'horizon:admin:volumes:volume_types_tab'

    def get_success_url(self):
        return reverse(self.success_url)

    def get_context_data(self, **kwargs):
        context = super(ManageQosSpecAssociationView, self).\
            get_context_data(**kwargs)
        context['type_id'] = self.kwargs["type_id"]
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
                              _('Unable to retrieve QOS Specs.'))

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
                exceptions.handle(self.request,
                        _('Unable to retrieve QOS Spec association.'))

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
