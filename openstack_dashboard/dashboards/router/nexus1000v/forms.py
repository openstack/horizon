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

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _


LOG = logging.getLogger(__name__)


def get_tenant_choices(request):
    tenant_choices = [('', _("Select a project"))]
    tenants = []
    try:
        tenants, has_more = api.keystone.tenant_list(request)
    except Exception:
        msg = _('Projects could not be retrieved.')
        exceptions.handle(request, msg)
    for tenant in tenants:
        if tenant.enabled:
            tenant_choices.append((tenant.id, tenant.name))
    return tenant_choices


class CreateNetworkProfile(forms.SelfHandlingForm):

    """Create Network Profile form."""

    name = forms.CharField(max_length=255,
                           label=_("Name"))
    segment_type = forms.ChoiceField(label=_('Segment Type'),
                                     choices=[('vlan', _('VLAN')),
                                              ('overlay', _('Overlay')),
                                              ('trunk', _('Trunk'))],
                                     widget=forms.Select
                                     (attrs={'class': 'switchable',
                                             'data-slug': 'segtype'}))
    # Sub type options available for Overlay segment type
    sub_type = forms.ChoiceField(label=_('Sub Type'),
                                 choices=[('native_vxlan', _('Native VXLAN')),
                                          ('enhanced', _('Enhanced VXLAN')),
                                          ('other', _('Other'))],
                                 required=False,
                                 widget=forms.Select
                                 (attrs={'class': 'switchable switched',
                                         'data-slug': 'subtype',
                                         'data-switch-on': 'segtype',
                                         'data-segtype-overlay':
                                             _("Sub Type")}))
    # Sub type options available for Trunk segment type
    sub_type_trunk = forms.ChoiceField(label=_('Sub Type'),
                                       choices=[('vlan', _('VLAN'))],
                                       required=False,
                                       widget=forms.Select
                                       (attrs={'class': 'switched',
                                               'data-switch-on': 'segtype',
                                               'data-segtype-trunk':
                                                   _("Sub Type")}))
    segment_range = forms.CharField(max_length=255,
                                    label=_("Segment Range"),
                                    required=False,
                                    widget=forms.TextInput
                                    (attrs={'class': 'switched',
                                            'data-switch-on': 'segtype',
                                            'data-segtype-vlan':
                                                _("Segment Range"),
                                            'data-segtype-overlay':
                                                _("Segment Range")}),
                                    help_text=_("1-4093 for VLAN; "
                                                "5000 and above for Overlay"))
    multicast_ip_range = forms.CharField(max_length=30,
                                         label=_("Multicast IP Range"),
                                         required=False,
                                         widget=forms.TextInput
                                         (attrs={'class': 'switched',
                                                 'data-switch-on':
                                                     'subtype',
                                                 'data-subtype-native_vxlan':
                                                     _("Multicast IP Range")}),
                                         help_text=_("Multicast IPv4 range"
                                                     "(e.g. 224.0.1.0-"
                                                     "224.0.1.100)"))
    other_subtype = forms.CharField(max_length=255,
                                    label=_("Sub Type Value (Manual Input)"),
                                    required=False,
                                    widget=forms.TextInput
                                    (attrs={'class': 'switched',
                                            'data-switch-on':
                                                'subtype',
                                            'data-subtype-other':
                                                _("Sub Type Value "
                                                  "(Manual Input)")}),
                                    help_text=_("Enter parameter (e.g. GRE)"))
    physical_network = forms.CharField(max_length=255,
                                       label=_("Physical Network"),
                                       required=False,
                                       widget=forms.TextInput
                                       (attrs={'class': 'switched',
                                               'data-switch-on': 'segtype',
                                               'data-segtype-vlan':
                                                   _("Physical Network")}))
    project = forms.ChoiceField(label=_("Project"),
                                required=False)

    def __init__(self, request, *args, **kwargs):
        super(CreateNetworkProfile, self).__init__(request, *args, **kwargs)
        self.fields['project'].choices = get_tenant_choices(request)

    def clean(self):
        # If sub_type is 'other' or 'trunk' then
        # assign this new value for sub_type
        cleaned_data = super(CreateNetworkProfile, self).clean()

        segment_type = cleaned_data.get('segment_type')
        if segment_type == 'overlay':
            sub_type = cleaned_data.get('sub_type')
            if sub_type == 'other':
                other_subtype = cleaned_data.get('other_subtype')
                cleaned_data['sub_type'] = other_subtype
                LOG.debug('subtype is now %(params)s',
                          {'params': other_subtype})
        elif segment_type == 'trunk':
            sub_type_trunk = cleaned_data.get('sub_type_trunk')
            cleaned_data['sub_type'] = sub_type_trunk
            LOG.debug('subtype is now %(params)s',
                      {'params': sub_type_trunk})

        return cleaned_data

    def handle(self, request, data):
        try:
            LOG.debug('request = %(req)s, params = %(params)s',
                      {'req': request, 'params': data})
            params = {'name': data['name'],
                      'segment_type': data['segment_type'],
                      'sub_type': data['sub_type'],
                      'segment_range': data['segment_range'],
                      'physical_network': data['physical_network'],
                      'multicast_ip_range': data['multicast_ip_range'],
                      'tenant_id': data['project']}
            profile = api.neutron.profile_create(request,
                                                 **params)
            msg = _('Network Profile %s '
                    'was successfully created.') % data['name']
            LOG.debug(msg)
            messages.success(request, msg)
            return profile
        except Exception:
            redirect = reverse('horizon:router:nexus1000v:index')
            msg = _('Failed to create network profile %s') % data['name']
            exceptions.handle(request, msg, redirect=redirect)


class UpdateNetworkProfile(CreateNetworkProfile):
    """Update Network Profile form."""

    profile_id = forms.CharField(label=_("ID"),
                                 widget=forms.HiddenInput())

    project = forms.CharField(label=_("Project"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(UpdateNetworkProfile, self).__init__(request, *args, **kwargs)

        self.fields['segment_type'].widget.attrs['readonly'] = 'readonly'
        self.fields['sub_type'].widget.attrs['readonly'] = 'readonly'
        self.fields['sub_type_trunk'].widget.attrs['readonly'] = 'readonly'
        self.fields['other_subtype'].widget.attrs['readonly'] = 'readonly'
        self.fields['physical_network'].widget.attrs['readonly'] = 'readonly'
        self.fields['project'].widget.attrs['readonly'] = 'readonly'

    def handle(self, request, data):
        try:
            LOG.debug('request = %(req)s, params = %(params)s',
                      {'req': request, 'params': data})
            params = {'name': data['name'],
                      'segment_range': data['segment_range'],
                      'multicast_ip_range': data['multicast_ip_range']}
            profile = api.neutron.profile_update(
                request,
                data['profile_id'],
                **params
            )
            msg = _('Network Profile %s '
                    'was successfully updated.') % data['name']
            LOG.debug(msg)
            messages.success(request, msg)
            return profile
        except Exception:
            msg = _('Failed to update '
                    'network profile (%s).') % data['name']
            redirect = reverse('horizon:router:nexus1000v:index')
            exceptions.handle(request, msg, redirect=redirect)
            return False
