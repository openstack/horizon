# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
# All rights reserved.

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

"""
Views for managing Neutron Routers.
"""
import logging

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class CreateForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Router Name"),
                           required=False)
    admin_state_up = forms.BooleanField(
        label=_("Enable Admin State"),
        initial=True,
        required=False,
        help_text=_("If checked, the router will be enabled."))
    external_network = forms.ThemableChoiceField(label=_("External Network"),
                                                 required=False)
    enable_snat = forms.BooleanField(label=_("Enable SNAT"),
                                     initial=True,
                                     required=False)
    mode = forms.ThemableChoiceField(label=_("Router Type"))
    ha = forms.ThemableChoiceField(label=_("High Availability Mode"))
    az_hints = forms.MultipleChoiceField(
        label=_("Availability Zone Hints"),
        required=False,
        help_text=_("Availability Zones where the router may be scheduled. "
                    "Leaving this unset is equivalent to selecting all "
                    "Availability Zones"))
    failure_url = 'horizon:project:routers:index'

    def __init__(self, request, *args, **kwargs):
        super(CreateForm, self).__init__(request, *args, **kwargs)
        self.dvr_allowed = api.neutron.get_feature_permission(self.request,
                                                              "dvr", "create")
        if self.dvr_allowed:
            mode_choices = [('server_default', _('Use Server Default')),
                            ('centralized', _('Centralized')),
                            ('distributed', _('Distributed'))]
            self.fields['mode'].choices = mode_choices
        else:
            del self.fields['mode']

        self.ha_allowed = api.neutron.get_feature_permission(self.request,
                                                             "l3-ha", "create")
        if self.ha_allowed:
            ha_choices = [('server_default', _('Use Server Default')),
                          ('enabled', _('Enable HA mode')),
                          ('disabled', _('Disable HA mode'))]
            self.fields['ha'].choices = ha_choices
        else:
            del self.fields['ha']
        networks = self._get_network_list(request)
        if networks:
            self.fields['external_network'].choices = networks
        else:
            del self.fields['external_network']

        self.enable_snat_allowed = self.initial['enable_snat_allowed']
        if (not networks or not self.enable_snat_allowed):
            del self.fields['enable_snat']

        try:
            az_supported = api.neutron.is_extension_supported(
                self.request, 'router_availability_zone')

            if az_supported:
                zones = api.neutron.list_availability_zones(
                    self.request, 'router', 'available')
                self.fields['az_hints'].choices = [(zone['name'], zone['name'])
                                                   for zone in zones]
            else:
                del self.fields['az_hints']
        except Exception:
            msg = _("Failed to get availability zone list.")
            exceptions.handle(self.request, msg)
            del self.fields['az_hints']

    def _get_network_list(self, request):
        search_opts = {'router:external': True}
        try:
            networks = api.neutron.network_list(request, **search_opts)
        except Exception as e:
            LOG.info('Failed to get network list: %s', e)
            msg = _('Failed to get network list.')
            messages.warning(request, msg)
            networks = []

        choices = [(network.id, network.name or network.id)
                   for network in networks]
        if choices:
            choices.insert(0, ("", _("Select network")))
        return choices

    def handle(self, request, data):
        try:
            params = {'name': data['name'],
                      'admin_state_up': data['admin_state_up']}
            # NOTE: admin form allows to specify tenant_id.
            # We have the logic here to simplify the logic.
            if 'tenant_id' in data and data['tenant_id']:
                params['tenant_id'] = data['tenant_id']
            if 'external_network' in data and data['external_network']:
                params['external_gateway_info'] = {'network_id':
                                                   data['external_network']}
                if self.enable_snat_allowed:
                    params['external_gateway_info']['enable_snat'] = \
                        data['enable_snat']
            if 'az_hints' in data and data['az_hints']:
                params['availability_zone_hints'] = data['az_hints']
            if (self.dvr_allowed and data['mode'] != 'server_default'):
                params['distributed'] = (data['mode'] == 'distributed')
            if (self.ha_allowed and data['ha'] != 'server_default'):
                params['ha'] = (data['ha'] == 'enabled')
            router = api.neutron.router_create(request, **params)
            message = (_('Router %s was successfully created.') %
                       router.name_or_id)
            messages.success(request, message)
            return router
        except Exception as exc:
            LOG.info('Failed to create router: %s', exc)
            if exc.status_code == 409:
                msg = _('Quota exceeded for resource router.')
            else:
                if data["name"]:
                    msg = _('Failed to create router "%s".') % data['name']
                else:
                    msg = _('Failed to create router.')
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            return False


class UpdateForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), required=False)
    admin_state = forms.BooleanField(
        label=_("Enable Admin State"),
        required=False,
        help_text=_("If checked, the router will be enabled."))
    mode = forms.ThemableChoiceField(label=_("Router Type"))
    ha = forms.BooleanField(label=_("High Availability Mode"), required=False)

    redirect_url = reverse_lazy('horizon:project:routers:index')

    def __init__(self, request, *args, **kwargs):
        super(UpdateForm, self).__init__(request, *args, **kwargs)
        self.dvr_allowed = api.neutron.get_feature_permission(self.request,
                                                              "dvr", "update")
        if not self.dvr_allowed:
            del self.fields['mode']
        elif self.initial.get('mode') == 'distributed':
            # Neutron supports only changing from centralized to
            # distributed now.
            mode_choices = [('distributed', _('Distributed'))]
            self.fields['mode'].widget = forms.TextInput(attrs={'readonly':
                                                                'readonly'})
            self.fields['mode'].choices = mode_choices
        else:
            mode_choices = [('centralized', _('Centralized')),
                            ('distributed', _('Distributed'))]
            self.fields['mode'].choices = mode_choices

        # TODO(amotoki): Due to Neutron Bug 1378525, Neutron disables
        # PUT operation. It will be fixed in Kilo cycle.
        # self.ha_allowed = api.neutron.get_feature_permission(
        #     self.request, "l3-ha", "update")
        self.ha_allowed = False
        if not self.ha_allowed:
            del self.fields['ha']

    def handle(self, request, data):
        try:
            params = {'admin_state_up': data['admin_state'],
                      'name': data['name']}
            if self.dvr_allowed:
                params['distributed'] = (data['mode'] == 'distributed')
            if self.ha_allowed:
                params['ha'] = data['ha']
            router = api.neutron.router_update(request,
                                               self.initial['router_id'],
                                               **params)
            msg = _('Router %s was successfully updated.') % router.name_or_id
            messages.success(request, msg)
            return router
        except Exception as exc:
            LOG.info('Failed to update router %(id)s: %(exc)s',
                     {'id': self.initial['router_id'], 'exc': exc})
            name_or_id = data['name'] or self.initial['router_id']
            msg = _('Failed to update router %s') % name_or_id
            exceptions.handle(request, msg, redirect=self.redirect_url)
