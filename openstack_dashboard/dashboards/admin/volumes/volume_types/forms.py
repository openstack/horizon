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
from django.forms import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import cinder


class CreateVolumeType(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Name"))
    vol_type_description = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={'rows': 4}),
        label=_("Description"),
        required=False)

    def clean_name(self):
        cleaned_name = self.cleaned_data['name']
        if len(cleaned_name.strip()) == 0:
            raise ValidationError(_('Volume type name can not be empty.'))

        return cleaned_name

    def handle(self, request, data):
        try:
            # Remove any new lines in the public key
            volume_type = cinder.volume_type_create(
                request,
                data['name'],
                data['vol_type_description'])
            messages.success(request, _('Successfully created volume type: %s')
                             % data['name'])
            return volume_type
        except Exception as e:
            if getattr(e, 'code', None) == 409:
                msg = _('Volume type name "%s" already '
                        'exists.') % data['name']
                self._errors['name'] = self.error_class([msg])
            else:
                redirect = reverse("horizon:admin:volumes:index")
                exceptions.handle(request,
                                  _('Unable to create volume type.'),
                                  redirect=redirect)


class CreateQosSpec(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Name"))
    consumer = forms.ChoiceField(label=_("Consumer"),
                                 choices=cinder.CONSUMER_CHOICES)

    def handle(self, request, data):
        try:
            qos_spec = cinder.qos_spec_create(request,
                                              data['name'],
                                              {'consumer': data['consumer']})
            messages.success(request,
                             _('Successfully created QoS Spec: %s')
                             % data['name'])
            return qos_spec
        except Exception as ex:
            if getattr(ex, 'code', None) == 409:
                msg = _('QoS Spec name "%s" already '
                        'exists.') % data['name']
                self._errors['name'] = self.error_class([msg])
            else:
                redirect = reverse("horizon:admin:volumes:index")
                exceptions.handle(request,
                                  _('Unable to create QoS Spec.'),
                                  redirect=redirect)


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
            if data['cipher'] == u'':
                data['cipher'] = None

            # Create encryption for the volume type
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


class UpdateVolumeTypeEncryption(CreateVolumeTypeEncryption):

    def handle(self, request, data):
        try:
            # Set Cipher to None if empty
            if data['cipher'] == u'':
                data['cipher'] = None

            # Update encryption for the volume type
            volume_type = cinder.\
                volume_encryption_type_update(request,
                                              data['volume_type_id'],
                                              data)
            messages.success(request, _('Successfully updated encryption for '
                                        'volume type: %s') % data['name'])
            return volume_type
        except NotImplementedError:
            messages.error(request, _('Updating encryption is not '
                                      'implemented.  Unable to update '
                                      ' encrypted volume type.'))
        except Exception:
            redirect = reverse("horizon:admin:volumes:index")
            exceptions.handle(request,
                              _('Unable to update encrypted volume type.'),
                              redirect=redirect)
        return False


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

    def populate_qos_spec_choices(self):
        # populate qos spec list box
        qos_specs = self.initial["qos_specs"]
        current_qos_spec = self.initial["cur_qos_spec_id"]
        qos_spec_list = [(qos_spec.id, qos_spec.name)
                         for qos_spec in qos_specs
                         if qos_spec.id != current_qos_spec]

        if current_qos_spec:
            # used to remove the current spec
            qos_spec_list.insert(0, ("-1", _("None (removes spec)")))
        if qos_spec_list:
            qos_spec_list.insert(0, ("", _("Select a new QoS spec")))
        else:
            qos_spec_list.insert(0, ("", _("No new QoS spec available")))
        return qos_spec_list

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
    current_consumer = forms.CharField(label=_("Current consumer"),
                                       widget=forms.TextInput(
                                       attrs={'readonly': 'readonly'}),
                                       required=False)
    consumer_choice = forms.ChoiceField(
        label=_("New QoS Spec Consumer"),
        choices=cinder.CONSUMER_CHOICES,
        help_text=_("Choose consumer for this QoS Spec."))

    def __init__(self, request, *args, **kwargs):
        super(EditQosSpecConsumer, self).__init__(request, *args, **kwargs)
        consumer_field = self.fields['consumer_choice']
        qos_spec = self.initial["qos_spec"]
        self.fields['current_consumer'].initial = qos_spec.consumer
        choices = [choice for choice in cinder.CONSUMER_CHOICES
                   if choice[0] != qos_spec.consumer]
        choices.insert(0, ("", _("Select a new consumer")))
        consumer_field.choices = choices

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


class EditVolumeType(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255,
                           label=_("Name"))
    description = forms.CharField(max_length=255,
                                  widget=forms.Textarea(attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)

    def clean_name(self):
        cleaned_name = self.cleaned_data['name']
        if len(cleaned_name.strip()) == 0:
            msg = _('New name cannot be empty.')
            self._errors['name'] = self.error_class([msg])

        return cleaned_name

    def handle(self, request, data):
        volume_type_id = self.initial['id']
        try:
            cinder.volume_type_update(request,
                                      volume_type_id,
                                      data['name'],
                                      data['description'])
            message = _('Successfully updated volume type.')
            messages.success(request, message)
            return True
        except Exception as ex:
            redirect = reverse("horizon:admin:volumes:index")
            if ex.code == 409:
                error_message = _('New name conflicts with another '
                                  'volume type.')
            else:
                error_message = _('Unable to update volume type.')

            exceptions.handle(request, error_message,
                              redirect=redirect)
