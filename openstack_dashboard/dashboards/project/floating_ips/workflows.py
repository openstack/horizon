# Copyright 2012 Nebula, Inc.

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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from neutronclient.common import exceptions as neutron_exc

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.utils import filters


ALLOCATE_URL = "horizon:project:floating_ips:allocate"


class AssociateIPAction(workflows.Action):
    ip_id = forms.ThemableDynamicTypedChoiceField(
        label=_("IP Address"),
        coerce=filters.get_int_or_uuid,
        empty_value=None,
        add_item_link=ALLOCATE_URL)
    instance_id = forms.ThemableChoiceField(label=_("Port to be associated"))

    class Meta(object):
        name = _("IP Address")
        help_text = _("Select the IP address you wish to associate with "
                      "the selected instance or port.")

    def __init__(self, *args, **kwargs):
        super(AssociateIPAction, self).__init__(*args, **kwargs)

        # If AssociateIP is invoked from instance menu, instance_id parameter
        # is passed in URL. In Neutron based Floating IP implementation
        # an association target is not an instance but a port, so we need
        # to get an association target based on a received instance_id
        # and set the initial value of instance_id ChoiceField.
        q_instance_id = self.request.GET.get('instance_id')
        q_port_id = self.request.GET.get('port_id')
        if q_instance_id:
            targets = self._get_target_list()
            target_id = api.neutron.floating_ip_target_get_by_instance(
                self.request, q_instance_id, targets)
            self.initial['instance_id'] = target_id
        elif q_port_id:
            targets = self._get_target_list()
            for target in targets:
                if (hasattr(target, 'port_id') and
                        target.port_id == q_port_id):
                    self.initial['instance_id'] = target.id
                    break

    def populate_ip_id_choices(self, request, context):
        ips = []
        redirect = reverse('horizon:project:floating_ips:index')
        try:
            ips = api.neutron.tenant_floating_ip_list(self.request)
        except neutron_exc.ConnectionFailed:
            exceptions.handle(self.request, redirect=redirect)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve floating IP addresses.'),
                              redirect=redirect)
        options = sorted([(ip.id, ip.ip) for ip in ips if not ip.port_id])
        if options:
            options.insert(0, ("", _("Select an IP address")))
        else:
            options = [("", _("No floating IP addresses allocated"))]

        return options

    @memoized.memoized_method
    def _get_target_list(self):
        targets = []
        try:
            targets = api.neutron.floating_ip_target_list(self.request)
        except Exception:
            redirect = reverse('horizon:project:floating_ips:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve instance list.'),
                              redirect=redirect)
        return targets

    # TODO(amotoki): [drop-nova-network] Rename instance_id to port_id
    def populate_instance_id_choices(self, request, context):
        targets = self._get_target_list()

        instances = []
        for target in targets:
            instances.append((target.id, target.name))

        # Sort instances for easy browsing
        instances = sorted(instances, key=lambda x: x[1])

        if instances:
            instances.insert(0, ("", _("Select a port")))
        else:
            instances = (("", _("No ports available")),)
        return instances


class AssociateIP(workflows.Step):
    action_class = AssociateIPAction
    contributes = ("ip_id", "instance_id", "ip_address")

    def contribute(self, data, context):
        context = super(AssociateIP, self).contribute(data, context)
        ip_id = data.get('ip_id', None)
        if ip_id:
            ip_choices = dict(self.action.fields['ip_id'].choices)
            context["ip_address"] = ip_choices.get(ip_id, None)
        return context


class IPAssociationWorkflow(workflows.Workflow):
    slug = "ip_association"
    name = _("Manage Floating IP Associations")
    finalize_button_name = _("Associate")
    success_message = _('IP address %s associated.')
    failure_message = _('Unable to associate IP address %s.')
    success_url = "horizon:project:floating_ips:index"
    default_steps = (AssociateIP,)

    def format_status_message(self, message):
        if "%s" in message:
            return message % self.context.get('ip_address',
                                              _('unknown IP address'))
        else:
            return message

    def handle(self, request, data):
        try:
            api.neutron.floating_ip_associate(request,
                                              data['ip_id'],
                                              data['instance_id'])
        except neutron_exc.Conflict:
            msg = _('The requested instance port is already'
                    ' associated with another floating IP.')
            exceptions.handle(request, msg)
            self.failure_message = msg
            return False

        except Exception:
            exceptions.handle(request)
            return False
        return True
