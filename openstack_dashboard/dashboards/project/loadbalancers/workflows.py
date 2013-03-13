# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Copyright 2013, Big Switch Networks, Inc.
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
import re

from django.utils.translation import ugettext as _

from horizon import exceptions
from horizon import forms
from horizon.utils import fields
from horizon import workflows

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class AddPoolAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    subnet_id = forms.ChoiceField(label=_("Subnet"))
    protocol = forms.ChoiceField(label=_("Protocol"))
    lb_method = forms.ChoiceField(label=_("Load Balancing Method"))
    admin_state_up = forms.BooleanField(label=_("Admin State"),
                                     initial=True, required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddPoolAction, self).__init__(request, *args, **kwargs)

        tenant_id = request.user.tenant_id

        subnet_id_choices = [('', _("Select a Subnet"))]
        try:
            networks = api.quantum.network_list_for_tenant(request, tenant_id)
        except:
            exceptions.handle(request,
                              _('Unable to retrieve networks list.'))
            networks = []
        for n in networks:
            for s in n['subnets']:
                subnet_id_choices.append((s.id, s.cidr))
        self.fields['subnet_id'].choices = subnet_id_choices

        protocol_choices = [('', _("Select a Protocol"))]
        protocol_choices.append(('HTTP', 'HTTP'))
        protocol_choices.append(('HTTPS', 'HTTPS'))
        self.fields['protocol'].choices = protocol_choices

        lb_method_choices = [('', _("Select a Protocol"))]
        lb_method_choices.append(('ROUND_ROBIN', 'ROUND_ROBIN'))
        lb_method_choices.append(('LEAST_CONNECTIONS', 'LEAST_CONNECTIONS'))
        lb_method_choices.append(('SOURCE_IP', 'SOURCE_IP'))
        self.fields['lb_method'].choices = lb_method_choices

    class Meta:
        name = _("PoolDetails")
        permissions = ('openstack.services.network',)
        help_text = _("Create Pool for current tenant.\n\n"
                      "Assign a name and description for the pool. "
                      "Choose one subnet where all members of this "
                      "pool must be on. "
                      "Select the protocol and load balancing method "
                      "for this pool. "
                      "Admin State is UP (checked) by defaul.t")


class AddPoolStep(workflows.Step):
    action_class = AddPoolAction
    contributes = ("name", "description", "subnet_id",
                   "protocol", "lb_method", "admin_state_up")

    def contribute(self, data, context):
        context = super(AddPoolStep, self).contribute(data, context)
        if data:
            return context


class AddPool(workflows.Workflow):
    slug = "addpool"
    name = _("Add Pool")
    finalize_button_name = _("Add")
    success_message = _('Added Pool "%s".')
    failure_message = _('Unable to add Pool "%s".')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (AddPoolStep,)

    def format_status_message(self, message):
        name = self.context.get('name')
        return message % name

    def handle(self, request, context):
        try:
            pool = api.lbaas.pool_create(request, **context)
            return True
        except:
            msg = self.format_status_message(self.failure_message)
            exceptions.handle(request, msg)
            return False


class AddVipAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    floatip_address = forms.ChoiceField(
        label=_("Vip Address from Floating IPs"),
        widget=forms.Select(attrs={'disabled': 'disabled'}),
        required=False)
    other_address = fields.IPField(required=False,
                                   initial="",
                                   version=fields.IPv4,
                                   mask=False)
    protocol_port = forms.CharField(max_length=80, label=_("Protocol Port"))
    protocol = forms.ChoiceField(label=_("Protocol"))
    session_persistence = forms.ChoiceField(
        required=False, initial={}, label=_("Session Persistence"))
    cookie_name = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Cookie Name"),
        help_text=_("Required for APP_COOKIE persistence;"
                    " Ignored otherwise."))
    connection_limit = forms.CharField(
        max_length=80, label=_("Connection Limit"))
    admin_state_up = forms.BooleanField(
        label=_("Admin State"), initial=True, required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddVipAction, self).__init__(request, *args, **kwargs)

        self.fields['other_address'].label = _("Specify a free IP address"
                                               " from %s" %
                                               args[0]['subnet'])

        protocol_choices = [('', _("Select a Protocol"))]
        protocol_choices.append(('HTTP', 'HTTP'))
        protocol_choices.append(('HTTPS', 'HTTPS'))
        self.fields['protocol'].choices = protocol_choices

        session_persistence_choices = [('', _("Set Session Persistence"))]
        for mode in ('SOURCE_IP', 'HTTP_COOKIE', 'APP_COOKIE'):
            session_persistence_choices.append((mode, mode))
        self.fields[
            'session_persistence'].choices = session_persistence_choices

        floatip_address_choices = [('', _("Currently Not Supported"))]
        self.fields['floatip_address'].choices = floatip_address_choices

    class Meta:
        name = _("AddVip")
        permissions = ('openstack.services.network',)
        help_text = _("Create a vip (virtual IP) for this pool. "
                      "Assign a name and description for the vip. "
                      "Specify an IP address and port for the vip. "
                      "Choose the protocol and session persistence "
                      "method for the vip."
                      "Specify the max connections allowed. "
                      "Admin State is UP (checked) by default.")


