# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


class EvacuateHostForm(forms.SelfHandlingForm):

    current_host = forms.CharField(label=_("Current Host"),
                                   widget=forms.TextInput(
                                       attrs={'readonly': 'readonly'}))
    target_host = forms.ChoiceField(label=_("Target Host"),
                         help_text=_("Choose a Host to evacuate servers to."))

    on_shared_storage = forms.BooleanField(label=_("Shared Storage"),
                                          initial=False, required=False)

    def __init__(self, request, *args, **kwargs):
        super(EvacuateHostForm, self).__init__(request, *args, **kwargs)
        initial = kwargs.get('initial', {})
        self.fields['target_host'].choices = \
            self.populate_host_choices(request, initial)

    def populate_host_choices(self, request, initial):
        hosts = initial.get('hosts')
        current_host = initial.get('current_host')
        host_list = sorted([(host, host)
                            for host in hosts
                            if host != current_host])
        if host_list:
            host_list.insert(0, ("", _("Select a target host")))
        else:
            host_list.insert(0, ("", _("No other hosts available.")))
        return host_list

    def handle(self, request, data):
        try:
            current_host = data['current_host']
            target_host = data['target_host']
            on_shared_storage = data['on_shared_storage']
            api.nova.evacuate_host(request, current_host,
                                   target_host, on_shared_storage)

            msg = _('Starting evacuation from %(current)s to %(target)s.') % \
                {'current': current_host, 'target': target_host}
            messages.success(request, msg)
            return True
        except Exception:
            redirect = reverse('horizon:admin:hypervisors:index')
            msg = _('Failed to evacuate host: %s.') % data['current_host']
            exceptions.handle(request, message=msg, redirect=redirect)
            return False
