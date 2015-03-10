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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import validators
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.loadbalancers import utils


AVAILABLE_PROTOCOLS = ('HTTP', 'HTTPS', 'TCP')
AVAILABLE_METHODS = ('ROUND_ROBIN', 'LEAST_CONNECTIONS', 'SOURCE_IP')


LOG = logging.getLogger(__name__)


class AddPoolAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    # provider is optional because some LBaaS implemetation does
    # not support service-type extension.
    provider = forms.ChoiceField(label=_("Provider"), required=False)
    subnet_id = forms.ChoiceField(label=_("Subnet"))
    protocol = forms.ChoiceField(label=_("Protocol"))
    lb_method = forms.ChoiceField(label=_("Load Balancing Method"))
    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    def __init__(self, request, *args, **kwargs):
        super(AddPoolAction, self).__init__(request, *args, **kwargs)

        tenant_id = request.user.tenant_id

        subnet_id_choices = [('', _("Select a Subnet"))]
        try:
            networks = api.neutron.network_list_for_tenant(request, tenant_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve networks list.'))
            networks = []
        for n in networks:
            for s in n['subnets']:
                subnet_id_choices.append((s.id, s.cidr))
        self.fields['subnet_id'].choices = subnet_id_choices

        protocol_choices = [('', _("Select a Protocol"))]
        [protocol_choices.append((p, p)) for p in AVAILABLE_PROTOCOLS]
        self.fields['protocol'].choices = protocol_choices

        lb_method_choices = [('', _("Select a Method"))]
        [lb_method_choices.append((m, m)) for m in AVAILABLE_METHODS]
        self.fields['lb_method'].choices = lb_method_choices

        # provider choice
        try:
            if api.neutron.is_extension_supported(request, 'service-type'):
                provider_list = api.neutron.provider_list(request)
                providers = [p for p in provider_list
                             if p['service_type'] == 'LOADBALANCER']
            else:
                providers = None
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve providers list.'))
            providers = []

        if providers:
            default_providers = [p for p in providers if p.get('default')]
            if default_providers:
                default_provider = default_providers[0]['name']
            else:
                default_provider = None
            provider_choices = [(p['name'], p['name']) for p in providers
                                if p['name'] != default_provider]
            if default_provider:
                provider_choices.insert(
                    0, (default_provider,
                        _("%s (default)") % default_provider))
        else:
            if providers is None:
                msg = _("Provider for Load Balancer is not supported")
            else:
                msg = _("No provider is available")
            provider_choices = [('', msg)]
            self.fields['provider'].widget.attrs['readonly'] = True
        self.fields['provider'].choices = provider_choices

    class Meta(object):
        name = _("Add New Pool")
        permissions = ('openstack.services.network',)
        help_text = _("Create Pool for current project.\n\n"
                      "Assign a name and description for the pool. "
                      "Choose one subnet where all members of this "
                      "pool must be on. "
                      "Select the protocol and load balancing method "
                      "for this pool. "
                      "Admin State is UP (checked) by default.")


class AddPoolStep(workflows.Step):
    action_class = AddPoolAction
    contributes = ("name", "description", "subnet_id", "provider",
                   "protocol", "lb_method", "admin_state_up")

    def contribute(self, data, context):
        context = super(AddPoolStep, self).contribute(data, context)
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        if data:
            return context


class AddPool(workflows.Workflow):
    slug = "addpool"
    name = _("Add Pool")
    finalize_button_name = _("Add")
    success_message = _('Added pool "%s".')
    failure_message = _('Unable to add pool "%s".')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (AddPoolStep,)

    def format_status_message(self, message):
        name = self.context.get('name')
        return message % name

    def handle(self, request, context):
        try:
            api.lbaas.pool_create(request, **context)
            return True
        except Exception:
            return False


class AddVipAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    subnet_id = forms.ChoiceField(label=_("VIP Subnet"),
                                  initial="",
                                  required=False)
    address = forms.IPField(label=_("Specify a free IP address "
                                    "from the selected subnet"),
                            version=forms.IPv4,
                            mask=False,
                            required=False)
    protocol_port = forms.IntegerField(
        label=_("Protocol Port"), min_value=1,
        help_text=_("Enter an integer value "
                    "between 1 and 65535."),
        validators=[validators.validate_port_range])
    protocol = forms.ChoiceField(label=_("Protocol"))
    session_persistence = forms.ChoiceField(
        required=False, initial={}, label=_("Session Persistence"),
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'persistence'
        }))
    cookie_name = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Cookie Name"),
        help_text=_("Required for APP_COOKIE persistence;"
                    " Ignored otherwise."),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'persistence',
            'data-persistence-app_cookie': 'APP_COOKIE',
        }))
    connection_limit = forms.IntegerField(
        required=False, min_value=-1, label=_("Connection Limit"),
        help_text=_("Maximum number of connections allowed "
                    "for the VIP or '-1' if the limit is not set"))
    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    def __init__(self, request, *args, **kwargs):
        super(AddVipAction, self).__init__(request, *args, **kwargs)
        tenant_id = request.user.tenant_id
        subnet_id_choices = [('', _("Select a Subnet"))]
        try:
            networks = api.neutron.network_list_for_tenant(request, tenant_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve networks list.'))
            networks = []
        for n in networks:
            for s in n['subnets']:
                subnet_id_choices.append((s.id, s.cidr))
        self.fields['subnet_id'].choices = subnet_id_choices
        protocol_choices = [('', _("Select a Protocol"))]
        [protocol_choices.append((p, p)) for p in AVAILABLE_PROTOCOLS]
        self.fields['protocol'].choices = protocol_choices

        session_persistence_choices = [('', _("No Session Persistence"))]
        for mode in ('SOURCE_IP', 'HTTP_COOKIE', 'APP_COOKIE'):
            session_persistence_choices.append((mode.lower(), mode))
        self.fields[
            'session_persistence'].choices = session_persistence_choices

    def clean(self):
        cleaned_data = super(AddVipAction, self).clean()
        persistence = cleaned_data.get('session_persistence')
        if persistence:
            cleaned_data['session_persistence'] = persistence.upper()
        if (cleaned_data.get('session_persistence') == 'APP_COOKIE' and
                not cleaned_data.get('cookie_name')):
            msg = _('Cookie name is required for APP_COOKIE persistence.')
            self._errors['cookie_name'] = self.error_class([msg])
        return cleaned_data

    class Meta(object):
        name = _("Specify VIP")
        permissions = ('openstack.services.network',)
        help_text = _("Create a VIP for this pool. "
                      "Assign a name, description, IP address, port, "
                      "and maximum connections allowed for the VIP. "
                      "Choose the protocol and session persistence "
                      "method for the VIP. "
                      "Admin State is UP (checked) by default.")


class AddVipStep(workflows.Step):
    action_class = AddVipAction
    depends_on = ("pool_id", "subnet")
    contributes = ("name", "description", "subnet_id",
                   "address", "protocol_port", "protocol",
                   "session_persistence", "cookie_name",
                   "connection_limit", "admin_state_up")

    def contribute(self, data, context):
        context = super(AddVipStep, self).contribute(data, context)
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        return context


class AddVip(workflows.Workflow):
    slug = "addvip"
    name = _("Add VIP")
    finalize_button_name = _("Add")
    success_message = _('Added VIP "%s".')
    failure_message = _('Unable to add VIP "%s".')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (AddVipStep,)

    def format_status_message(self, message):
        name = self.context.get('name')
        return message % name

    def handle(self, request, context):
        if context['subnet_id'] == '':
            try:
                pool = api.lbaas.pool_get(request, context['pool_id'])
                context['subnet_id'] = pool['subnet_id']
            except Exception:
                context['subnet_id'] = None
                self.failure_message = _(
                    'Unable to retrieve the specified pool. '
                    'Unable to add VIP "%s".')
                return False

        if context['session_persistence']:
            stype = context['session_persistence']
            if stype == 'APP_COOKIE':
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
        except Exception:
            return False


class AddMemberAction(workflows.Action):
    pool_id = forms.ChoiceField(label=_("Pool"))
    member_type = forms.ChoiceField(
        label=_("Member Source"),
        choices=[('server_list', _("Select from active instances")),
                 ('member_address', _("Specify member IP address"))],
        required=False,
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'membertype'
        }))
    members = forms.MultipleChoiceField(
        label=_("Member(s)"),
        required=False,
        initial=["default"],
        widget=forms.SelectMultiple(attrs={
            'class': 'switched',
            'data-switch-on': 'membertype',
            'data-membertype-server_list': _("Member(s)"),
        }),
        help_text=_("Select members for this pool "))
    address = forms.IPField(required=False, label=_("Member address"),
                            help_text=_("Specify member IP address"),
                            widget=forms.TextInput(attrs={
                                'class': 'switched',
                                'data-switch-on': 'membertype',
                                'data-membertype-member_address':
                                _("Member address"),
                            }),
                            initial="", version=forms.IPv4 | forms.IPv6,
                            mask=False)
    weight = forms.IntegerField(
        max_value=256, min_value=1, label=_("Weight"), required=False,
        help_text=_("Relative part of requests this pool member serves "
                    "compared to others. \nThe same weight will be applied to "
                    "all the selected members and can be modified later. "
                    "Weight must be in the range 1 to 256.")
    )
    protocol_port = forms.IntegerField(
        label=_("Protocol Port"), min_value=1,
        help_text=_("Enter an integer value between 1 and 65535. "
                    "The same port will be used for all the selected "
                    "members and can be modified later."),
        validators=[validators.validate_port_range]
    )
    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    def __init__(self, request, *args, **kwargs):
        super(AddMemberAction, self).__init__(request, *args, **kwargs)

        pool_id_choices = [('', _("Select a Pool"))]
        try:
            tenant_id = self.request.user.tenant_id
            pools = api.lbaas.pool_list(request, tenant_id=tenant_id)
        except Exception:
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
            servers, has_more = api.nova.server_list(request)
        except Exception:
            servers = []
            exceptions.handle(request,
                              _('Unable to retrieve instances list.'))

        if len(servers) == 0:
            self.fields['members'].label = _(
                "No servers available. To add a member, you "
                "need at least one running instance.")
            self.fields['pool_id'].required = False
            self.fields['protocol_port'].required = False
            return

        for m in servers:
            members_choices.append((m.id, m.name))
        self.fields['members'].choices = sorted(
            members_choices,
            key=lambda member: member[1])

    def clean(self):
        cleaned_data = super(AddMemberAction, self).clean()
        if (cleaned_data.get('member_type') == 'server_list' and
                not cleaned_data.get('members')):
            msg = _('At least one member must be specified')
            self._errors['members'] = self.error_class([msg])
        elif (cleaned_data.get('member_type') == 'member_address' and
                not cleaned_data.get('address')):
            msg = _('Member IP address must be specified')
            self._errors['address'] = self.error_class([msg])
        return cleaned_data

    class Meta(object):
        name = _("Add New Member")
        permissions = ('openstack.services.network',)
        help_text = _("Add member(s) to the selected pool.\n\n"
                      "Choose one or more listed instances to be "
                      "added to the pool as member(s). "
                      "Assign a numeric weight and port number for the "
                      "selected member(s) to operate(s) on; e.g., 80. \n\n"
                      "Only one port can be associated with "
                      "each instance.")


