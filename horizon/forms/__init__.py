# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

# FIXME(gabriel): Legacy imports for API compatibility.
from django.forms import *
from django.forms import widgets

# Convenience imports for public API components.
from horizon.forms.base import DateForm
from horizon.forms.base import SelfHandlingForm
from horizon.forms.base import SelfHandlingMixin
from horizon.forms.fields import DynamicChoiceField
from horizon.forms.fields import DynamicTypedChoiceField
from horizon.forms.views import ModalFormMixin
from horizon.forms.views import ModalFormView

assert widgets
assert SelfHandlingMixin
assert SelfHandlingForm
assert DateForm
assert ModalFormView
assert ModalFormMixin
assert DynamicTypedChoiceField
assert DynamicChoiceField
