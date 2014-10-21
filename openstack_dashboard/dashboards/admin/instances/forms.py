# Copyright 2013 Kylin OS, Inc
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
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


class LiveMigrateForm(forms.SelfHandlingForm):
    current_host = forms.CharField(label=_("Current Host"),
                                   required=False,
                                   widget=forms.TextInput(
                                       attrs={'readonly': 'readonly'}))
    host = forms.ChoiceField(label=_("New Host"),
                             help_text=_("Choose a Host to migrate to."))
    disk_over_commit = forms.BooleanField(label=_("Disk Over Commit"),
                                          initial=False, required=False)
    block_migration = forms.BooleanField(label=_("Block Migration"),
                                         initial=False, required=False)

    def __init__(self, request, *args, **kwargs):
        super(LiveMigrateForm, self).__init__(request, *args, **kwargs)
        initial = kwargs.get('initial', {})
        instance_id = initial.get('instance_id')
        self.fields['instance_id'] = forms.CharField(widget=forms.HiddenInput,
                                                     initial=instance_id)
        self.fields['host'].choices = self.populate_host_choices(request,
                                                                 initial)

    def populate_host_choices(self, request, initial):
        hosts = initial.get('hosts')
        current_host = initial.get('current_host')
        host_list = [(host.host_name,
                      host.host_name)
                     for host in hosts
                     if (host.service.startswith('compute') and
                         host.host_name != current_host)]
        if host_list:
            host_list.insert(0, ("", _("Select a new host")))
        else:
            host_list.insert(0, ("", _("No other hosts available.")))
        return sorted(host_list)

    def handle(self, request, data):
        try:
            block_migration = data['block_migration']
            disk_over_commit = data['disk_over_commit']
            api.nova.server_live_migrate(request,
                                         data['instance_id'],
                                         data['host'],
                                         block_migration=block_migration,
                                         disk_over_commit=disk_over_commit)
            msg = _('The instance is preparing the live migration '
                    'to host "%s".') % data['host']
            messages.success(request, msg)
            return True
        except Exception:
            msg = _('Failed to live migrate instance to '
                    'host "%s".') % data['host']
            redirect = reverse('horizon:admin:instances:index')
            exceptions.handle(request, msg, redirect=redirect)