class AddMemberStep(workflows.Step):
    action_class = AddMemberAction
    contributes = ("pool_id", "member_type", "members", "address",
                   "protocol_port", "weight", "admin_state_up")

    def contribute(self, data, context):
        context = super(AddMemberStep, self).contribute(data, context)
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        return context


class AddMember(workflows.Workflow):
    slug = "addmember"
    name = _("Add Member")
    finalize_button_name = _("Add")
    success_message = _('Added member(s).')
    failure_message = _('Unable to add member(s)')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (AddMemberStep,)

    def handle(self, request, context):
        if context['member_type'] == 'server_list':
            try:
                pool = api.lbaas.pool_get(request, context['pool_id'])
                subnet_id = pool['subnet_id']
            except Exception:
                self.failure_message = _('Unable to retrieve '
                                         'the specified pool.')
                return False
            for m in context['members']:
                params = {'device_id': m}
                try:
                    plist = api.neutron.port_list(request, **params)
                except Exception:
                    return False

                # Sort port list for each member. This is needed to avoid
                # attachment of random ports in case of creation of several
                # members attached to several networks.
                plist = sorted(plist, key=lambda port: port.network_id)
                psubnet = [p for p in plist for ips in p.fixed_ips
                           if ips['subnet_id'] == subnet_id]

                # If possible, select a port on pool subnet.
                if psubnet:
                    selected_port = psubnet[0]
                elif plist:
                    selected_port = plist[0]
                else:
                    selected_port = None

                if selected_port:
                    context['address'] = \
                        selected_port.fixed_ips[0]['ip_address']
                    try:
                        api.lbaas.member_create(request, **context).id
                    except Exception as e:
                        msg = self.failure_message
                        LOG.info('%s: %s' % (msg, e))
                        return False
            return True
        else:
            try:
                context['member_id'] = api.lbaas.member_create(
                    request, **context).id
                return True
            except Exception as e:
                msg = self.failure_message
                LOG.info('%s: %s' % (msg, e))
                return False


