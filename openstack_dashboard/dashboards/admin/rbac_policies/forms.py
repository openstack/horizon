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
from neutronclient.common import exceptions as neutron_exc

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


ACTION_OBJECT_TYPE_LIST = [
    {
        'choice': 'shared_network',
        'label': _("Shared Network"),
        'object_type': 'network',
        'action': 'access_as_shared',
    },
    {
        'choice': 'external_network',
        'label': _("External Network"),
        'object_type': 'network',
        'action': 'access_as_external',
    },
    {
        'choice': 'shared_qos_policy',
        'label': _("Shared QoS Policy"),
        'object_type': 'qos_policy',
        'action': 'access_as_shared',
    }
]


class CreatePolicyForm(forms.SelfHandlingForm):
    target_tenant = forms.ThemableChoiceField(label=_("Target Project"))
    action_object_type = forms.ThemableChoiceField(
        label=_("Action and Object Type"),
        widget=forms.ThemableSelectWidget(
            attrs={
                'class': 'switchable',
                'data-slug': 'action_object_type'
            }))
    network_id = forms.ThemableChoiceField(
        label=_("Network"),
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switched',
            'data-switch-on': 'action_object_type',
            'data-action_object_type-shared_network': _('Network'),
            'data-action_object_type-external_network': _('Network'),
            'data-required-when-shown': 'true',
        }),
        required=False)
    qos_policy_id = forms.ThemableChoiceField(
        label=_("QoS Policy"),
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switched',
            'data-switch-on': 'action_object_type',
            'data-action_object_type-shared_qos_policy': _('QoS Policy'),
            'data-required-when-shown': 'true',
        }),
        required=False)

    def clean(self):
        cleaned_data = super(CreatePolicyForm, self).clean()
        action_object_type = cleaned_data.get("action_object_type")
        error_msg = _("This field is required.")
        if action_object_type in ["shared_network", "external_network"]:
            if not cleaned_data.get("network_id"):
                self._errors['network_id'] = self.error_class([error_msg])
        elif action_object_type == "shared_qos_policy":
            if not cleaned_data.get("qos_policy_id"):
                self._errors['qos_policy_id'] = self.error_class([error_msg])
        return cleaned_data

    def __init__(self, request, *args, **kwargs):
        super(CreatePolicyForm, self).__init__(request, *args, **kwargs)
        tenant_choices = [('', _("Select a project"))]
        tenants, has_more = api.keystone.tenant_list(request)
        tenant_choices.append(("*", "*"))
        for tenant in tenants:
            tenant_choices.append((tenant.id, tenant.name))
        self.fields['target_tenant'].choices = tenant_choices

        networks = api.neutron.network_list(request)
        network_choices = [(network.id, network.name)
                           for network in networks]
        network_choices.insert(0, ('', _("Select a network")))
        self.fields['network_id'].choices = network_choices

        # If enable QoS Policy
        qos_supported = api.neutron.is_extension_supported(
            request, extension_alias='qos')
        if qos_supported:
            qos_policies = api.neutron.policy_list(request)
            qos_choices = [(qos_policy['id'], qos_policy['name'])
                           for qos_policy in qos_policies]
            qos_choices.insert(0, ('', _("Select a QoS policy")))
            self.fields['qos_policy_id'].choices = qos_choices

        action_object_type_choices = [('', _("Select action and object type"))]
        for x in ACTION_OBJECT_TYPE_LIST:
            if x['choice'] == 'shared_qos_policy' and not qos_supported:
                continue
            action_object_type_choices.append((x['choice'], x['label']))
        self.fields['action_object_type'].choices = action_object_type_choices

    def _get_action_and_object_type(self, action_object_type):
        _map = dict((x['choice'], x) for x in ACTION_OBJECT_TYPE_LIST)
        selected = _map[action_object_type]
        return (selected['action'], selected['object_type'])

    def handle(self, request, data):
        try:
            action, object_type = self._get_action_and_object_type(
                data['action_object_type'])
            params = {
                'target_tenant': data['target_tenant'],
                'action': action,
                'object_type': object_type,
            }
            if object_type == 'network':
                params['object_id'] = data['network_id']
            elif object_type == 'qos_policy':
                params['object_id'] = data['qos_policy_id']

            rbac_policy = api.neutron.rbac_policy_create(request, **params)
            msg = _('RBAC Policy was successfully created.')
            messages.success(request, msg)
            return rbac_policy
        except neutron_exc.OverQuotaClient:
            redirect = reverse('horizon:admin:rbac_policies:index')
            msg = _('rbac policy quota exceeded.')
            exceptions.handle(request, msg, redirect=redirect)
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
        tenant_choices.append(("*", "*"))
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
