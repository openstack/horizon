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

from glanceclient import exc

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


def str2bool(value):
    """Convert a string value to boolean
    """
    return value.lower() in ("yes", "true", "1")


# Mapping of property names to type, used for converting input string value
# before submitting.
PROPERTY_TYPES = {'min_disk': long, 'min_ram': long, 'protected': str2bool}


def convert_value(key, value):
    """Convert the property value to the proper type if necessary.
    """
    _type = PROPERTY_TYPES.get(key)
    if _type:
        return _type(value)
    return value


class CreateProperty(forms.SelfHandlingForm):
    key = forms.CharField(max_length="255", label=_("Key"))
    value = forms.CharField(label=_("Value"))

    def handle(self, request, data):
        try:
            api.glance.image_update_properties(request,
                self.initial['image_id'],
                **{data['key']: convert_value(data['key'], data['value'])})
            msg = _('Created custom property "%s".') % data['key']
            messages.success(request, msg)
            return True
        except exc.HTTPForbidden:
            msg = _('Unable to create image custom property. Property "%s" '
                    'is read only.') % data['key']
            exceptions.handle(request, msg)
        except exc.HTTPConflict:
            msg = _('Unable to create image custom property. Property "%s" '
                    'already exists.') % data['key']
            exceptions.handle(request, msg)
        except Exception:
            msg = _('Unable to create image custom '
                    'property "%s".') % data['key']
            exceptions.handle(request, msg)


class EditProperty(forms.SelfHandlingForm):
    key = forms.CharField(widget=forms.widgets.HiddenInput)
    value = forms.CharField(label=_("Value"))

    def handle(self, request, data):
        try:
            api.glance.image_update_properties(request,
                self.initial['image_id'],
                **{data['key']: convert_value(data['key'], data['value'])})
            msg = _('Saved custom property "%s".') % data['key']
            messages.success(request, msg)
            return True
        except exc.HTTPForbidden:
            msg = _('Unable to edit image custom property. Property "%s" '
                    'is read only.') % data['key']
            exceptions.handle(request, msg)
        except Exception:
            msg = _('Unable to edit image custom '
                    'property "%s".') % data['key']
            exceptions.handle(request, msg)