class AddMonitorAction(workflows.Action):
    type = forms.ChoiceField(
        label=_("Type"),
        choices=[('ping', _('PING')),
                 ('tcp', _('TCP')),
                 ('http', _('HTTP')),
                 ('https', _('HTTPS'))],
        widget=forms.Select(attrs={
            'class': 'switchable',
            'data-slug': 'type'
        }))
    delay = forms.IntegerField(
        min_value=1,
        label=_("Delay"),
        help_text=_("The minimum time in seconds between regular checks "
                    "of a member"))
    timeout = forms.IntegerField(
        min_value=1,
        label=_("Timeout"),
        help_text=_("The maximum time in seconds for a monitor to wait "
                    "for a reply"))
    max_retries = forms.IntegerField(
        max_value=10, min_value=1,
        label=_("Max Retries (1~10)"),
        help_text=_("Number of permissible failures before changing "
                    "the status of member to inactive"))
    http_method = forms.ChoiceField(
        initial="GET",
        required=False,
        choices=[('GET', _('GET'))],
        label=_("HTTP Method"),
        help_text=_("HTTP method used to check health status of a member"),
        widget=forms.Select(attrs={
            'class': 'switched',
            'data-switch-on': 'type',
            'data-type-http': _('HTTP Method'),
            'data-type-https': _('HTTP Method')
        }))
    url_path = forms.CharField(
        initial="/",
        required=False,
        max_length=80,
        label=_("URL"),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'type',
            'data-type-http': _('URL'),
            'data-type-https': _('URL')
        }))
    expected_codes = forms.RegexField(
        initial="200",
        required=False,
        max_length=80,
        regex=r'^(\d{3}(\s*,\s*\d{3})*)$|^(\d{3}-\d{3})$',
        label=_("Expected HTTP Status Codes"),
        help_text=_("Expected code may be a single value (e.g. 200), "
                    "a list of values (e.g. 200, 202), "
                    "or range of values (e.g. 200-204)"),
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'type',
            'data-type-http': _('Expected HTTP Status Codes'),
            'data-type-https': _('Expected HTTP Status Codes')
        }))
    admin_state_up = forms.ChoiceField(choices=[(True, _('UP')),
                                                (False, _('DOWN'))],
                                       label=_("Admin State"))

    def __init__(self, request, *args, **kwargs):
        super(AddMonitorAction, self).__init__(request, *args, **kwargs)

    def clean(self):
        cleaned_data = super(AddMonitorAction, self).clean()
        type_opt = cleaned_data.get('type')
        delay = cleaned_data.get('delay')
        timeout = cleaned_data.get('timeout')

        if not delay >= timeout:
            msg = _('Delay must be greater than or equal to Timeout')
            self._errors['delay'] = self.error_class([msg])

        if type_opt in ['http', 'https']:
            http_method_opt = cleaned_data.get('http_method')
            url_path = cleaned_data.get('url_path')
            expected_codes = cleaned_data.get('expected_codes')

            if not http_method_opt:
                msg = _('Please choose a HTTP method')
                self._errors['http_method'] = self.error_class([msg])
            if not url_path:
                msg = _('Please specify an URL')
                self._errors['url_path'] = self.error_class([msg])
            if not expected_codes:
                msg = _('Please enter a single value (e.g. 200), '
                        'a list of values (e.g. 200, 202), '
                        'or range of values (e.g. 200-204)')
                self._errors['expected_codes'] = self.error_class([msg])
        return cleaned_data

    class Meta(object):
        name = _("Add New Monitor")
        permissions = ('openstack.services.network',)
        help_text = _("Create a monitor template.\n\n"
                      "Select type of monitoring. "
                      "Specify delay, timeout, and retry limits "
                      "required by the monitor. "
                      "Specify method, URL path, and expected "
                      "HTTP codes upon success.")


