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
                        help_text=_(
                            "The VNIC type that is bound to the neutron port"),
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
                    help_text=_("Enable anti-spoofing rules for the port"),
                    required=False
                )
        except Exception:
            msg = _("Unable to retrieve port security state")
            exceptions.handle(self.request, msg)

    class Meta(object):
        name = _("Info")


class UpdatePortInfo(workflows.Step):
    action_class = UpdatePortInfoAction
    depends_on = ("network_id", "port_id")
    contributes = ["name", "admin_state",
                   "binding__vnic_type", "mac_state", "port_security_enabled"]
    help_text = _("You can update the editable properties of your port here.")


class UpdatePort(workflows.Workflow):
    slug = "update_port"
    name = _("Edit Port")
    finalize_button_name = _("Update")
    success_message = _('Port %s was successfully updated.')
    failure_message = _('Failed to update port "%s".')
    default_steps = (UpdatePortInfo,)

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

        return params
