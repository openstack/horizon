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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.networks.ports import sg_base
from openstack_dashboard.utils import filters
from openstack_dashboard.utils import settings as setting_utils


LOG = logging.getLogger(__name__)


class CreatePortSecurityGroupAction(sg_base.BaseSecurityGroupsAction):
    def _get_initial_security_groups(self, context):
        field_name = self.get_member_field_name('member')
        groups_list = self.fields[field_name].choices
        return [group[0] for group in groups_list
                if group[1] == 'default']

    class Meta(object):
        name = _("Security Groups")
        slug = "create_security_groups"


class CreatePortSecurityGroup(sg_base.BaseSecurityGroups):
    action_class = CreatePortSecurityGroupAction
    members_list_title = _("Port Security Groups")
    help_text = _('Add or remove security groups to the port '
                  'from the list of available security groups. '
                  'The "default" security group is associated '
                  'by default and you can remove "default" '
                  'security group from the port.')
    depends_on = ("target_tenant_id",)


class CreatePortInfoAction(workflows.Action):
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False)
    admin_state = forms.BooleanField(
        label=_("Enable Admin State"),
        initial=True,
        required=False,
        help_text=_("If checked, the port will be enabled."))
    device_id = forms.CharField(max_length=100, label=_("Device ID"),
                                help_text=_("Device ID attached to the port"),
                                required=False)
    device_owner = forms.CharField(
        max_length=100, label=_("Device Owner"),
        help_text=_("Owner of the device attached to the port"),
        required=False)
    specify_ip = forms.ThemableChoiceField(
        label=_("Specify IP address or subnet"),
        help_text=_("To specify a subnet or a fixed IP, select any options."),
        required=False,
        choices=[('', _("Unspecified")),
                 ('subnet_id', _("Subnet")),
                 ('fixed_ip', _("Fixed IP Address"))],
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switchable',
            'data-slug': 'specify_ip',
        }))
    subnet_id = forms.ThemableChoiceField(
        label=_("Subnet"),
        required=False,
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switched',
            'data-required-when-shown': 'true',
            'data-switch-on': 'specify_ip',
            'data-specify_ip-subnet_id': _('Subnet'),
        }))
    fixed_ip = forms.IPField(
        label=_("Fixed IP Address"),
        required=False,
        help_text=_("Specify the subnet IP address for the new port"),
        version=forms.IPv4 | forms.IPv6,
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-required-when-shown': 'true',
            'data-switch-on': 'specify_ip',
            'data-specify_ip-fixed_ip': _('Fixed IP Address'),
        }))
    mac_address = forms.MACAddressField(
        label=_("MAC Address"),
        required=False,
        help_text=_("Specify the MAC address for the new port"))
    mac_state = forms.BooleanField(
        label=_("MAC Learning State"), initial=False,
        required=False)
    port_security_enabled = forms.BooleanField(
        label=_("Port Security"),
        help_text=_("Enable anti-spoofing rules for the port"),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'switchable',
            'data-slug': 'port_security_enabled',
            'data-hide-tab': 'create_port__create_security_groups',
            'data-hide-on-checked': 'false'
        }))
    binding__vnic_type = forms.ThemableChoiceField(
        label=_("VNIC Type"),
        help_text=_("The VNIC type that is bound to the network port"),
        required=False)

    def __init__(self, request, context, *args, **kwargs):
        super(CreatePortInfoAction, self).__init__(
            request, context, *args, **kwargs)

        # prepare subnet choices and input area for each subnet
        subnet_choices = self._get_subnet_choices(context)
        if subnet_choices:
            subnet_choices.insert(0, ('', _("Select a subnet")))
            self.fields['subnet_id'].choices = subnet_choices
        else:
            self.fields['specify_ip'].widget = forms.HiddenInput()
            self.fields['subnet_id'].widget = forms.HiddenInput()
            self.fields['fixed_ip'].widget = forms.HiddenInput()

        self._hide_field_if_not_supported(
            request, 'mac_state', 'mac-learning',
            _("Unable to retrieve MAC learning state"))
        self._hide_field_if_not_supported(
            request, 'port_security_enabled', 'port-security',
            _("Unable to retrieve port security state"))

        self._populate_vnic_type_choices(request)

    def _hide_field_if_not_supported(self, request, field, extension_alias,
                                     failure_message):
        is_supproted = False
        try:
            is_supproted = api.neutron.is_extension_supported(
                request, extension_alias)
        except Exception:
            exceptions.handle(self.request, failure_message)
        if not is_supproted:
            del self.fields[field]
        return is_supproted

    def _populate_vnic_type_choices(self, request):
        supported_vnic_types = setting_utils.get_dict_config(
            'OPENSTACK_NEUTRON_NETWORK', 'supported_vnic_types')
        # When a list of VNIC types is empty, hide the corresponding field.
        if not supported_vnic_types:
            del self.fields['binding__vnic_type']
            return

        binding_supported = self._hide_field_if_not_supported(
            request, 'binding__vnic_type', 'binding',
            _("Unable to verify the VNIC types extension in Neutron"))
        if not binding_supported:
            # binding__vnic_type field is already deleted, so return here
            return

        if supported_vnic_types == ['*']:
            vnic_type_choices = api.neutron.VNIC_TYPES
        else:
            vnic_type_choices = [
                vnic_type for vnic_type in api.neutron.VNIC_TYPES
                if vnic_type[0] in supported_vnic_types
            ]
        self.fields['binding__vnic_type'].choices = vnic_type_choices

    def _get_subnet_choices(self, context):
        try:
            network_id = context['network_id']
            network = api.neutron.network_get(self.request, network_id)
        except Exception:
            return []

        # NOTE(amotoki): When a user cannot retrieve a subnet info,
        # subnet ID is stored in network.subnets field.
        # If so, we skip such subnet as subnet choices.
        # This happens usually for external networks.
        # TODO(amotoki): Ideally it is better to disable/hide
        # Create Port button in the port table, but as of Pike
        # the default neutron policy.json for "create_port" is empty
        # and there seems no appropriate policy. This is a dirty hack.
        return [(subnet.id, '%s %s' % (subnet.name_or_id, subnet.cidr))
                for subnet in network.subnets
                if isinstance(subnet, api.neutron.Subnet)]

    def clean_subnet_id(self):
        specify_ip = self.cleaned_data.get('specify_ip')
        subnet_id = self.cleaned_data.get('subnet_id')
        if specify_ip == "subnet_id" and not subnet_id:
            raise forms.ValidationError(_("This field is required."))
        return subnet_id

    def clean_fixed_ip(self):
        specify_ip = self.cleaned_data.get('specify_ip')
        fixed_ip = self.cleaned_data.get('fixed_ip')
        if specify_ip == "fixed_ip" and not fixed_ip:
            raise forms.ValidationError(_("This field is required."))
        return fixed_ip

    class Meta(object):
        name = _("Info")
        slug = 'create_info'
        help_text_template = 'project/networks/ports/_create_port_help.html'


