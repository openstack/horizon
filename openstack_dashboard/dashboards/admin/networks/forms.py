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

# Predefined provider network types.
# You can add or override these entries by extra_provider_types
# in the settings.
PROVIDER_TYPES = {
    'local': {
        'display_name': _('Local'),
        'require_physical_network': False,
        'require_segmentation_id': False,
    },
    'flat': {
        'display_name': _('Flat'),
        'require_physical_network': True,
        'require_segmentation_id': False,
    },
    'vlan': {
        'display_name': _('VLAN'),
        'require_physical_network': True,
        'require_segmentation_id': True,
    },
    'gre': {
        'display_name': _('GRE'),
        'require_physical_network': False,
        'require_segmentation_id': True,
    },
    'vxlan': {
        'display_name': _('VXLAN'),
        'require_physical_network': False,
        'require_segmentation_id': True,
    },
    'geneve': {
        'display_name': _('Geneve'),
        'require_physical_network': False,
        'require_segmentation_id': True,
    },
    'midonet': {
        'display_name': _('MidoNet'),
        'require_physical_network': False,
        'require_segmentation_id': False,
    },
    'uplink': {
        'display_name': _('MidoNet Uplink'),
        'require_physical_network': False,
        'require_segmentation_id': False,
    },
}
# Predefined valid segmentation ID range per network type.
# You can add or override these entries by segmentation_id_range
# in the settings.
SEGMENTATION_ID_RANGE = {
    'vlan': (1, 4094),
    'gre': (1, (2 ** 32) - 1),
    'vxlan': (1, (2 ** 24) - 1),
    'geneve': (1, (2 ** 24) - 1),
}
# DEFAULT_PROVIDER_TYPES is used when ['*'] is specified
# in supported_provider_types. This list contains network types
# supported by Neutron ML2 plugin reference implementation.
# You can control enabled network types by
# supported_provider_types setting.
DEFAULT_PROVIDER_TYPES = ['local', 'flat', 'vlan', 'gre', 'vxlan', 'geneve']


class CreateNetwork(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False)
    tenant_id = forms.ChoiceField(label=_("Project"))
    if api.neutron.is_port_profiles_supported():
        widget = None
    else:
        widget = forms.HiddenInput()
    net_profile_id = forms.ChoiceField(label=_("Network Profile"),
                                       required=False,
                                       widget=widget)
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
        }))
    segmentation_id = forms.IntegerField(
        label=_("Segmentation ID"),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'network_type',
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

        if api.neutron.is_port_profiles_supported():
            self.fields['net_profile_id'].choices = (
                self.get_network_profile_choices(request))

        if api.neutron.is_extension_supported(request, 'provider'):
            neutron_settings = getattr(settings,
                                       'OPENSTACK_NEUTRON_NETWORK', {})
            self.seg_id_range = SEGMENTATION_ID_RANGE.copy()
            seg_id_range = neutron_settings.get('segmentation_id_range')
            if seg_id_range:
                self.seg_id_range.update(seg_id_range)

            self.provider_types = PROVIDER_TYPES.copy()
            extra_provider_types = neutron_settings.get('extra_provider_types')
            if extra_provider_types:
                self.provider_types.update(extra_provider_types)

            self.nettypes_with_seg_id = [
                net_type for net_type in self.provider_types
                if self.provider_types[net_type]['require_segmentation_id']]
            self.nettypes_with_physnet = [
                net_type for net_type in self.provider_types
                if self.provider_types[net_type]['require_physical_network']]

            supported_provider_types = neutron_settings.get(
                'supported_provider_types', DEFAULT_PROVIDER_TYPES)
            if supported_provider_types == ['*']:
                supported_provider_types = DEFAULT_PROVIDER_TYPES

            undefined_provider_types = [
                net_type for net_type in supported_provider_types
                if net_type not in self.provider_types]
            if undefined_provider_types:
                LOG.error('Undefined provider network types are found: %s',
                          undefined_provider_types)

            seg_id_help = [
                _("For %(type)s networks, valid IDs are %(min)s to %(max)s.")
                % {'type': net_type,
                   'min': self.seg_id_range[net_type][0],
                   'max': self.seg_id_range[net_type][1]}
                for net_type in self.nettypes_with_seg_id]
            self.fields['segmentation_id'].help_text = ' '.join(seg_id_help)

            # Register network types which require segmentation ID
            attrs = dict(('data-network_type-%s' % network_type,
                          _('Segmentation ID'))
                         for network_type in self.nettypes_with_seg_id)
            self.fields['segmentation_id'].widget.attrs.update(attrs)

            # Register network types which require physical network
            attrs = dict(('data-network_type-%s' % network_type,
                          _('Physical Network'))
                         for network_type in self.nettypes_with_physnet)
            self.fields['physical_network'].widget.attrs.update(attrs)

            network_type_choices = [
                (net_type, self.provider_types[net_type]['display_name'])
                for net_type in supported_provider_types]
            if len(network_type_choices) == 0:
                self._hide_provider_network_type()
            else:
                self.fields['network_type'].choices = network_type_choices
        else:
            self._hide_provider_network_type()

    def get_network_profile_choices(self, request):
        profile_choices = [('', _("Select a profile"))]
        for profile in self._get_profiles(request, 'network'):
            profile_choices.append((profile.id, profile.name))
        return profile_choices

    def _get_profiles(self, request, type_p):
        profiles = []
        try:
            profiles = api.neutron.profile_list(request, type_p)
        except Exception:
            msg = _('Network Profiles could not be retrieved.')
            exceptions.handle(request, msg)
        return profiles

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
            if api.neutron.is_port_profiles_supported():
                params['net_profile_id'] = data['net_profile_id']
            if api.neutron.is_extension_supported(request, 'provider'):
                network_type = data['network_type']
                params['provider:network_type'] = network_type
                if network_type in self.nettypes_with_physnet:
                    params['provider:physical_network'] = (
                        data['physical_network'])
                if network_type in self.nettypes_with_seg_id:
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
        if api.neutron.is_extension_supported(self.request, 'provider'):
            self._clean_physical_network(cleaned_data)
            self._clean_segmentation_id(cleaned_data)
        return cleaned_data

    def _clean_physical_network(self, data):
        network_type = data.get('network_type')
        if ('physical_network' in self._errors and
                network_type not in self.nettypes_with_physnet):
            # In this case the physical network is not required, so we can
            # ignore any errors.
            del self._errors['physical_network']

    def _clean_segmentation_id(self, data):
        network_type = data.get('network_type')
        if 'segmentation_id' in self._errors:
            if network_type not in self.nettypes_with_seg_id:
                # In this case the segmentation ID is not required, so we can
                # ignore any errors.
                del self._errors['segmentation_id']
        elif network_type in self.nettypes_with_seg_id:
            seg_id = data.get('segmentation_id')
            seg_id_range = {'min': self.seg_id_range[network_type][0],
                            'max': self.seg_id_range[network_type][1]}
            if seg_id < seg_id_range['min'] or seg_id > seg_id_range['max']:
                msg = (_('For a %(network_type)s network, valid segmentation '
                         'IDs are %(min)s through %(max)s.')
                       % {'network_type': network_type,
                          'min': seg_id_range['min'],
                          'max': seg_id_range['max']})
                self._errors['segmentation_id'] = self.error_class([msg])


class UpdateNetwork(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), required=False)
    tenant_id = forms.CharField(widget=forms.HiddenInput)
    network_id = forms.CharField(label=_("ID"),
                                 widget=forms.TextInput(
                                     attrs={'readonly': 'readonly'}))
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