class AddVipStep(workflows.Step):
    action_class = AddVipAction
    depends_on = ("pool_id", "subnet")
    contributes = ("name", "description", "floatip_address",
                   "other_address", "protocol_port", "protocol",
                   "session_persistence", "cookie_name",
                   "connection_limit", "admin_state_up")

    def contribute(self, data, context):
        context = super(AddVipStep, self).contribute(data, context)
        return context


class AddVip(workflows.Workflow):
    slug = "addvip"
    name = _("Add Vip")
    finalize_button_name = _("Add")
    success_message = _('Added Vip "%s".')
    failure_message = _('Unable to add Vip "%s".')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (AddVipStep,)

    def format_status_message(self, message):
        name = self.context.get('name')
        return message % name

    def handle(self, request, context):
        if context['other_address'] == '':
            context['address'] = context['floatip_address']
        else:
            if not context['floatip_address'] == '':
                self.failure_message = _('Only one address can be specified.'
                                         'Unable to add Vip %s.')
                return False
            else:
                context['address'] = context['other_address']
        try:
            pool = api.lbaas.pool_get(request, context['pool_id'])
            context['subnet_id'] = pool['subnet_id']
        except:
            context['subnet_id'] = None
            exceptions.handle(request,
                              _('Unable to retrieve pool.'))
            return False

        if context['session_persistence']:
            stype = context['session_persistence']
            if stype == 'APP_COOKIE':
                if context['cookie_name'] == "":
                    self.failure_message = _('Cookie name must be specified '
                                             'with APP_COOKIE persistence.')
                    return False
                else:
                    cookie = context['cookie_name']
                    context['session_persistence'] = {'type': stype,
                                                      'cookie_name': cookie}
            else:
                context['session_persistence'] = {'type': stype}
        else:
            context['session_persistence'] = {}

        try:
            api.lbaas.vip_create(request, **context)
            return True
        except:
            msg = self.format_status_message(self.failure_message)
            exceptions.handle(request, msg)
            return False


class AddMemberAction(workflows.Action):
    pool_id = forms.ChoiceField(label=_("Pool"))
    members = forms.MultipleChoiceField(
        label=_("Member(s)"),
        required=True,
        initial=["default"],
        widget=forms.CheckboxSelectMultiple(),
        help_text=_("Select members for this pool "))
    weight = forms.CharField(max_length=80, label=_("Weight"))
    protocol_port = forms.CharField(max_length=80, label=_("Protocol Port"))
    admin_state_up = forms.BooleanField(label=_("Admin State"),
                                        initial=True, required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddMemberAction, self).__init__(request, *args, **kwargs)

        pool_id_choices = [('', _("Select a Pool"))]
        try:
            pools = api.lbaas.pools_get(request)
        except:
            pools = []
            exceptions.handle(request,
                              _('Unable to retrieve pools list.'))
        pools = sorted(pools,
                       key=lambda pool: pool.name)
        for p in pools:
            pool_id_choices.append((p.id, p.name))
        self.fields['pool_id'].choices = pool_id_choices

        members_choices = []
        try:
            servers = api.nova.server_list(request)
        except:
            servers = []
            exceptions.handle(request,
                              _('Unable to retrieve instances list.'))

        if len(servers) == 0:
            self.fields['members'].label = _("No servers available. "
                                             "Click Add to cancel.")
            self.fields['members'].required = False
            self.fields['members'].help_text = _("Select members "
                                                 "for this pool ")
            self.fields['pool_id'].required = False
            self.fields['weight'].required = False
            self.fields['protocol_port'].required = False
            return

        for m in servers:
            members_choices.append((m.id, m.name))
        self.fields['members'].choices = sorted(
            members_choices,
            key=lambda member: member[1])

    class Meta:
        name = _("MemberDetails")
        permissions = ('openstack.services.network',)
        help_text = _("Add member to selected pool.\n\n"
                      "Choose one or more listed instances to be "
                      "added to the pool as member(s). "
                      "Assign a numeric weight for this member "
                      "Specify the port number the member(s) "
                      "operate on; e.g., 80.")


