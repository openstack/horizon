# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

import logging

from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import forms


LOG = logging.getLogger(__name__)


class CreateNetwork(forms.SelfHandlingForm):
    name = forms.CharField(required=True, label=_("Network Name"))

    def handle(self, request, data):
        network_name = data['name']
        try:
            data = {'network': {'name': network_name}}
            api.quantum.quantum_create_network(request, data)
            messages.success(request,
                             _('Network %s has been created.') % network_name)
        except:
            exceptions.handle(request, _("Unable to create network."))
        return shortcuts.redirect('horizon:nova:networks:index')


class RenameNetwork(forms.SelfHandlingForm):
    network = forms.CharField(widget=forms.HiddenInput())
    new_name = forms.CharField(required=True)

    def handle(self, request, data):
        try:
            LOG.info('Renaming network %s to %s' %
                     (data['network'], data['new_name']))
            send_data = {'network': {'name': '%s' % data['new_name']}}
            api.quantum_update_network(request, data['network'], send_data)
        except Exception, e:
            if not hasattr(e, 'message'):
                e.message = str(e)
            messages.error(request,
                    _('Unable to rename network %(network)s: %(msg)s') %
                    {"network": data['network'], "msg": e.message})
        else:
            msg = _('Network %(net)s has been renamed to %(new_name)s.') % {
                  "net": data['network'], "new_name": data['new_name']}
            LOG.info(msg)
            messages.success(request, msg)

        return shortcuts.redirect('horizon:nova:networks:index')


class CreatePort(forms.SelfHandlingForm):
    network = forms.CharField(widget=forms.HiddenInput())
    ports_num = forms.IntegerField(required=True, label=_("Number of Ports"))

    def handle(self, request, data):
        try:
            LOG.info('Creating %s ports on network %s' %
                     (data['ports_num'], data['network']))
            for i in range(0, data['ports_num']):
                api.quantum_create_port(request, data['network'])
        except Exception, e:
            if not hasattr(e, 'message'):
                e.message = str(e)
            messages.error(request,
                _('Unable to create ports on network %(network)s: %(msg)s') %
                {"network": data['network'], "msg": e.message})
        else:
            msg = _('%(num_ports)s ports created on network %(network)s.') % {
                  "num_ports": data['ports_num'], "network": data['network']}
            LOG.info(msg)
            messages.success(request, msg)

        return shortcuts.redirect('horizon:nova:networks:detail',
                                  network_id=data['network'])


class AttachPort(forms.SelfHandlingForm):
    network = forms.CharField(widget=forms.HiddenInput())
    port = forms.CharField(widget=forms.HiddenInput())
    vif_id = forms.ChoiceField(label=_("Select VIF to connect"))

    def __init__(self, request, *args, **kwargs):
        super(AttachPort, self).__init__(*args, **kwargs)
        # Populate VIF choices
        vif_choices = [('', "Select a VIF")]
        for vif in api.get_vif_ids(request):
            if vif['available']:
                name = "Instance %s VIF %s" % (vif['instance_name'], vif['id'])
                vif_choices.append((vif['id'], name,))
        self.fields['vif_id'].choices = vif_choices

    @classmethod
    def _instantiate(cls, request, *args, **kwargs):
        return cls(request, *args, **kwargs)

    def handle(self, request, data):
        try:
            body = {'attachment': {'id': '%s' % data['vif_id']}}
            api.quantum_attach_port(request,
                                    data['network'],
                                    data['port'],
                                    body)
            messages.success(request, _("Port attached."))
        except:
            exceptions.handle(request, _('Unable to attach port.'))
        return shortcuts.redirect("horizon:nova:networks:detail",
                                  data['network'])
