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
from django.core.exceptions import ValidationError  # noqa
from django.forms.fields import *  # noqa
from django.forms.forms import *  # noqa
from django.forms import widgets
from django.forms.widgets import *  # noqa


# Convenience imports for public API components.
from horizon.forms.base import DateForm  # noqa
from horizon.forms.base import SelfHandlingForm  # noqa
from horizon.forms.base import SelfHandlingMixin  # noqa
from horizon.forms.fields import DynamicChoiceField  # noqa
from horizon.forms.fields import DynamicTypedChoiceField  # noqa
from horizon.forms.fields import IPField  # noqa
from horizon.forms.fields import IPv4  # noqa
from horizon.forms.fields import IPv6  # noqa
from horizon.forms.fields import MultiIPField  # noqa
from horizon.forms.fields import SelectWidget  # noqa
from horizon.forms.views import ModalFormMixin  # noqa
from horizon.forms.views import ModalFormView  # noqa


__all__ = [
    "SelfHandlingMixin",
    "SelfHandlingForm",
    "DateForm",
    "ModalFormView",
    "ModalFormMixin",
    "DynamicTypedChoiceField",
    "DynamicChoiceField",
    "IPField",
    "IPv4",
    "IPv6",
    "MultiIPField",
    "SelectWidget"

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
