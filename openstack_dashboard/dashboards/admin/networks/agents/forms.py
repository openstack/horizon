# Copyright 2014 Kylincloud
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


class AddDHCPAgent(forms.SelfHandlingForm):
    network_id = forms.CharField(widget=forms.HiddenInput())
    network_name = forms.CharField(label=_("Network Name"),
                                   widget=forms.TextInput(
                                   attrs={'readonly': 'readonly'}))
    agent = forms.ThemableChoiceField(
        label=_("New DHCP Agent"),
        help_text=_("Choose an DHCP Agent to attach to."))

    def __init__(self, request, *args, **kwargs):
        super(AddDHCPAgent, self).__init__(request, *args, **kwargs)
        initial = kwargs.get('initial', {})
        self.fields['agent'].choices = self._populate_agent_choices(request,
                                                                    initial)

    def _populate_agent_choices(self, request, initial):
        network_id = initial.get('network_id')
        agents = initial.get('agents')
        try:
            exist_agents = [agent.id for agent in
                            api.neutron.list_dhcp_agent_hosting_networks(
                                request, network_id)]
            agent_list = [(agent.id, agent.host) for agent in agents
                          if agent.id not in exist_agents]
            if agent_list:
                agent_list.insert(0, ("", _("Select a new agent")))
            else:
                agent_list.insert(0, ("", _("No other agents available.")))
            return agent_list
        except Exception:
            redirect = reverse('horizon:admin:networks:detail',
                               args=(network_id,))
            msg = _('Unable to list dhcp agents hosting network.')
            exceptions.handle(request, msg, redirect=redirect)

    def handle(self, request, data):
        # Get the agent name for message
        agent_name = data['agent']
        for choice in self.fields['agent'].choices:
            if choice[0] == data['agent']:
                agent_name = choice[1]
        try:
            api.neutron.add_network_to_dhcp_agent(request, data['agent'],
                                                  data['network_id'])
            msg = _('Agent %s was successfully added.') % agent_name
            messages.success(request, msg)
            return True
        except Exception:
            redirect = reverse('horizon:admin:networks:detail',
                               args=(data['network_id'],))
            msg = _('Failed to add agent %(agent_name)s for '
                    'network %(network)s.') \
                % {'agent_name': agent_name,
                   'network': data['network_name']}
            exceptions.handle(request, msg, redirect=redirect)