class AddMonitorStep(workflows.Step):
    action_class = AddMonitorAction
    contributes = ("type", "delay", "timeout", "max_retries",
                   "http_method", "url_path", "expected_codes",
                   "admin_state_up")

    def contribute(self, data, context):
        context = super(AddMonitorStep, self).contribute(data, context)
        context['admin_state_up'] = (context['admin_state_up'] == 'True')
        if data:
            return context


class AddMonitor(workflows.Workflow):
    slug = "addmonitor"
    name = _("Add Monitor")
    finalize_button_name = _("Add")
    success_message = _('Added monitor')
    failure_message = _('Unable to add monitor')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (AddMonitorStep,)

    def handle(self, request, context):
        try:
            context['monitor_id'] = api.lbaas.pool_health_monitor_create(
                request, **context).get('id')
            return True
        except Exception:
            exceptions.handle(request, _("Unable to add monitor."))
        return False


class AddPMAssociationAction(workflows.Action):
    monitor_id = forms.ChoiceField(label=_("Monitor"))

    def __init__(self, request, *args, **kwargs):
        super(AddPMAssociationAction, self).__init__(request, *args, **kwargs)

    def populate_monitor_id_choices(self, request, context):
        self.fields['monitor_id'].label = _("Select a monitor template "
                                            "for %s") % context['pool_name']

        monitor_id_choices = [('', _("Select a Monitor"))]
        try:
            tenant_id = self.request.user.tenant_id
            monitors = api.lbaas.pool_health_monitor_list(request,
                                                          tenant_id=tenant_id)
            pool_monitors_ids = [pm.id for pm in context['pool_monitors']]
            for m in monitors:
                if m.id not in pool_monitors_ids:
                    display_name = utils.get_monitor_display_name(m)
                    monitor_id_choices.append((m.id, display_name))
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve monitors list.'))
        self.fields['monitor_id'].choices = monitor_id_choices

        return monitor_id_choices

    class Meta(object):
        name = _("Association Details")
        permissions = ('openstack.services.network',)
        help_text = _("Associate a health monitor with target pool.")


