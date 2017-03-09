# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard import api

from horizon import exceptions
from horizon import forms
from horizon import messages


class CreateExtraSpec(forms.SelfHandlingForm):
    key = forms.CharField(max_length=255, label=_("Key"))
    value = forms.CharField(max_length=255, label=_("Value"))

    def handle(self, request, data):
        type_id = self.initial['type_id']
        try:
            api.cinder.volume_type_extra_set(request,
                                             type_id,
                                             {data['key']: data['value']})
            msg = _('Created extra spec "%s".') % data['key']
            messages.success(request, msg)
            return True
        except Exception:
            redirect = reverse("horizon:admin:volume_types:index")
            exceptions.handle(request,
                              _("Unable to create volume type extra spec."),
                              redirect=redirect)


class EditExtraSpec(forms.SelfHandlingForm):
    value = forms.CharField(max_length=255, label=_("Value"))

    def handle(self, request, data):
        key = self.initial['key']
        type_id = self.initial['type_id']
        try:
            api.cinder.volume_type_extra_set(request,
                                             type_id,
                                             {key: data['value']})
            msg = _('Saved extra spec "%s".') % key
            messages.success(request, msg)
            return True
        except Exception:
            redirect = reverse("horizon:admin:volume_types:index")
            exceptions.handle(request,
                              _("Unable to edit volume type extra spec."),
                              redirect=redirect)
