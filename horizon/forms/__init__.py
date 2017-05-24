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

# Importing non-modules that are not used explicitly

# FIXME(gabriel): Legacy imports for API compatibility.
from django.core.exceptions import ValidationError
from django.forms.fields import *  # noqa: F403,H303
from django.forms.forms import *  # noqa: F403,H303
from django.forms import widgets
from django.forms.widgets import *  # noqa: F403,H303


# Convenience imports for public API components.
from horizon.forms.base import DateForm
from horizon.forms.base import SelfHandlingForm
from horizon.forms.base import SelfHandlingMixin
from horizon.forms.fields import DynamicChoiceField
from horizon.forms.fields import DynamicTypedChoiceField
from horizon.forms.fields import ExternalFileField
from horizon.forms.fields import ExternalUploadMeta
from horizon.forms.fields import IPField
from horizon.forms.fields import IPv4
from horizon.forms.fields import IPv6
from horizon.forms.fields import MACAddressField
from horizon.forms.fields import MultiIPField
from horizon.forms.fields import SelectWidget
from horizon.forms.fields import ThemableCheckboxInput
from horizon.forms.fields import ThemableCheckboxSelectMultiple
from horizon.forms.fields import ThemableChoiceField
from horizon.forms.fields import ThemableDynamicChoiceField
from horizon.forms.fields import ThemableDynamicTypedChoiceField
from horizon.forms.fields import ThemableSelectWidget
from horizon.forms.views import ModalFormMixin
from horizon.forms.views import ModalFormView


__all__ = [
    "SelfHandlingMixin",
    "SelfHandlingForm",
    "DateForm",
    "ModalFormView",
    "ModalFormMixin",
    "DynamicTypedChoiceField",
    "DynamicChoiceField",
    "ExternalFileField",
    "ExternalUploadMeta",
    "ThemableCheckboxInput",
    "ThemableCheckboxSelectMultiple",
    "ThemableChoiceField",
    "ThemableDynamicChoiceField",
    "ThemableDynamicTypedChoiceField",
    "ThemableSelectWidget",
    "IPField",
    "IPv4",
    "IPv6",
    "MACAddressField",
    "MultiIPField",
    "SelectWidget",

    # From django.forms
    "ValidationError",

    # From django.forms.fields
    'Field', 'CharField', 'IntegerField', 'DateField', 'TimeField',
    'DateTimeField', 'TimeField', 'RegexField', 'EmailField', 'FileField',
    'ImageField', 'URLField', 'BooleanField', 'NullBooleanField',
    'ChoiceField', 'MultipleChoiceField', 'ComboField', 'MultiValueField',
    'FloatField', 'DecimalField', 'SplitDateTimeField', 'IPAddressField',
    'GenericIPAddressField', 'FilePathField', 'SlugField', 'TypedChoiceField',
    'TypedMultipleChoiceField',

    # From django.forms.widgets
    "widgets",
    'Media', 'MediaDefiningClass', 'Widget', 'TextInput', 'PasswordInput',
    'HiddenInput', 'MultipleHiddenInput', 'ClearableFileInput', 'FileInput',
    'DateInput', 'DateTimeInput', 'TimeInput', 'Textarea', 'CheckboxInput',
    'Select', 'NullBooleanSelect', 'SelectMultiple', 'RadioSelect',
    'CheckboxSelectMultiple', 'MultiWidget', 'SplitDateTimeWidget',

    # From django.forms.forms
    'BaseForm', 'Form',
]