class AddPMAssociationStep(workflows.Step):
    action_class = AddPMAssociationAction
    depends_on = ("pool_id", "pool_name", "pool_monitors")
    contributes = ("monitor_id",)

    def contribute(self, data, context):
        context = super(AddPMAssociationStep, self).contribute(data, context)
        if data:
            return context


class AddPMAssociation(workflows.Workflow):
    slug = "addassociation"
    name = _("Associate Monitor")
    finalize_button_name = _("Associate")
    success_message = _('Associated monitor.')
    failure_message = _('Unable to associate monitor.')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (AddPMAssociationStep,)

    def handle(self, request, context):
        try:
            context['monitor_id'] = api.lbaas.pool_monitor_association_create(
                request, **context)
            return True
        except Exception:
            exceptions.handle(request, _("Unable to associate monitor."))
            return False


class DeletePMAssociationAction(workflows.Action):
    monitor_id = forms.ChoiceField(label=_("Monitor"))

    def __init__(self, request, *args, **kwargs):
        super(DeletePMAssociationAction, self).__init__(
            request, *args, **kwargs)

    def populate_monitor_id_choices(self, request, context):
        self.fields['monitor_id'].label = (_("Select a health monitor of %s") %
                                           context['pool_name'])

        monitor_id_choices = [('', _("Select a Monitor"))]
        try:
            monitors = api.lbaas.pool_health_monitor_list(request)
            pool_monitors_ids = [pm.id for pm in context['pool_monitors']]
            for m in monitors:
                if m.id in pool_monitors_ids:
                    display_name = utils.get_monitor_display_name(m)
                    monitor_id_choices.append((m.id, display_name))
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve monitors list.'))
        self.fields['monitor_id'].choices = monitor_id_choices

        return monitor_id_choices

    class Meta(object):
        name = _("Association Details")
        permissions = ('openstack.services.network',)
        help_text = _("Disassociate a health monitor from target pool. ")


class DeletePMAssociationStep(workflows.Step):
    action_class = DeletePMAssociationAction
    depends_on = ("pool_id", "pool_name", "pool_monitors")
    contributes = ("monitor_id",)

    def contribute(self, data, context):
        context = super(DeletePMAssociationStep, self).contribute(
            data, context)
        if data:
            return context


class DeletePMAssociation(workflows.Workflow):
    slug = "deleteassociation"
    name = _("Disassociate Monitor")
    finalize_button_name = _("Disassociate")
    success_message = _('Disassociated monitor.')
    failure_message = _('Unable to disassociate monitor.')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (DeletePMAssociationStep,)

    def handle(self, request, context):
        try:
            context['monitor_id'] = api.lbaas.pool_monitor_association_delete(
                request, **context)
            return True
        except Exception:
            exceptions.handle(request, _("Unable to disassociate monitor."))
        return False
