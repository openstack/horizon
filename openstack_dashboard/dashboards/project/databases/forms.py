# Copyright 2014 Tesora Inc.
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

from django.core.urlresolvers import reverse
from django.forms import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from openstack_dashboard import api


class ResizeVolumeForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    orig_size = forms.IntegerField(
        label=_("Current Size (GB)"),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
        required=False,
    )
    new_size = forms.IntegerField(label=_("New Size (GB)"))

    def clean(self):
        cleaned_data = super(ResizeVolumeForm, self).clean()
        new_size = cleaned_data.get('new_size')
        if new_size <= self.initial['orig_size']:
            raise ValidationError(
                _("New size for volume must be greater than current size."))

        return cleaned_data

    def handle(self, request, data):
        instance = data.get('instance_id')
        try:
            api.trove.instance_resize_volume(request,
                                             instance,
                                             data['new_size'])

            messages.success(request, _('Resizing volume "%s"') % instance)
        except Exception as e:
            redirect = reverse("horizon:project:databases:index")
            exceptions.handle(request, _('Unable to resize volume. %s') %
                              e.message, redirect=redirect)
        return True


class ResizeInstanceForm(forms.SelfHandlingForm):
    instance_id = forms.CharField(widget=forms.HiddenInput())
    old_flavor_name = forms.CharField(label=_("Old Flavor"),
                                      required=False,
                                      widget=forms.TextInput(
                                      attrs={'readonly': 'readonly'}))
    new_flavor = forms.ChoiceField(label=_("New Flavor"),
                                   help_text=_("Choose a new instance "
                                               "flavor."))

    def __init__(self, request, *args, **kwargs):
        super(ResizeInstanceForm, self).__init__(request, *args, **kwargs)

        old_flavor_id = kwargs.get('initial', {}).get('old_flavor_id')
        choices = kwargs.get('initial', {}).get('flavors')
        # Remove current flavor from the list of flavor choices
        choices = [(flavor_id, name) for (flavor_id, name) in choices
                   if flavor_id != old_flavor_id]
        if choices:
            choices.insert(0, ("", _("Select a new flavor")))
        else:
            choices.insert(0, ("", _("No flavors available")))
        self.fields['new_flavor'].choices = choices

    def handle(self, request, data):
        instance = data.get('instance_id')
        flavor = data.get('new_flavor')
        try:
            api.trove.instance_resize(request, instance, flavor)

            messages.success(request, _('Resizing instance "%s"') % instance)
        except Exception as e:
            redirect = reverse("horizon:project:databases:index")
            exceptions.handle(request, _('Unable to resize instance. %s') %
                              e.message, redirect=redirect)
        return True
