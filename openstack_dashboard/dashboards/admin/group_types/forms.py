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

from django.forms import ValidationError
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import cinder


class CreateGroupType(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Name"))
    group_type_description = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={'rows': 4}),
        label=_("Description"),
        required=False)
    is_public = forms.BooleanField(
        label=_("Public"),
        initial=True,
        required=False,
        help_text=_("By default, group type is created as public. To "
                    "create a private group type, uncheck this field."))

    def clean_name(self):
        cleaned_name = self.cleaned_data['name']
        if cleaned_name.isspace():
            raise ValidationError(_('Group type name can not be empty.'))

        return cleaned_name

    def handle(self, request, data):
        try:
            group_type = cinder.group_type_create(
                request,
                data['name'],
                data['group_type_description'],
                data['is_public'])
            messages.success(request, _('Successfully created group type: %s')
                             % data['name'])
            return group_type
        except Exception as e:
            if getattr(e, 'code', None) == 409:
                msg = _('Group type name "%s" already '
                        'exists.') % data['name']
                self._errors['name'] = self.error_class([msg])
            else:
                redirect = reverse("horizon:admin:group_types:index")
                exceptions.handle(request,
                                  _('Unable to create group type.'),
                                  redirect=redirect)


class EditGroupType(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255,
                           label=_("Name"))
    description = forms.CharField(max_length=255,
                                  widget=forms.Textarea(attrs={'rows': 4}),
                                  label=_("Description"),
                                  required=False)
    is_public = forms.BooleanField(label=_("Public"), required=False,
                                   help_text=_(
                                       "To make group type private, uncheck "
                                       "this field."))

    def clean_name(self):
        cleaned_name = self.cleaned_data['name']
        if cleaned_name.isspace():
            msg = _('New name cannot be empty.')
            self._errors['name'] = self.error_class([msg])

        return cleaned_name

    def handle(self, request, data):
        group_type_id = self.initial['id']
        try:
            cinder.group_type_update(request,
                                     group_type_id,
                                     data['name'],
                                     data['description'],
                                     data['is_public'])
            message = _('Successfully updated group type.')
            messages.success(request, message)
            return True
        except Exception as ex:
            redirect = reverse("horizon:admin:group_types:index")
            if ex.code == 409:
                error_message = _('New name conflicts with another '
                                  'group type.')
            else:
                error_message = _('Unable to update group type.')

            exceptions.handle(request, error_message,
                              redirect=redirect)
