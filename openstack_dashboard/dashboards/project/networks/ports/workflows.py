#    Copyright 2016 NEC Corporation
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
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.instances.workflows import \
    update_instance as base_sec_group
from openstack_dashboard.utils import filters


LOG = logging.getLogger(__name__)


class UpdatePortInfoAction(workflows.Action):
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False)
    admin_state = forms.BooleanField(label=_("Enable Admin State"),
                                     required=False)

    def __init__(self, request, *args, **kwargs):
        super(UpdatePortInfoAction, self).__init__(request, *args, **kwargs)
        try:
            if api.neutron.is_extension_supported(request, 'binding'):
                neutron_settings = getattr(settings,
                                           'OPENSTACK_NEUTRON_NETWORK', {})
                supported_vnic_types = neutron_settings.get(
                    'supported_vnic_types', ['*'])
                if supported_vnic_types:
                    if supported_vnic_types == ['*']:
                        vnic_type_choices = api.neutron.VNIC_TYPES
                    else:
                        vnic_type_choices = [
                            vnic_type for vnic_type in api.neutron.VNIC_TYPES
                            if vnic_type[0] in supported_vnic_types
                        ]
                    self.fields['binding__vnic_type'] = forms.ChoiceField(
                        choices=vnic_type_choices,
                        label=_("Binding: VNIC Type"),
                        required=False)
        except Exception:
            msg = _("Unable to verify the VNIC types extension in Neutron")
            exceptions.handle(self.request, msg)

        try:
            if api.neutron.is_extension_supported(request, 'mac-learning'):
                self.fields['mac_state'] = forms.BooleanField(
                    label=_("MAC Learning State"), initial=False,
                    required=False)
        except Exception:
            msg = _("Unable to retrieve MAC learning state")
            exceptions.handle(self.request, msg)

        try:
            if api.neutron.is_extension_supported(request, 'port-security'):
                self.fields['port_security_enabled'] = forms.BooleanField(
                    label=_("Port Security"),
                    required=False,
                    widget=forms.CheckboxInput(attrs={
                        'class': 'switchable',
                        'data-slug': 'port_security_enabled',
                        'data-hide-tab': 'update_port__update_security_groups',
                        'data-hide-on-checked': 'false'
                    })
                )
        except Exception:
            msg = _("Unable to retrieve port security state")
            exceptions.handle(self.request, msg)

    class Meta(object):
        name = _("Info")
        slug = 'update_info'
        help_text_template = 'project/networks/ports/_edit_port_help.html'


class UpdatePortInfo(workflows.Step):
    action_class = UpdatePortInfoAction
    depends_on = ("network_id", "port_id")
    contributes = ["name", "admin_state",
                   "binding__vnic_type", "mac_state", "port_security_enabled"]


class UpdatePortSecurityGroupAction(base_sec_group.BaseSecurityGroupsAction):
    def _get_initial_security_groups(self, context):
        port_id = context.get('port_id', '')
        port = api.neutron.port_get(self.request, port_id)
        return port.security_groups

    class Meta(object):
        name = _("Security Groups")
        slug = "update_security_groups"


class UpdatePortSecurityGroup(base_sec_group.BaseSecurityGroups):
    action_class = UpdatePortSecurityGroupAction
    members_list_title = _("Port Security Groups")
    help_text = _("Add or remove security groups to this port "
                  "from the list of available security groups.")
    depends_on = ("port_id", 'target_tenant_id')


class UpdatePort(workflows.Workflow):
    slug = "update_port"
    name = _("Edit Port")
    finalize_button_name = _("Update")
    success_message = _('Port %s was successfully updated.')
    failure_message = _('Failed to update port "%s".')
    default_steps = (UpdatePortInfo, UpdatePortSecurityGroup)

    def get_success_url(self):
        return reverse("horizon:project:networks:detail",
                       args=(self.context['network_id'],))

    def format_status_message(self, message):
        name = self.context['name'] or self.context['port_id']
        return message % name

    def handle(self, request, data):
        port_id = self.context['port_id']
        LOG.debug('params = %s', data)
        params = self._construct_parameters(data)
        try:
            api.neutron.port_update(request, port_id, **params)
            return True
        except Exception as e:
            LOG.info('Failed to update port %(port_id)s: %(exc)s',
                     {'port_id': port_id, 'exc': e})
            return False

    def _construct_parameters(self, data):
        params = {
            'name': data['name'],
            'admin_state_up': data['admin_state'],
        }
        # If a field value is None, it means the field is not supported,
        # If so, we skip sending such field.
        if data['binding__vnic_type'] is not None:
            params['binding__vnic_type'] = data['binding__vnic_type']
        if data['mac_state'] is not None:
            params['mac_learning_enabled'] = data['mac_state']
        if data['port_security_enabled'] is not None:
            params['port_security_enabled'] = data['port_security_enabled']

        # If port_security_enabled is set to False, security groups on the port
        # must be cleared. We will clear the current security groups
        # in this case.
        if ('port_security_enabled' in params
                and not params['port_security_enabled']):
            params['security_groups'] = []
        # In case of UpdatePortSecurityGroup registered, 'wanted_groups'
        # exists in data.
        elif 'wanted_groups' in data:
            # If data has that key, we need to set its value
            # even if its value is empty to clear sec group setting.
            groups = map(filters.get_int_or_uuid, data['wanted_groups'])
            params['security_groups'] = groups

        return params