class CreatePortInfo(workflows.Step):
    action_class = CreatePortInfoAction
    depends_on = ("network_id",)
    contributes = ["name", "admin_state", "device_id", "device_owner",
                   "specify_ip", "subnet_id", "fixed_ip", "mac_address",
                   "mac_state", "port_security_enabled", "binding__vnic_type"]


class CreatePort(workflows.Workflow):
    slug = "create_port"
    name = _("Create Port")
    finalize_button_name = _("Create")
    success_message = _('Port %s was successfully created.')
    failure_message = _('Failed to create port "%s".')
    default_steps = (CreatePortInfo, CreatePortSecurityGroup)

    def get_success_url(self):
        return reverse("horizon:project:networks:detail",
                       args=(self.context['network_id'],))

    def format_status_message(self, message):
        name = self.context['name'] or self.context.get('port_id', '')
        return message % name

    def handle(self, request, context):
        try:
            params = self._construct_parameters(context)
            port = api.neutron.port_create(request, **params)
            self.context['port_id'] = port.id
            return True
        except Exception as e:
            LOG.info('Failed to create a port for network %(id)s: %(exc)s',
                     {'id': context['network_id'], 'exc': e})

    def _construct_parameters(self, context):
        params = {
            'network_id': context['network_id'],
            'admin_state_up': context['admin_state'],
            'name': context['name'],
            'device_id': context['device_id'],
            'device_owner': context['device_owner']
        }

        if context.get('specify_ip') == 'subnet_id':
            if context.get('subnet_id'):
                params['fixed_ips'] = [{"subnet_id": context['subnet_id']}]
        elif context.get('specify_ip') == 'fixed_ip':
            if context.get('fixed_ip'):
                params['fixed_ips'] = [{"ip_address": context['fixed_ip']}]

        if context.get('binding__vnic_type'):
            params['binding__vnic_type'] = context['binding__vnic_type']
        if context.get('mac_state'):
            params['mac_learning_enabled'] = context['mac_state']
        if context['port_security_enabled'] is not None:
            params['port_security_enabled'] = context['port_security_enabled']

        # Send mac_address only when it is specified.
        if context['mac_address']:
            params['mac_address'] = context['mac_address']

        # If port_security_enabled is set to False, security groups on the port
        # must be cleared. We will clear the current security groups
        # in this case.
        if ('port_security_enabled' in params and
                not params['port_security_enabled']):
            params['security_groups'] = []
        # In case of CreatePortSecurityGroup registered, 'wanted_groups'
        # exists in context.
        elif 'wanted_groups' in context:
            # If context has that key, we need to set its value
            # even if its value is empty to clear sec group setting.
            groups = [filters.get_int_or_uuid(sg)
                      for sg in context['wanted_groups']]
            params['security_groups'] = groups

        return params


