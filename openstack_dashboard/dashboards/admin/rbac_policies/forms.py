# Copyright 2019 vmware, Inc.
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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


# Predefined provider types.
ACTIONS = [
    {
        'name': 'access_as_shared',
        'value': _('Access as Shared')
    },
    {
        'name': 'access_as_external',
        'value': _('Access as External')
    }
]

# Predefined provider object types.
OBJECT_TYPES = [
    {
        'name': 'network',
        'value': _('Network')
    }
]

QOS_POLICY_TYPE = {
    'name': 'qos_policy',
    'value': _('QoS Policy')
}


class CreatePolicyForm(forms.SelfHandlingForm):
    target_tenant = forms.ThemableChoiceField(label=_("Target Project"))
    object_type = forms.ThemableChoiceField(
        label=_("Object Type"),
        widget=forms.ThemableSelectWidget(
            attrs={
                'class': 'switchable',
                'data-slug': 'object_type'
            }))
    network_id = forms.ThemableChoiceField(
        label=_("Network"),
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switched',
            'data-switch-on': 'object_type',
        }),
        required=False)
    qos_policy_id = forms.ThemableChoiceField(
        label=_("QoS Policy"),
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switched',
            'data-switch-on': 'object_type',
        }),
        required=False)
    action = forms.ThemableChoiceField(label=_("Action"))

    def __init__(self, request, *args, **kwargs):
        super(CreatePolicyForm, self).__init__(request, *args, **kwargs)
        tenant_choices = [('', _("Select a project"))]
        tenants, has_more = api.keystone.tenant_list(request)
        tenant_choices.append(("*", "*"))
        for tenant in tenants:
            tenant_choices.append((tenant.id, tenant.name))
        self.fields['target_tenant'].choices = tenant_choices
        action_choices = [('', _("Select an action"))]
        for action in ACTIONS:
            action_choices.append((action['name'],
                                   action['value']))
        self.fields['action'].choices = action_choices
        network_choices = []
        networks = api.neutron.network_list(request)
        for network in networks:
            network_choices.append((network.id, network.name))
        self.fields['network_id'].choices = network_choices

        # If enable QoS Policy
        if api.neutron.is_extension_supported(request, extension_alias='qos'):
            qos_policies = api.neutron.policy_list(request)
            qos_choices = [(qos_policy['id'], qos_policy['name'])
                           for qos_policy in qos_policies]
            self.fields['qos_policy_id'].choices = qos_choices
            if QOS_POLICY_TYPE not in OBJECT_TYPES:
                OBJECT_TYPES.append(QOS_POLICY_TYPE)

        object_type_choices = [('', _("Select an object type"))]
        for object_type in OBJECT_TYPES:
            object_type_choices.append((object_type['name'],
                                        object_type['value']))
        self.fields['object_type'].choices = object_type_choices

        # Register object types which required
        self.fields['network_id'].widget.attrs.update(
            {'data-object_type-network': _('Network')})
        self.fields['qos_policy_id'].widget.attrs.update(
            {'data-object_type-qos_policy': _('QoS Policy')})

    def handle(self, request, data):
        try:
            params = {
                'target_tenant': data['target_tenant'],
                'action': data['action'],
                'object_type': data['object_type'],
            }
            if data['object_type'] == 'network':
                params['object_id'] = data['network_id']
            elif data['object_type'] == 'qos_policy':
                params['object_id'] = data['qos_policy_id']

            rbac_policy = api.neutron.rbac_policy_create(request, **params)
            msg = _('RBAC Policy was successfully created.')
            messages.success(request, msg)
            return rbac_policy
        except Exception:
            redirect = reverse('horizon:admin:rbac_policies:index')
            msg = _('Failed to create a rbac policy.')
            exceptions.handle(request, msg, redirect=redirect)
            return False


class UpdatePolicyForm(forms.SelfHandlingForm):
    target_tenant = forms.ThemableChoiceField(label=_("Target Project"))
    failure_url = 'horizon:admin:rbac_policies:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdatePolicyForm, self).__init__(request, *args, **kwargs)
        tenant_choices = [('', _("Select a project"))]
        tenants, has_more = api.keystone.tenant_list(request)
        for tenant in tenants:
            tenant_choices.append((tenant.id, tenant.name))
        self.fields['target_tenant'].choices = tenant_choices

    def handle(self, request, data):
        try:
            params = {'target_tenant': data['target_tenant']}
            rbac_policy = api.neutron.rbac_policy_update(
                request, self.initial['rbac_policy_id'], **params)
            msg = _('RBAC Policy %s was successfully updated.') \
                % self.initial['rbac_policy_id']
            messages.success(request, msg)
            return rbac_policy
        except Exception as e:
            LOG.info('Failed to update rbac policy %(id)s: %(exc)s',
                     {'id': self.initial['rbac_policy_id'], 'exc': e})
            msg = _('Failed to update rbac policy %s') \
                % self.initial['rbac_policy_id']
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
