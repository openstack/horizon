# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

"""
Views for managing api.quantum_api(request) network ports.
"""
import logging

from django import http
from django import shortcuts
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from django_openstack import forms
from django_openstack import api


LOG = logging.getLogger('django_openstack.dash.views.ports')


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
            messages.error(request,
                _('Unable to create ports on network %(network)s: %(msg)s') %
                {"network": data['network'], "msg": e.message})
        else:
            msg = _('%(num_ports)s ports created on network %(network)s.') % {
                  "num_ports": data['ports_num'], "network": data['network']}
            LOG.info(msg)
            messages.success(request, msg)

        return shortcuts.redirect(request.build_absolute_uri())


class DeletePort(forms.SelfHandlingForm):
    network = forms.CharField(widget=forms.HiddenInput())
    port = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            LOG.info('Deleting %s ports on network %s' %
                     (data['port'], data['network']))
            api.quantum_delete_port(request, data['network'], data['port'])
        except Exception, e:
            messages.error(request,
                           _('Unable to delete port %(port)s: %(msg)s') %
                           {"port": data['port'], "msg": e.message})
        else:
            msg = _('Port %(port)s deleted from network %(network)s.') % {
                  "port": data['port'], "network": data['network']}
            LOG.info(msg)
            messages.success(request, msg)
        return shortcuts.redirect(request.build_absolute_uri())


class AttachPort(forms.SelfHandlingForm):
    network = forms.CharField(widget=forms.HiddenInput())
    port = forms.CharField(widget=forms.HiddenInput())
    vif_id = forms.CharField(widget=forms.Select(),
                             label=_("Select VIF to connect"))

    def handle(self, request, data):
        try:
            LOG.info('Attaching %s port to VIF %s' %
                     (data['port'], data['vif_id']))
            body = {'attachment': {'id': '%s' % data['vif_id']}}
            api.quantum_attach_port(request,
                                        data['network'], data['port'], body)
        except Exception, e:
            messages.error(request,
                _('Unable to attach port %(port)s to VIF %(vif)s: %(msg)s') %
                {"port": data['port'],
                 "vif": data['vif_id'],
                 "msg": e.message})
        else:
            msg = _('Port %(port)s connected to VIF %(vif)s.') % \
                  {"port": data['port'], "vif": data['vif_id']}
            LOG.info(msg)
            messages.success(request, msg)
        return shortcuts.redirect(request.build_absolute_uri())


class DetachPort(forms.SelfHandlingForm):
    network = forms.CharField(widget=forms.HiddenInput())
    port = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            LOG.info('Detaching port %s' % data['port'])
            api.quantum_detach_port(request, data['network'], data['port'])
        except Exception, e:
            messages.error(request,
                _('Unable to detach port %(port)s: %(message)s') %
                {"port": data['port'], "message": e.message})
        else:
            msg = _('Port %s detached.') % (data['port'])
            LOG.info(msg)
            messages.success(request, msg)
        return shortcuts.redirect(request.build_absolute_uri())


class TogglePort(forms.SelfHandlingForm):
    network = forms.CharField(widget=forms.HiddenInput())
    port = forms.CharField(widget=forms.HiddenInput())
    state = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            LOG.info('Toggling port state to %s' % data['state'])
            body = {'port': {'state': '%s' % data['state']}}
            api.quantum_set_port_state(request,
                                       data['network'], data['port'], body)
        except Exception, e:
            messages.error(request,
                _('Unable to set port state to %(state)s: %(message)s') %
                {"state": data['state'], "message": e.message})
        else:
            msg = _('Port %(port)s state set to %(state)s.') % {
                "port": data['port'], "state": data['state']}
            LOG.info(msg)
            messages.success(request, msg)
        return shortcuts.redirect(request.build_absolute_uri())


@login_required
def create(request, tenant_id, network_id):
    create_form, handled = CreatePort.maybe_handle(request)

    if handled:
        return shortcuts.redirect(
            'dash_networks_detail',
            tenant_id=request.user.tenant_id,
            network_id=network_id
        )

    return shortcuts.render_to_response(
    'django_openstack/dash/ports/create.html', {
        'network_id': network_id,
        'create_form': create_form
    }, context_instance=template.RequestContext(request))


@login_required
def attach(request, tenant_id, network_id, port_id):
    attach_form, handled = AttachPort.maybe_handle(request)

    if handled:
        return shortcuts.redirect('dash_networks_detail',
                                  request.user.tenant_id, network_id)

    # Get all avaliable vifs
    vifs = _get_available_vifs(request)

    return shortcuts.render_to_response(
    'django_openstack/dash/ports/attach.html', {
        'network': network_id,
        'port': port_id,
        'attach_form': attach_form,
        'vifs': vifs,
    }, context_instance=template.RequestContext(request))


def _get_available_vifs(request):
    """
    Method to get a list of available virtual interfaces
    """
    vif_choices = []
    vifs = api.get_vif_ids(request)

    for vif in vifs:
        if vif['available']:
            name = "Instance %s VIF %s" % \
                   (str(vif['instance_name']), str(vif['id']))
            vif_choices.append({
                'name': str(name),
                'id': str(vif['id'])
            })

    return vif_choices
