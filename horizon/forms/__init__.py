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
from django.forms import *  # noqa
from django.forms import widgets

# Convenience imports for public API components.
from horizon.forms.base import DateForm  # noqa
from horizon.forms.base import SelfHandlingForm  # noqa
from horizon.forms.base import SelfHandlingMixin  # noqa
from horizon.forms.fields import DynamicChoiceField  # noqa
from horizon.forms.fields import DynamicTypedChoiceField  # noqa
from horizon.forms.views import ModalFormMixin  # noqa
from horizon.forms.views import ModalFormView  # noqa

assert widgets
assert SelfHandlingMixin
assert SelfHandlingForm
assert DateForm
assert ModalFormView
assert ModalFormMixin
assert DynamicTypedChoiceField
assert DynamicChoiceField
