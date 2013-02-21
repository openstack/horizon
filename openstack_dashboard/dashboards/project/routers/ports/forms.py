# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
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

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import messages
from horizon import exceptions
from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class AddInterface(forms.SelfHandlingForm):
    subnet_id = forms.ChoiceField(label=_("Subnet"), required=False)
    router_name = forms.CharField(label=_("Router Name"),
                                  widget=forms.TextInput(
                                      attrs={'readonly': 'readonly'}))
    router_id = forms.CharField(label=_("Router ID"),
                                widget=forms.TextInput(
                                    attrs={'readonly': 'readonly'}))
    failure_url = 'horizon:project:routers:detail'

    def __init__(self, request, *args, **kwargs):
        super(AddInterface, self).__init__(request, *args, **kwargs)
        c = self.populate_subnet_id_choices(request)
        self.fields['subnet_id'].choices = c

    def populate_subnet_id_choices(self, request):
        tenant_id = self.request.user.tenant_id
        networks = []
        try:
            networks = api.quantum.network_list_for_tenant(request, tenant_id)
        except Exception as e:
            msg = _('Failed to get network list %s') % e.message
            LOG.info(msg)
            messages.error(request, msg)
            redirect = reverse(self.failure_url,
                               args=[request.REQUEST['router_id']])
            exceptions.handle(request, msg, redirect=redirect)
            return

        choices = []
        for n in networks:
            net_name = n.name + ': ' if n.name else ''
            choices += [(subnet.id,
                         '%s%s (%s)' % (net_name, subnet.cidr,
                                        subnet.name or subnet.id))
                        for subnet in n['subnets']]
        if choices:
            choices.insert(0, ("", _("Select Subnet")))
        else:
            choices.insert(0, ("", _("No subnets available.")))
        return choices

    def handle(self, request, data):
        try:
            api.quantum.router_add_interface(request,
                                             data['router_id'],
                                             subnet_id=data['subnet_id'])
            msg = _('Interface added')
            LOG.debug(msg)
            messages.success(request, msg)
            return True
        except Exception as e:
            msg = _('Failed to add_interface %s') % e.message
            LOG.info(msg)
            messages.error(request, msg)
            redirect = reverse(self.failure_url, args=[data['router_id']])
            exceptions.handle(request, msg, redirect=redirect)


class SetGatewayForm(forms.SelfHandlingForm):
    network_id = forms.ChoiceField(label=_("External Network"), required=False)
    router_name = forms.CharField(label=_("Router Name"),
                                  widget=forms.TextInput(
                                      attrs={'readonly': 'readonly'}))
    router_id = forms.CharField(label=_("Router ID"),
                                widget=forms.TextInput(
                                    attrs={'readonly': 'readonly'}))
    failure_url = 'horizon:project:routers:index'

    def __init__(self, request, *args, **kwargs):
        super(SetGatewayForm, self).__init__(request, *args, **kwargs)
        c = self.populate_network_id_choices(request)
        self.fields['network_id'].choices = c

    def populate_network_id_choices(self, request):
        search_opts = {'router:external': True}
        try:
            networks = api.quantum.network_list(request, **search_opts)
        except Exception as e:
            msg = _('Failed to get network list %s') % e.message
            LOG.info(msg)
            messages.error(request, msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            return
        choices = [(network.id, network.name or network.id)
                   for network in networks]
        if choices:
            choices.insert(0, ("", _("Select network")))
        else:
            choices.insert(0, ("", _("No networks available.")))
        return choices

    def handle(self, request, data):
        try:
            api.quantum.router_add_gateway(request,
                                           data['router_id'],
                                           data['network_id'])
            msg = _('Gateway interface is added')
            LOG.debug(msg)
            messages.success(request, msg)
            return True
        except Exception as e:
            msg = _('Failed to set gateway %s') % e.message
            LOG.info(msg)
            messages.error(request, msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
