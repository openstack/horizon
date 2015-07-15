# Copyright 2012 NEC Corporation
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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


LOG = logging.getLogger(__name__)
PROVIDER_TYPES = [('local', _('Local')), ('flat', _('Flat')),
                  ('vlan', _('VLAN')), ('gre', _('GRE')),
                  ('vxlan', _('VXLAN'))]
SEGMENTATION_ID_RANGE = {'vlan': [1, 4094], 'gre': [0, (2 ** 32) - 1],
                         'vxlan': [0, (2 ** 24) - 1]}


class CreateNetwork(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False)
    tenant_id = forms.ChoiceField(label=_("Project"))
    network_type = forms.ChoiceField(
        label=_("Provider Network Type"),
        help_text=_("The physical mechanism by which the virtual "
                    "network is implemented."),
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'network_type'
        }))
    physical_network = forms.CharField(
        max_length=255,
        label=_("Physical Network"),
        help_text=_("The name of the physical network over which the "
                    "virtual network is implemented."),
        initial='default',
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'network_type',
            'data-network_type-flat': _('Physical Network'),
            'data-network_type-vlan': _('Physical Network')
        }))
    segmentation_id = forms.IntegerField(
        label=_("Segmentation ID"),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'network_type',
            'data-network_type-vlan': _('Segmentation ID'),
            'data-network_type-gre': _('Segmentation ID'),
            'data-network_type-vxlan': _('Segmentation ID')
        }))
    admin_state = forms.ChoiceField(choices=[(True, _('UP')),
                                             (False, _('DOWN'))],
                                    label=_("Admin State"))
    shared = forms.BooleanField(label=_("Shared"),
                                initial=False, required=False)
    external = forms.BooleanField(label=_("External Network"),
                                  initial=False, required=False)

    @classmethod
    def _instantiate(cls, request, *args, **kwargs):
        return cls(request, *args, **kwargs)

    def __init__(self, request, *args, **kwargs):
        super(CreateNetwork, self).__init__(request, *args, **kwargs)
        tenant_choices = [('', _("Select a project"))]
        tenants, has_more = api.keystone.tenant_list(request)
        for tenant in tenants:
            if tenant.enabled:
                tenant_choices.append((tenant.id, tenant.name))
        self.fields['tenant_id'].choices = tenant_choices

        if api.neutron.is_extension_supported(request, 'provider'):
            neutron_settings = getattr(settings,
                                       'OPENSTACK_NEUTRON_NETWORK', {})
            seg_id_range = neutron_settings.get('segmentation_id_range', {})
            self.seg_id_range = {
                'vlan': seg_id_range.get('vlan',
                                         SEGMENTATION_ID_RANGE.get('vlan')),
                'gre': seg_id_range.get('gre',
                                        SEGMENTATION_ID_RANGE.get('gre')),
                'vxlan': seg_id_range.get('vxlan',
                                          SEGMENTATION_ID_RANGE.get('vxlan'))
            }
            seg_id_help = (
                _("For VLAN networks, the VLAN VID on the physical "
                  "network that realizes the virtual network. Valid VLAN VIDs "
                  "are %(vlan_min)s through %(vlan_max)s. For GRE or VXLAN "
                  "networks, the tunnel ID. Valid tunnel IDs for GRE networks "
                  "are %(gre_min)s through %(gre_max)s. For VXLAN networks, "
                  "%(vxlan_min)s through %(vxlan_max)s.")
                % {'vlan_min': self.seg_id_range['vlan'][0],
                   'vlan_max': self.seg_id_range['vlan'][1],
                   'gre_min': self.seg_id_range['gre'][0],
                   'gre_max': self.seg_id_range['gre'][1],
                   'vxlan_min': self.seg_id_range['vxlan'][0],
                   'vxlan_max': self.seg_id_range['vxlan'][1]})
            self.fields['segmentation_id'].help_text = seg_id_help

            supported_provider_types = neutron_settings.get(
                'supported_provider_types', ['*'])
            if supported_provider_types == ['*']:
                network_type_choices = PROVIDER_TYPES
            else:
                network_type_choices = [
                    net_type for net_type in PROVIDER_TYPES
                    if net_type[0] in supported_provider_types]
            if len(network_type_choices) == 0:
                self._hide_provider_network_type()
            else:
                self.fields['network_type'].choices = network_type_choices
        else:
            self._hide_provider_network_type()

    def _hide_provider_network_type(self):
        self.fields['network_type'].widget = forms.HiddenInput()
        self.fields['physical_network'].widget = forms.HiddenInput()
        self.fields['segmentation_id'].widget = forms.HiddenInput()
        self.fields['network_type'].required = False
        self.fields['physical_network'].required = False
        self.fields['segmentation_id'].required = False

    def handle(self, request, data):
        try:
            params = {'name': data['name'],
                      'tenant_id': data['tenant_id'],
                      'admin_state_up': (data['admin_state'] == 'True'),
                      'shared': data['shared'],
                      'router:external': data['external']}
            if api.neutron.is_extension_supported(request, 'provider'):
                network_type = data['network_type']
                params['provider:network_type'] = network_type
                if network_type in ['flat', 'vlan']:
                    params['provider:physical_network'] = (
                        data['physical_network'])
                if network_type in ['vlan', 'gre', 'vxlan']:
                    params['provider:segmentation_id'] = (
                        data['segmentation_id'])
            network = api.neutron.network_create(request, **params)
            msg = _('Network %s was successfully created.') % data['name']
            LOG.debug(msg)
            messages.success(request, msg)
            return network
        except Exception:
            redirect = reverse('horizon:admin:networks:index')
            msg = _('Failed to create network %s') % data['name']
            exceptions.handle(request, msg, redirect=redirect)

    def clean(self):
        cleaned_data = super(CreateNetwork, self).clean()
        self._clean_physical_network(cleaned_data)
        self._clean_segmentation_id(cleaned_data)
        return cleaned_data

    def _clean_physical_network(self, data):
        network_type = data.get('network_type')
        if 'physical_network' in self._errors and (
                network_type in ['local', 'gre']):
            # In this case the physical network is not required, so we can
            # ignore any errors.
            del self._errors['physical_network']

    def _clean_segmentation_id(self, data):
        network_type = data.get('network_type')
        if 'segmentation_id' in self._errors:
            if network_type in ['local', 'flat']:
                # In this case the segmentation ID is not required, so we can
                # ignore any errors.
                del self._errors['segmentation_id']
        elif network_type in ['vlan', 'gre', 'vxlan']:
            seg_id = data.get('segmentation_id')
            seg_id_range = {'min': self.seg_id_range[network_type][0],
                            'max': self.seg_id_range[network_type][1]}
            if seg_id < seg_id_range['min'] or seg_id > seg_id_range['max']:
                if network_type == 'vlan':
                    msg = _('For VLAN networks, valid VLAN IDs are %(min)s '
                            'through %(max)s.') % seg_id_range
                elif network_type == 'gre':
                    msg = _('For GRE networks, valid tunnel IDs are %(min)s '
                            'through %(max)s.') % seg_id_range
                elif network_type == 'vxlan':
                    msg = _('For VXLAN networks, valid tunnel IDs are %(min)s '
                            'through %(max)s.') % seg_id_range
                self._errors['segmentation_id'] = self.error_class([msg])


class UpdateNetwork(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), required=False)
    tenant_id = forms.CharField(widget=forms.HiddenInput)
    admin_state = forms.ChoiceField(choices=[(True, _('UP')),
                                             (False, _('DOWN'))],
                                    label=_("Admin State"))
    shared = forms.BooleanField(label=_("Shared"), required=False)
    external = forms.BooleanField(label=_("External Network"), required=False)
    failure_url = 'horizon:admin:networks:index'

    def handle(self, request, data):
        try:
            params = {'name': data['name'],
                      'admin_state_up': (data['admin_state'] == 'True'),
                      'shared': data['shared'],
                      'router:external': data['external']}
            network = api.neutron.network_update(request,
                                                 self.initial['network_id'],
                                                 **params)
            msg = _('Network %s was successfully updated.') % data['name']
            LOG.debug(msg)
            messages.success(request, msg)
            return network
        except Exception:
            msg = _('Failed to update network %s') % data['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
