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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


class EditQosSpec(forms.SelfHandlingForm):
    value = forms.CharField(max_length=255, label=_("Value"))

    # update the backend with the new qos spec value
    def handle(self, request, data):
        key = self.initial['key']
        qos_spec_id = self.initial['qos_spec_id']

        # build up new 'specs' object with all previous values plus new value
        try:
            # first retrieve current value of specs
            specs = api.cinder.qos_spec_get_keys(request,
                                                 qos_spec_id,
                                                 raw=True)
            specs.specs[key] = data['value']
            api.cinder.qos_spec_set_keys(request,
                                         qos_spec_id,
                                         specs.specs)
            msg = _('Saved spec "%s".') % key
            messages.success(request, msg)
            return True
        except Exception:
            exceptions.handle(request,
                              _("Unable to edit spec."))
            return False