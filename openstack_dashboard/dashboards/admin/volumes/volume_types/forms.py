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

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import cinder


class CreateVolumeTypeEncryption(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), required=False,
                           widget=forms.TextInput(attrs={'readonly':
                                                         'readonly'}))
    provider = forms.CharField(max_length=255, label=_("Provider"))
    control_location = forms.ChoiceField(label=_("Control Location"),
                                         choices=(('front-end',
                                                   _('front-end')),
                                                  ('back-end',
                                                   _('back-end')))
                                         )
    cipher = forms.CharField(label=_("Cipher"), required=False)
    key_size = forms.IntegerField(label=_("Key Size (bits)"),
                                  required=False,
                                  min_value=1)
    volume_type_id = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            # Set Cipher to None if empty
            if data['cipher'] is u'':
                data['cipher'] = None

            # Create encyrption for the volume type
            volume_type = cinder.\
                volume_encryption_type_create(request,
                                              data['volume_type_id'],
                                              data)
            messages.success(request, _('Successfully created encryption for '
                                        'volume type: %s') % data['name'])
            return volume_type
        except Exception:
            redirect = reverse("horizon:admin:volumes:index")
            exceptions.handle(request,
                              _('Unable to create encrypted volume type.'),
                              redirect=redirect)


class ManageQosSpecAssociation(forms.SelfHandlingForm):
    qos_spec_choice = forms.ChoiceField(
        label=_("QoS Spec to be associated"),
        help_text=_("Choose associated QoS Spec."))

    def __init__(self, request, *args, **kwargs):
        super(ManageQosSpecAssociation, self).__init__(request,
                                                       *args,
                                                       **kwargs)
        qos_spec_field = self.fields['qos_spec_choice']
        qos_spec_field.choices = \
            self.populate_qos_spec_choices()

        # pre-select the current qos spec, if exists
        # if no association exists, the selected entry will be "None"
        # since it is index 0 of the choice box
        current_qos_spec = self.initial["cur_qos_spec_id"]
        if current_qos_spec:
            qos_spec_field.initial = current_qos_spec

    def populate_qos_spec_choices(self):
        # populate qos spec list box
        qos_specs = self.initial["qos_specs"]
        qos_spec_list = [(qos_spec.id, qos_spec.name)
                         for qos_spec in qos_specs]

        # 'none' is always listed first
        qos_spec_list.insert(0, ("-1", _("None")))
        return qos_spec_list

    def clean_qos_spec_choice(self):
        # ensure that new association isn't the same as current association
        cleaned_new_spec_id = self.cleaned_data.get('qos_spec_choice')
        cur_spec_id = self.initial['cur_qos_spec_id']

        found_error = False
        if cur_spec_id:
            # new = current
            if cur_spec_id == cleaned_new_spec_id:
                found_error = True
        else:
            # no current association
            if cleaned_new_spec_id == '-1':
                # new = current
                found_error = True

        if found_error:
            raise forms.ValidationError(
                _('New associated QoS Spec must be different than '
                  'the current associated QoS Spec.'))
        return cleaned_new_spec_id

    def handle(self, request, data):
        vol_type_id = self.initial['type_id']
        new_qos_spec_id = data['qos_spec_choice']

        # Update QOS Spec association information
        try:
            # NOTE - volume types can only be associated with
            #        ONE QOS Spec at a time

            # first we need to un-associate the current QOS Spec, if it exists
            cur_qos_spec_id = self.initial['cur_qos_spec_id']
            if cur_qos_spec_id:
                qos_spec = cinder.qos_spec_get(request,
                                               cur_qos_spec_id)
                cinder.qos_spec_disassociate(request,
                                             qos_spec,
                                             vol_type_id)

            # now associate with new QOS Spec, if user wants one associated
            if new_qos_spec_id != '-1':
                qos_spec = cinder.qos_spec_get(request,
                                               new_qos_spec_id)

                cinder.qos_spec_associate(request,
                                          qos_spec,
                                          vol_type_id)

            messages.success(request,
                             _('Successfully updated QoS Spec association.'))
            return True
        except Exception:
            redirect = reverse("horizon:admin:volumes:index")
            exceptions.handle(request,
                              _('Error updating QoS Spec association.'),
                              redirect=redirect)


class EditQosSpecConsumer(forms.SelfHandlingForm):
    consumer_choice = forms.ChoiceField(
        label=_("QoS Spec Consumer"),
        choices=cinder.CONSUMER_CHOICES,
        help_text=_("Choose consumer for this QoS Spec."))

    def __init__(self, request, *args, **kwargs):
        super(EditQosSpecConsumer, self).__init__(request, *args, **kwargs)
        consumer_field = self.fields['consumer_choice']
        qos_spec = self.initial["qos_spec"]
        consumer_field.initial = qos_spec.consumer

    def clean_consumer_choice(self):
        # ensure that new consumer isn't the same as current consumer
        qos_spec = self.initial['qos_spec']
        cleaned_new_consumer = self.cleaned_data.get('consumer_choice')
        old_consumer = qos_spec.consumer

        if cleaned_new_consumer == old_consumer:
            raise forms.ValidationError(
                _('QoS Spec consumer value must be different than '
                  'the current consumer value.'))
        return cleaned_new_consumer

    def handle(self, request, data):
        qos_spec_id = self.initial['qos_spec_id']
        new_consumer = data['consumer_choice']

        # Update QOS Spec consumer information
        try:
            cinder.qos_spec_set_keys(request,
                                     qos_spec_id,
                                     {'consumer': new_consumer})
            messages.success(request,
                             _('Successfully modified QoS Spec consumer.'))
            return True
        except Exception:
            redirect = reverse("horizon:admin:volumes:index")
            exceptions.handle(request, _('Error editing QoS Spec consumer.'),
                              redirect=redirect)