class UpdatePortInfoAction(workflows.Action):
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False)
    admin_state = forms.BooleanField(
        label=_("Enable Admin State"),
        required=False,
        help_text=_("If checked, the port will be enabled."))

    def __init__(self, request, *args, **kwargs):
        super(UpdatePortInfoAction, self).__init__(request, *args, **kwargs)
        try:
            if api.neutron.is_extension_supported(request, 'binding'):
                supported_vnic_types = setting_utils.get_dict_config(
                    'OPENSTACK_NEUTRON_NETWORK', 'supported_vnic_types')
                if supported_vnic_types:
                    if supported_vnic_types == ['*']:
                        vnic_type_choices = api.neutron.VNIC_TYPES
                    else:
                        vnic_type_choices = [
                            vnic_type for vnic_type in api.neutron.VNIC_TYPES
                            if vnic_type[0] in supported_vnic_types
                        ]
                    self.fields['binding__vnic_type'] = (
                        forms.ThemableChoiceField(
                            choices=vnic_type_choices,
                            label=_("Binding: VNIC Type"),
                            required=False))
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


class UpdatePortSecurityGroupAction(sg_base.BaseSecurityGroupsAction):
    def _get_initial_security_groups(self, context):
        port_id = context.get('port_id', '')
        port = api.neutron.port_get(self.request, port_id)
        return port.security_groups

    class Meta(object):
        name = _("Security Groups")
        slug = "update_security_groups"


class UpdatePortSecurityGroup(sg_base.BaseSecurityGroups):
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
        if ('port_security_enabled' in params and
                not params['port_security_enabled']):
            params['security_groups'] = []
        # In case of UpdatePortSecurityGroup registered, 'wanted_groups'
        # exists in data.
        elif 'wanted_groups' in data:
            # If data has that key, we need to set its value
            # even if its value is empty to clear sec group setting.
            groups = [filters.get_int_or_uuid(sg)
                      for sg in data['wanted_groups']]
            params['security_groups'] = groups

        return params