class AddMemberStep(workflows.Step):
    action_class = AddMemberAction
    contributes = ("pool_id", "members", "protocol_port", "weight",
                   "admin_state_up")

    def contribute(self, data, context):
        context = super(AddMemberStep, self).contribute(data, context)
        return context


class AddMember(workflows.Workflow):
    slug = "addmember"
    name = _("Add Member")
    finalize_button_name = _("Add")
    success_message = _('Added Member "%s".')
    failure_message = _('Unable to add Member %s.')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (AddMemberStep,)

    def handle(self, request, context):
        if context['members'] == []:
            self.failure_message = _('No instances available.%s')
            context['member_id'] = ''
            return False

        for m in context['members']:
            params = {'device_id': m}
            try:
                plist = api.quantum.port_list(request, **params)
            except:
                plist = []
                exceptions.handle(request,
                                  _('Unable to retrieve ports list.'))
                return False
            if plist:
                context['address'] = plist[0].fixed_ips[0]['ip_address']
            try:
                context['member_id'] = api.lbaas.member_create(
                    request, **context).id
            except:
                exceptions.handle(request, _("Unable to add member."))
                return False
        return True


class AddMonitorAction(workflows.Action):
    pool_id = forms.ChoiceField(label=_("Pool"))
    type = forms.ChoiceField(label=_("Type"))
    delay = forms.CharField(max_length=80, label=_("Delay"))
    timeout = forms.CharField(max_length=80, label=_("Timeout"))
    max_retries = forms.CharField(max_length=80,
                                  label=_("Max Retries (1~10)"))
    http_method = forms.ChoiceField(
        initial="GET", required=False, label=_("HTTP Method"))
    url_path = forms.CharField(
        initial="/", required=False, max_length=80, label=_("URL"))
    expected_codes = forms.CharField(
        initial="200", required=False, max_length=80,
        label=_("Expected HTTP Status Codes"))
    admin_state_up = forms.BooleanField(label=_("Admin State"),
                                        initial=True, required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddMonitorAction, self).__init__(request, *args, **kwargs)

        pool_id_choices = [('', _("Select a Pool"))]
        try:
            pools = api.lbaas.pools_get(request)
            for p in pools:
                pool_id_choices.append((p.id, p.name))
        except:
            exceptions.handle(request,
                              _('Unable to retrieve pools list.'))
        self.fields['pool_id'].choices = pool_id_choices

        type_choices = [('', _("Select Type"))]
        type_choices.append(('PING', 'PING'))
        type_choices.append(('TCP', 'TCP'))
        type_choices.append(('HTTP', 'HTTP'))
        type_choices.append(('HTTPS', 'HTTPS'))
        self.fields['type'].choices = type_choices

        http_method_choices = [('', _("Select HTTP Method"))]
        http_method_choices.append(('GET', 'GET'))
        self.fields['http_method'].choices = http_method_choices

    class Meta:
        name = _("MonitorDetails")
        permissions = ('openstack.services.network',)
        help_text = _("Create a monitor for a pool.\n\n"
                      "Select target pool and type of monitoring. "
                      "Specify delay, timeout, and retry limits "
                      "required by the monitor. "
                      "Specify method, URL path, and expected "
                      "HTTP codes upon success.")


class AddMonitorStep(workflows.Step):
    action_class = AddMonitorAction
    contributes = ("pool_id", "type", "delay", "timeout", "max_retries",
                   "http_method", "url_path", "expected_codes",
                   "admin_state_up")

    def contribute(self, data, context):
        context = super(AddMonitorStep, self).contribute(data, context)
        if data:
            return context


class AddMonitor(workflows.Workflow):
    slug = "addmonitor"
    name = _("Add Monitor")
    finalize_button_name = _("Add")
    success_message = _('Added Monitor "%s".')
    failure_message = _('Unable to add Monitor "%s".')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (AddMonitorStep,)

    def handle(self, request, context):
        try:
            context['monitor_id'] = api.lbaas.pool_health_monitor_create(
                request, **context).get('id')
            return True
        except:
            exceptions.handle(request, _("Unable to add monitor."))
        return False
