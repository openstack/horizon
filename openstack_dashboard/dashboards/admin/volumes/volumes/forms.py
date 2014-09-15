# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import cinder


class CreateVolumeType(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Name"))

    def handle(self, request, data):
        try:
            # Remove any new lines in the public key
            volume_type = cinder.volume_type_create(request,
                                                    data['name'])
            messages.success(request, _('Successfully created volume type: %s')
                                      % data['name'])
            return volume_type
        except Exception:
            exceptions.handle(request,
                              _('Unable to create volume type.'))
            return False


class UpdateStatus(forms.SelfHandlingForm):
    status = forms.ChoiceField(label=_("Status"))

    def __init__(self, request, *args, **kwargs):
        super(forms.SelfHandlingForm, self).__init__(request, *args, **kwargs)

        # This set of states was culled from cinder's admin_actions.py
        self.fields['status'].choices = (
            ('attaching', _('Attaching')),
            ('available', _('Available')),
            ('creating', _('Creating')),
            ('deleting', _('Deleting')),
            ('detaching', _('Detaching')),
            ('error', _('Error')),
            ('error_deleting', _('Error Deleting')),
            ('in-use', _('In Use')),
        )

    def handle(self, request, data):
        # Obtain the localized status for including in the message
        for choice in self.fields['status'].choices:
            if choice[0] == data['status']:
                new_status = choice[1]
                break
        else:
            new_status = data['status']

        try:
            cinder.volume_reset_state(request,
                                      self.initial['volume_id'],
                                      data['status'])
            messages.success(request,
                             _('Successfully updated volume status to "%s".') %
                             new_status)
            return True
        except Exception:
            exceptions.handle(request,
                              _('Unable to update volume status to "%s".') %
                             new_status)
            return False


class CreateQosSpec(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Name"))
    consumer = forms.ChoiceField(label=_("Consumer"),
                                 choices=cinder.CONSUMER_CHOICES)

    def handle(self, request, data):
        try:
            qos_spec = cinder.qos_spec_create(request,
                                              data['name'],
                                              {'consumer': data['consumer']})
            messages.success(request, _('Successfully created QOS Spec: %s')
                                      % data['name'])
            return qos_spec
        except Exception:
            exceptions.handle(request,
                              _('Unable to create QOS Spec.'))
            return False